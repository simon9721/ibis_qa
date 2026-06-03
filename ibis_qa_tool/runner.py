"""
runner.py  —  CheckRunner: discovers and runs all check modules
===============================================================
Auto-discovers all CheckModule subclasses from the checks/ package.
Runs them in check_id order and collects results.
"""

from __future__ import annotations
import importlib
import json
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

from checks.base import CheckModule, CheckResult

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile

_SPEC_PATH = Path(__file__).resolve().parent.parent / "data" / "ibis_quality_spec_3_0.json"


class CheckRunner:
    """
    Discovers all CheckModule subclasses registered in the checks/ package
    and runs them against an IBISFile.

    To add a new check: create a new file under checks/ that defines a
    class inheriting from CheckModule. It will be picked up automatically.
    """

    def __init__(self, max_level: int | None = None):
        self.max_level = max_level
        self._check_levels = self._load_check_levels()
        self._modules: list[CheckModule] = []
        self._discover()

    def _discover(self):
        """Import all modules in the checks/ package and collect CheckModule subclasses."""
        checks_path = Path(__file__).parent / "checks"
        seen_classes = set()

        for _, mod_name, _ in pkgutil.iter_modules([str(checks_path)]):
            if mod_name == "base" or mod_name.startswith("__"):
                continue
            try:
                module = importlib.import_module(f"checks.{mod_name}")
            except ImportError as e:
                print(f"Warning: could not import checks.{mod_name}: {e}")
                continue

            for attr_name in dir(module):
                cls = getattr(module, attr_name)
                if (isinstance(cls, type)
                        and issubclass(cls, CheckModule)
                        and cls is not CheckModule
                        and cls not in seen_classes
                        and cls.check_ids):
                    enabled_ids = [
                        check_id for check_id in cls.check_ids
                        if self._check_enabled(check_id)
                    ]
                    if not enabled_ids:
                        continue
                    module_instance = cls()
                    module_instance.enabled_check_ids = set(enabled_ids)
                    self._modules.append(module_instance)
                    seen_classes.add(cls)

        # Sort by first check_id for deterministic ordering
        self._modules.sort(key=lambda m: self._sort_key(m.check_ids[0]))

    @staticmethod
    def _sort_key(check_id: str) -> tuple:
        """Sort e.g. "5.3.14" numerically as (5, 3, 14)."""
        try:
            return tuple(int(x) for x in check_id.split('.'))
        except ValueError:
            return (999,)

    @staticmethod
    def _load_check_levels() -> dict[str, int | None]:
        if not _SPEC_PATH.exists():
            return {}
        try:
            data = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {
            item["id"]: item.get("numeric_level")
            for item in data.get("checks", [])
            if item.get("id")
        }

    def _check_enabled(self, check_id: str) -> bool:
        if self.max_level is None:
            return True
        numeric_level = self._check_levels.get(check_id)
        return numeric_level is None or numeric_level <= self.max_level

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for module in self._modules:
            try:
                results.extend(
                    result for result in module.run(ibis_file)
                    if self._check_enabled(result.check_id)
                )
            except Exception as e:
                from checks.base import Status
                results.append(CheckResult(
                    check_id=module.check_ids[0],
                    status=Status.ERROR,
                    subject=ibis_file.file_name,
                    message=f"Check module raised exception: {type(e).__name__}: {e}",
                    details=[],
                ))
        return results

    @property
    def registered_checks(self) -> list[str]:
        """All check IDs registered across all modules."""
        ids = []
        for m in self._modules:
            ids.extend(m.check_ids)
        return ids

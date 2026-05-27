"""
runner.py  —  CheckRunner: discovers and runs all check modules
===============================================================
Auto-discovers all CheckModule subclasses from the checks/ package.
Runs them in check_id order and collects results.
"""

from __future__ import annotations
import importlib
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

from checks.base import CheckModule, CheckResult

if TYPE_CHECKING:
    from parser.ibis_parser import IBISFile


class CheckRunner:
    """
    Discovers all CheckModule subclasses registered in the checks/ package
    and runs them against an IBISFile.

    To add a new check: create a new file under checks/ that defines a
    class inheriting from CheckModule. It will be picked up automatically.
    """

    def __init__(self):
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
                    self._modules.append(cls())
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

    def run(self, ibis_file: "IBISFile") -> list[CheckResult]:
        results = []
        for module in self._modules:
            try:
                results.extend(module.run(ibis_file))
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

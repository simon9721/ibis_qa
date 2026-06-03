"""Tkinter GUI for running IBIS QA and reviewing semi-auto evidence."""

from __future__ import annotations

import json
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from parser.ibis_parser import IBISParser
from review import (
    DECISIONS,
    apply_review_decisions,
    decision_for_item,
    load_review_decisions,
    make_review_payload,
)
from runner import CheckRunner
from reporter import Reporter, render_html_report, render_markdown_report
from spreadsheet import write_spreadsheet_report


MAX_LEVEL_CHOICES = ["IQ1", "IQ2", "IQ3", "IQ4"]


def run_qa_report(path: Path, max_level: int | None = 3) -> dict:
    """Run the existing parser/checker/reporter pipeline and return a report dict."""
    ibis_file = IBISParser().parse(path)
    results = CheckRunner(max_level=max_level).run(ibis_file)
    return Reporter(results, ibis_file, verbose=True, max_level=max_level).as_dict()


class IbisQaGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IBIS QA Tool")
        self.geometry("1180x760")
        self.minsize(980, 620)

        self.work_queue: queue.Queue = queue.Queue()
        self.ibis_path: Path | None = None
        self.report: dict | None = None
        self.review_decisions: dict[str, dict[str, str]] = {}
        self.selected_review_id: str | None = None

        self.path_var = tk.StringVar()
        self.max_level_var = tk.StringVar(value="IQ3")
        self.reviewer_var = tk.StringVar()
        self.organization_var = tk.StringVar()
        self.approval_date_var = tk.StringVar(value=datetime.now().date().isoformat())
        self.status_var = tk.StringVar(value="Choose an IBIS file to begin.")
        self.summary_vars = {
            key: tk.StringVar(value=f"{key}: 0")
            for key in ("PASS", "FAIL", "WARN", "NA", "ERROR", "Review")
        }
        self.decision_var = tk.StringVar(value=DECISIONS[0])

        self._build_ui()
        self.after(100, self._poll_worker)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(4, weight=1)

        file_bar = ttk.Frame(root)
        file_bar.grid(row=0, column=0, sticky="ew")
        file_bar.columnconfigure(0, weight=1)

        self.path_entry = ttk.Entry(file_bar, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(file_bar, text="Max Level").grid(row=0, column=1, padx=(0, 4))
        self.max_level_combo = ttk.Combobox(
            file_bar,
            textvariable=self.max_level_var,
            values=MAX_LEVEL_CHOICES,
            width=6,
            state="readonly",
        )
        self.max_level_combo.grid(row=0, column=2, padx=(0, 8))
        self.browse_button = ttk.Button(file_bar, text="Browse", command=self._browse)
        self.browse_button.grid(row=0, column=3, padx=(0, 8))
        self.run_button = ttk.Button(file_bar, text="Run QA", command=self._run_qa)
        self.run_button.grid(row=0, column=4, padx=(0, 8))
        self.save_report_button = ttk.Button(
            file_bar, text="Save Report", command=self._save_report, state=tk.DISABLED
        )
        self.save_report_button.grid(row=0, column=5, padx=(0, 8))
        self.save_review_button = ttk.Button(
            file_bar, text="Save Review", command=self._save_review, state=tk.DISABLED
        )
        self.save_review_button.grid(row=0, column=6)
        self.load_review_button = ttk.Button(
            file_bar, text="Load Review", command=self._load_review, state=tk.DISABLED
        )
        self.load_review_button.grid(row=0, column=7, padx=(8, 0))

        ttk.Label(root, textvariable=self.status_var).grid(
            row=1, column=0, sticky="ew", pady=(8, 4)
        )

        summary = ttk.Frame(root)
        summary.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        for col, (key, var) in enumerate(self.summary_vars.items()):
            label = ttk.Label(summary, textvariable=var)
            label.grid(row=0, column=col, padx=(0, 18), sticky="w")

        meta = ttk.Frame(root)
        meta.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        meta.columnconfigure(1, weight=1)
        meta.columnconfigure(3, weight=1)
        ttk.Label(meta, text="Reviewer").grid(row=0, column=0, sticky="w", padx=(0, 4))
        ttk.Entry(meta, textvariable=self.reviewer_var).grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Label(meta, text="Org").grid(row=0, column=2, sticky="w", padx=(0, 4))
        ttk.Entry(meta, textvariable=self.organization_var).grid(row=0, column=3, sticky="ew", padx=(0, 10))
        ttk.Label(meta, text="Approval Date").grid(row=0, column=4, sticky="w", padx=(0, 4))
        ttk.Entry(meta, textvariable=self.approval_date_var, width=14).grid(row=0, column=5, sticky="w")

        panes = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        panes.grid(row=4, column=0, sticky="nsew")

        notebook = ttk.Notebook(panes)
        self.results_tree = self._make_tree(
            notebook,
            ("result_id", "check_id", "iq_level", "status", "scope", "subject", "message"),
            {
                "result_id": 74,
                "check_id": 72,
                "iq_level": 76,
                "status": 68,
                "scope": 96,
                "subject": 150,
                "message": 400,
            },
        )
        self.review_tree = self._make_tree(
            notebook,
            ("result_id", "kind", "check_id", "iq_level", "status", "scope", "subject", "decision", "message"),
            {
                "result_id": 74,
                "kind": 76,
                "check_id": 72,
                "iq_level": 76,
                "status": 68,
                "scope": 90,
                "subject": 130,
                "decision": 118,
                "message": 330,
            },
            selectmode="extended",
        )
        self.review_tree.bind("<<TreeviewSelect>>", self._on_review_select)
        notebook.add(self.results_tree.master, text="Results")
        notebook.add(self.review_tree.master, text="Review Queue")
        panes.add(notebook, weight=3)

        detail = ttk.Frame(panes, padding=(10, 0, 0, 0))
        detail.columnconfigure(0, weight=1)
        detail.rowconfigure(1, weight=1)
        detail.rowconfigure(5, weight=1)
        detail.rowconfigure(9, weight=1)
        panes.add(detail, weight=2)

        ttk.Label(detail, text="Selected Review Item").grid(row=0, column=0, sticky="w")
        self.detail_text = tk.Text(detail, height=14, wrap="word", state=tk.DISABLED)
        self.detail_text.grid(row=1, column=0, sticky="nsew", pady=(4, 10))

        ttk.Label(detail, text="Decision").grid(row=2, column=0, sticky="w")
        self.decision_combo = ttk.Combobox(
            detail,
            textvariable=self.decision_var,
            values=DECISIONS,
            state="readonly",
        )
        self.decision_combo.grid(row=3, column=0, sticky="ew", pady=(4, 10))

        ttk.Label(detail, text="Reviewer Comments").grid(row=4, column=0, sticky="w")
        self.comment_text = tk.Text(detail, height=10, wrap="word")
        self.comment_text.grid(row=5, column=0, sticky="nsew", pady=(4, 10))

        fields = ttk.Frame(detail)
        fields.grid(row=6, column=0, sticky="ew", pady=(0, 8))
        fields.columnconfigure(1, weight=1)
        ttk.Label(fields, text="Evidence").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.evidence_var = tk.StringVar()
        ttk.Entry(fields, textvariable=self.evidence_var).grid(row=0, column=1, sticky="ew", pady=(0, 4))
        ttk.Label(fields, text="Reference").grid(row=1, column=0, sticky="w", padx=(0, 4))
        self.datasheet_var = tk.StringVar()
        ttk.Entry(fields, textvariable=self.datasheet_var).grid(row=1, column=1, sticky="ew")

        ttk.Label(detail, text="Model-Maker Action").grid(row=7, column=0, sticky="w")
        self.action_text = tk.Text(detail, height=4, wrap="word")
        self.action_text.grid(row=8, column=0, sticky="nsew", pady=(4, 10))

        button_bar = ttk.Frame(detail)
        button_bar.grid(row=10, column=0, sticky="ew")
        button_bar.columnconfigure(0, weight=1)
        self.apply_button = ttk.Button(
            button_bar, text="Apply Decision", command=self._apply_decision, state=tk.DISABLED
        )
        self.apply_button.grid(row=0, column=1, padx=(0, 6))
        self.apply_selected_button = ttk.Button(
            button_bar, text="Apply to Selected", command=self._apply_to_selected, state=tk.DISABLED
        )
        self.apply_selected_button.grid(row=0, column=2, padx=(0, 6))
        self.accept_selected_button = ttk.Button(
            button_bar, text="Accept Selected", command=lambda: self._batch_decision("Accepted"), state=tk.DISABLED
        )
        self.accept_selected_button.grid(row=0, column=3, padx=(0, 6))
        self.na_selected_button = ttk.Button(
            button_bar, text="Mark NA Selected", command=lambda: self._batch_decision("Not Applicable"), state=tk.DISABLED
        )
        self.na_selected_button.grid(row=0, column=4)

    def _make_tree(
            self,
            parent: ttk.Notebook,
            columns: tuple[str, ...],
            widths: dict[str, int],
            selectmode: str = "browse") -> ttk.Treeview:
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode=selectmode)
        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=widths.get(col, 120), minwidth=50, anchor="w")

        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        return tree

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose IBIS file",
            filetypes=[("IBIS files", "*.ibs"), ("All files", "*.*")],
        )
        if path:
            self.ibis_path = Path(path)
            self.path_var.set(str(self.ibis_path))
            self.status_var.set("Ready to run QA.")

    def _run_qa(self) -> None:
        raw_path = self.path_var.get().strip()
        if not raw_path:
            messagebox.showwarning("No file selected", "Choose an IBIS file first.")
            return

        path = Path(raw_path)
        if not path.exists():
            messagebox.showerror("File not found", f"Could not find:\n{path}")
            return

        self.ibis_path = path
        self.report = None
        self.review_decisions.clear()
        self.selected_review_id = None
        self._clear_trees()
        self._set_busy(True)
        max_level = self._selected_max_level()
        target = f"IQ{max_level}" if max_level else "all implemented levels"
        self.status_var.set(f"Running QA for {path.name} up to {target} ...")

        thread = threading.Thread(target=self._worker_run, args=(path, max_level), daemon=True)
        thread.start()

    def _worker_run(self, path: Path, max_level: int | None) -> None:
        try:
            self.work_queue.put(("report", run_qa_report(path, max_level=max_level)))
        except Exception as exc:
            self.work_queue.put(("error", exc))

    def _poll_worker(self) -> None:
        try:
            while True:
                kind, payload = self.work_queue.get_nowait()
                if kind == "report":
                    self._load_report(payload)
                elif kind == "error":
                    self._set_busy(False)
                    self.status_var.set("QA run failed.")
                    messagebox.showerror(
                        "QA run failed",
                        f"{type(payload).__name__}: {payload}",
                    )
        except queue.Empty:
            pass
        self.after(100, self._poll_worker)

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.browse_button.configure(state=state)
        self.run_button.configure(state=state)
        self.max_level_combo.configure(state=tk.DISABLED if busy else "readonly")
        if busy or self.report is None:
            self.save_report_button.configure(state=tk.DISABLED)
            self.save_review_button.configure(state=tk.DISABLED)
            self.load_review_button.configure(state=tk.DISABLED)
        else:
            self.save_report_button.configure(state=tk.NORMAL)
            self.save_review_button.configure(state=tk.NORMAL)
            self.load_review_button.configure(state=tk.NORMAL)

    def _clear_trees(self) -> None:
        for tree in (self.results_tree, self.review_tree):
            tree.delete(*tree.get_children())
        self._set_detail("")
        self.comment_text.delete("1.0", tk.END)
        self.evidence_var.set("")
        self.datasheet_var.set("")
        self.action_text.delete("1.0", tk.END)
        self.decision_var.set(DECISIONS[0])
        self.apply_button.configure(state=tk.DISABLED)
        self.apply_selected_button.configure(state=tk.DISABLED)
        self.accept_selected_button.configure(state=tk.DISABLED)
        self.na_selected_button.configure(state=tk.DISABLED)
        for key, var in self.summary_vars.items():
            var.set(f"{key}: 0")

    def _load_report(self, report: dict) -> None:
        self.report = report
        summary = report.get("summary", {})
        review_count = report.get("review_summary", {}).get(
            "review_required",
            len(report.get("review_queue", [])),
        )
        manual_count = (report.get("manual_review_summary") or {}).get(
            "total",
            len(report.get("manual_review_queue", [])),
        )
        for key in ("PASS", "FAIL", "WARN", "NA", "ERROR"):
            self.summary_vars[key].set(f"{key}: {summary.get(key, 0)}")
        self.summary_vars["Review"].set(f"Review: {review_count} + manual {manual_count}")

        for result in report.get("results", []):
            if result.get("status") in {"PASS", "NA"}:
                continue
            values = (
                result.get("result_id", ""),
                result.get("check_id", ""),
                result.get("iq_level", ""),
                result.get("status", ""),
                result.get("scope", ""),
                result.get("subject", ""),
                result.get("message", ""),
            )
            self.results_tree.insert("", tk.END, iid=result.get("result_id"), values=values)

        for item in self._review_items():
            result_id = item.get("review_key") or item.get("result_id") or item.get("manual_key")
            kind = item.get("item_type") or (
                "manual" if item.get("automation_class") == "manual" else "semi-auto"
            )
            self.review_decisions[result_id] = {
                "decision": DECISIONS[0],
                "comment": "",
                "external_evidence": "",
                "datasheet_section": "",
                "model_maker_action": "",
            }
            values = (
                result_id,
                kind,
                item.get("check_id", ""),
                item.get("iq_level", ""),
                item.get("effective_status") or item.get("status", ""),
                item.get("scope", ""),
                item.get("subject", ""),
                DECISIONS[0],
                item.get("message", "") or item.get("title", ""),
            )
            self.review_tree.insert("", tk.END, iid=result_id, values=values)

        file_name = Path(report.get("file", "")).name or "IBIS file"
        max_level = report.get("max_level")
        target = f"IQ{max_level}" if max_level else "all implemented levels"
        self.status_var.set(f"Finished {file_name} up to {target}. {review_count} semi-auto and {manual_count} manual item(s) need review.")
        self._set_busy(False)
        self.apply_selected_button.configure(state=tk.NORMAL if self.review_tree.get_children() else tk.DISABLED)
        self.accept_selected_button.configure(state=tk.NORMAL if self.review_tree.get_children() else tk.DISABLED)
        self.na_selected_button.configure(state=tk.NORMAL if self.review_tree.get_children() else tk.DISABLED)

    def _review_items(self) -> list[dict]:
        if self.report is None:
            return []
        return list(self.report.get("review_queue", [])) + list(self.report.get("manual_review_queue", []))

    def _on_review_select(self, _event=None) -> None:
        if self.selected_review_id:
            self._apply_decision(silent=True)

        selection = self.review_tree.selection()
        if not selection or self.report is None:
            self.selected_review_id = None
            self.apply_button.configure(state=tk.DISABLED)
            return

        result_id = selection[0]
        self.selected_review_id = result_id
        item = self._review_item_by_id(result_id)
        decision = self.review_decisions.get(result_id, {})
        self.decision_var.set(decision.get("decision", DECISIONS[0]))
        self.comment_text.delete("1.0", tk.END)
        self.comment_text.insert("1.0", decision.get("comment", ""))
        self.evidence_var.set(decision.get("external_evidence", ""))
        self.datasheet_var.set(decision.get("datasheet_section", ""))
        self.action_text.delete("1.0", tk.END)
        self.action_text.insert("1.0", decision.get("model_maker_action", ""))
        self._set_detail(self._format_result_detail(item))
        self.apply_button.configure(state=tk.NORMAL)

    def _review_item_by_id(self, result_id: str) -> dict:
        if self.report is None:
            return {}
        for item in self._review_items():
            keys = {
                item.get("review_key"),
                item.get("result_id"),
                item.get("result_key"),
                item.get("manual_key"),
            }
            if result_id in keys:
                return item
        return {}

    def _format_result_detail(self, result: dict) -> str:
        if not result:
            return ""

        lines = [
            f"Review Key: {result.get('review_key') or result.get('result_id') or result.get('manual_key') or ''}",
            f"Check: {result.get('check_id', '')}",
            f"IQ Level: {result.get('iq_level', '')}",
            f"Status: {result.get('effective_status') or result.get('status', '')}",
            f"Type: {result.get('item_type') or result.get('automation_class', '')}",
            f"Scope: {result.get('scope', '')}",
            f"Subject: {result.get('subject', '')}",
            f"Spec Ref: {result.get('spec_ref', '')}",
            "",
            "Message:",
            result.get("message", "") or result.get("title", ""),
        ]
        details = result.get("details") or []
        if details:
            lines.extend(["", "Evidence:"])
            lines.extend(str(detail) for detail in details)
        return "\n".join(lines)

    def _set_detail(self, text: str) -> None:
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", text)
        self.detail_text.configure(state=tk.DISABLED)

    def _apply_decision(self, silent: bool = False) -> None:
        if not self.selected_review_id:
            if not silent:
                messagebox.showinfo("No review item", "Select a review item first.")
            return

        comment = self.comment_text.get("1.0", tk.END).strip()
        decision = self.decision_var.get() or DECISIONS[0]
        if decision == "Exception" and not comment:
            if not silent:
                messagebox.showwarning("Comment required", "Exception decisions require a reviewer comment.")
            return
        self.review_decisions[self.selected_review_id] = {
            "decision": decision,
            "comment": comment,
            "external_evidence": self.evidence_var.get().strip(),
            "datasheet_section": self.datasheet_var.get().strip(),
            "model_maker_action": self.action_text.get("1.0", tk.END).strip(),
        }

        values = list(self.review_tree.item(self.selected_review_id, "values"))
        if len(values) >= 8:
            values[7] = decision
            self.review_tree.item(self.selected_review_id, values=values)

        if not silent:
            self.status_var.set(f"Applied review decision for {self.selected_review_id}.")

    def _apply_to_selected(self) -> None:
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showinfo("No review item", "Select one or more review items first.")
            return
        comment = self.comment_text.get("1.0", tk.END).strip()
        decision = self.decision_var.get() or DECISIONS[0]
        if decision == "Exception" and not comment:
            messagebox.showwarning("Comment required", "Exception decisions require a reviewer comment.")
            return
        for review_id in selection:
            self._set_decision_for_key(
                review_id,
                decision,
                comment,
                self.evidence_var.get().strip(),
                self.datasheet_var.get().strip(),
                self.action_text.get("1.0", tk.END).strip(),
            )
        self.status_var.set(f"Applied {decision} to {len(selection)} selected item(s).")

    def _batch_decision(self, decision: str) -> None:
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showinfo("No review item", "Select one or more review items first.")
            return
        for review_id in selection:
            existing = self.review_decisions.get(review_id, {})
            self._set_decision_for_key(
                review_id,
                decision,
                existing.get("comment", ""),
                existing.get("external_evidence", ""),
                existing.get("datasheet_section", ""),
                existing.get("model_maker_action", ""),
            )
        self.status_var.set(f"Applied {decision} to {len(selection)} selected item(s).")

    def _set_decision_for_key(
            self,
            review_id: str,
            decision: str,
            comment: str = "",
            external_evidence: str = "",
            datasheet_section: str = "",
            model_maker_action: str = "") -> None:
        self.review_decisions[review_id] = {
            "decision": decision,
            "comment": comment,
            "external_evidence": external_evidence,
            "datasheet_section": datasheet_section,
            "model_maker_action": model_maker_action,
        }
        values = list(self.review_tree.item(review_id, "values"))
        if len(values) >= 8:
            values[7] = decision
            self.review_tree.item(review_id, values=values)

    def _save_report(self) -> None:
        if self.report is None:
            return

        default_name = self._default_output_name(".qa.json")
        path = filedialog.asksaveasfilename(
            title="Save QA report",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        json_path = Path(path)
        markdown_path = json_path.with_suffix(".md")
        html_path = json_path.with_suffix(".html")
        spreadsheet_path = json_path.with_suffix(".xlsx")
        asset_dir = markdown_path.with_name(f"{markdown_path.stem}_assets")
        self._apply_decision(silent=True)
        review_payload = self._review_payload()
        reviewed_report = apply_review_decisions(self.report, review_payload, copy_report=True)
        json_path.write_text(json.dumps(reviewed_report, indent=2), encoding="utf-8")
        markdown_path.write_text(
            render_markdown_report(
                reviewed_report,
                asset_dir=asset_dir,
                asset_ref_prefix=asset_dir.name,
            ),
            encoding="utf-8",
        )
        html_path.write_text(
            render_html_report(
                reviewed_report,
                asset_dir=asset_dir,
                asset_ref_prefix=asset_dir.name,
            ),
            encoding="utf-8",
        )
        write_spreadsheet_report(
            reviewed_report,
            spreadsheet_path,
            target_level=reviewed_report.get("max_level"),
            review_decisions=review_payload,
        )
        self.status_var.set(
            f"Saved QA report to {json_path}, Markdown to {markdown_path}, HTML to {html_path}, curves to {asset_dir}, and spreadsheet to {spreadsheet_path}."
        )

    def _save_review(self) -> None:
        if self.report is None:
            return

        self._apply_decision(silent=True)
        payload = self._review_payload()

        default_name = self._default_output_name(".review.json")
        path = filedialog.asksaveasfilename(
            title="Save review decisions",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.status_var.set(f"Saved review decisions to {path}.")

    def _load_review(self) -> None:
        if self.report is None:
            return

        path = filedialog.askopenfilename(
            title="Load review decisions",
            filetypes=[("Review JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Could not load review", f"{type(exc).__name__}: {exc}")
            return

        info = payload.get("reviewer_info", {}) if isinstance(payload, dict) else {}
        self.reviewer_var.set(info.get("reviewer", payload.get("reviewer", "")))
        self.organization_var.set(info.get("organization", payload.get("organization", "")))
        self.approval_date_var.set(info.get("approval_date", payload.get("approval_date", "")))

        indexed = load_review_decisions(payload)
        for item in self._review_items():
            key = item.get("review_key") or item.get("result_id") or item.get("manual_key")
            decision = decision_for_item(item, indexed)
            if not key or not decision:
                continue
            self.review_decisions[key] = {
                "decision": decision.get("decision", DECISIONS[0]),
                "comment": decision.get("comment", ""),
                "external_evidence": decision.get("external_evidence", ""),
                "datasheet_section": decision.get("datasheet_section", ""),
                "model_maker_action": decision.get("model_maker_action", ""),
            }
            if self.review_tree.exists(key):
                values = list(self.review_tree.item(key, "values"))
                if len(values) >= 8:
                    values[7] = self.review_decisions[key]["decision"]
                    self.review_tree.item(key, values=values)

        self.report = apply_review_decisions(self.report, payload)
        self.status_var.set(f"Loaded review decisions from {path}.")

    def _review_payload(self) -> dict:
        if self.report is None:
            return {"schema_version": 2, "decisions": []}

        return make_review_payload(
            self.report,
            self.review_decisions,
            reviewer=self.reviewer_var.get().strip(),
            organization=self.organization_var.get().strip(),
            approval_date=self.approval_date_var.get().strip(),
        )

    def _default_output_name(self, suffix: str) -> str:
        if self.ibis_path is not None:
            return f"{self.ibis_path.stem}{suffix}"
        if self.report is not None and self.report.get("file"):
            return f"{Path(self.report['file']).stem}{suffix}"
        return f"ibis{suffix}"

    def _selected_max_level(self) -> int | None:
        value = self.max_level_var.get()
        if value.startswith("IQ"):
            try:
                return int(value[2:])
            except ValueError:
                return None
        return None


def main() -> None:
    app = IbisQaGui()
    app.mainloop()


if __name__ == "__main__":
    main()

"""Tkinter GUI for running IBIS QA and reviewing semi-auto evidence."""

from __future__ import annotations

import json
import queue
import sys
import threading
from collections import Counter
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from parser.ibis_parser import IBISParser
from runner import CheckRunner
from reporter import Reporter


DECISIONS = [
    "Pending",
    "Accepted",
    "Exception",
    "Rejected",
    "Not Applicable",
]


def run_qa_report(path: Path) -> dict:
    """Run the existing parser/checker/reporter pipeline and return a report dict."""
    ibis_file = IBISParser().parse(path)
    results = CheckRunner().run(ibis_file)
    return Reporter(results, ibis_file, verbose=True).as_dict()


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
        root.rowconfigure(3, weight=1)

        file_bar = ttk.Frame(root)
        file_bar.grid(row=0, column=0, sticky="ew")
        file_bar.columnconfigure(0, weight=1)

        self.path_entry = ttk.Entry(file_bar, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.browse_button = ttk.Button(file_bar, text="Browse", command=self._browse)
        self.browse_button.grid(row=0, column=1, padx=(0, 8))
        self.run_button = ttk.Button(file_bar, text="Run QA", command=self._run_qa)
        self.run_button.grid(row=0, column=2, padx=(0, 8))
        self.save_report_button = ttk.Button(
            file_bar, text="Save Report", command=self._save_report, state=tk.DISABLED
        )
        self.save_report_button.grid(row=0, column=3, padx=(0, 8))
        self.save_review_button = ttk.Button(
            file_bar, text="Save Review", command=self._save_review, state=tk.DISABLED
        )
        self.save_review_button.grid(row=0, column=4)

        ttk.Label(root, textvariable=self.status_var).grid(
            row=1, column=0, sticky="ew", pady=(8, 4)
        )

        summary = ttk.Frame(root)
        summary.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        for col, (key, var) in enumerate(self.summary_vars.items()):
            label = ttk.Label(summary, textvariable=var)
            label.grid(row=0, column=col, padx=(0, 18), sticky="w")

        panes = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        panes.grid(row=3, column=0, sticky="nsew")

        notebook = ttk.Notebook(panes)
        self.results_tree = self._make_tree(
            notebook,
            ("result_id", "check_id", "status", "scope", "subject", "message"),
            {
                "result_id": 74,
                "check_id": 72,
                "status": 68,
                "scope": 96,
                "subject": 170,
                "message": 430,
            },
        )
        self.review_tree = self._make_tree(
            notebook,
            ("result_id", "check_id", "status", "scope", "subject", "decision", "message"),
            {
                "result_id": 74,
                "check_id": 72,
                "status": 68,
                "scope": 90,
                "subject": 140,
                "decision": 118,
                "message": 360,
            },
        )
        self.review_tree.bind("<<TreeviewSelect>>", self._on_review_select)
        notebook.add(self.results_tree.master, text="Results")
        notebook.add(self.review_tree.master, text="Review Queue")
        panes.add(notebook, weight=3)

        detail = ttk.Frame(panes, padding=(10, 0, 0, 0))
        detail.columnconfigure(0, weight=1)
        detail.rowconfigure(1, weight=1)
        detail.rowconfigure(5, weight=1)
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

        self.apply_button = ttk.Button(
            detail, text="Apply Decision", command=self._apply_decision, state=tk.DISABLED
        )
        self.apply_button.grid(row=6, column=0, sticky="e")

    def _make_tree(
            self,
            parent: ttk.Notebook,
            columns: tuple[str, ...],
            widths: dict[str, int]) -> ttk.Treeview:
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
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
        self.status_var.set(f"Running QA for {path.name} ...")

        thread = threading.Thread(target=self._worker_run, args=(path,), daemon=True)
        thread.start()

    def _worker_run(self, path: Path) -> None:
        try:
            self.work_queue.put(("report", run_qa_report(path)))
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
        if busy or self.report is None:
            self.save_report_button.configure(state=tk.DISABLED)
            self.save_review_button.configure(state=tk.DISABLED)
        else:
            self.save_report_button.configure(state=tk.NORMAL)
            self.save_review_button.configure(state=tk.NORMAL)

    def _clear_trees(self) -> None:
        for tree in (self.results_tree, self.review_tree):
            tree.delete(*tree.get_children())
        self._set_detail("")
        self.comment_text.delete("1.0", tk.END)
        self.decision_var.set(DECISIONS[0])
        self.apply_button.configure(state=tk.DISABLED)
        for key, var in self.summary_vars.items():
            var.set(f"{key}: 0")

    def _load_report(self, report: dict) -> None:
        self.report = report
        summary = report.get("summary", {})
        review_count = report.get("review_summary", {}).get(
            "review_required",
            len(report.get("review_queue", [])),
        )
        for key in ("PASS", "FAIL", "WARN", "NA", "ERROR"):
            self.summary_vars[key].set(f"{key}: {summary.get(key, 0)}")
        self.summary_vars["Review"].set(f"Review: {review_count}")

        for result in report.get("results", []):
            if result.get("status") in {"PASS", "NA"}:
                continue
            values = (
                result.get("result_id", ""),
                result.get("check_id", ""),
                result.get("status", ""),
                result.get("scope", ""),
                result.get("subject", ""),
                result.get("message", ""),
            )
            self.results_tree.insert("", tk.END, iid=result.get("result_id"), values=values)

        for item in report.get("review_queue", []):
            result_id = item.get("result_id", "")
            self.review_decisions[result_id] = {
                "decision": DECISIONS[0],
                "comment": "",
            }
            values = (
                result_id,
                item.get("check_id", ""),
                item.get("status", ""),
                item.get("scope", ""),
                item.get("subject", ""),
                DECISIONS[0],
                item.get("message", ""),
            )
            self.review_tree.insert("", tk.END, iid=result_id, values=values)

        file_name = Path(report.get("file", "")).name or "IBIS file"
        self.status_var.set(f"Finished {file_name}. {review_count} item(s) need review.")
        self._set_busy(False)

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
        self._set_detail(self._format_result_detail(item))
        self.apply_button.configure(state=tk.NORMAL)

    def _review_item_by_id(self, result_id: str) -> dict:
        if self.report is None:
            return {}
        for item in self.report.get("review_queue", []):
            if item.get("result_id") == result_id:
                return item
        return {}

    def _format_result_detail(self, result: dict) -> str:
        if not result:
            return ""

        lines = [
            f"Result ID: {result.get('result_id', '')}",
            f"Check: {result.get('check_id', '')}",
            f"Status: {result.get('status', '')}",
            f"Scope: {result.get('scope', '')}",
            f"Subject: {result.get('subject', '')}",
            f"Spec Ref: {result.get('spec_ref', '')}",
            "",
            "Message:",
            result.get("message", ""),
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
        self.review_decisions[self.selected_review_id] = {
            "decision": decision,
            "comment": comment,
        }

        values = list(self.review_tree.item(self.selected_review_id, "values"))
        if len(values) >= 6:
            values[5] = decision
            self.review_tree.item(self.selected_review_id, values=values)

        if not silent:
            self.status_var.set(f"Applied review decision for {self.selected_review_id}.")

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

        Path(path).write_text(json.dumps(self.report, indent=2), encoding="utf-8")
        self.status_var.set(f"Saved QA report to {path}.")

    def _save_review(self) -> None:
        if self.report is None:
            return

        self._apply_decision(silent=True)
        decisions = []
        for item in self.report.get("review_queue", []):
            result_id = item.get("result_id", "")
            review = self.review_decisions.get(
                result_id,
                {"decision": DECISIONS[0], "comment": ""},
            )
            decisions.append({
                "result_id": result_id,
                "check_id": item.get("check_id", ""),
                "scope": item.get("scope", ""),
                "subject": item.get("subject", ""),
                "decision": review.get("decision", DECISIONS[0]),
                "comment": review.get("comment", ""),
                "source_result": item,
            })

        payload = {
            "schema_version": 1,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "ibis_file": self.report.get("file", ""),
            "summary": self.report.get("summary", {}),
            "review_summary": self.report.get("review_summary", {}),
            "decision_summary": dict(Counter(d["decision"] for d in decisions)),
            "decisions": decisions,
        }

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

    def _default_output_name(self, suffix: str) -> str:
        if self.ibis_path is not None:
            return f"{self.ibis_path.stem}{suffix}"
        if self.report is not None and self.report.get("file"):
            return f"{Path(self.report['file']).stem}{suffix}"
        return f"ibis{suffix}"


def main() -> None:
    app = IbisQaGui()
    app.mainloop()


if __name__ == "__main__":
    main()

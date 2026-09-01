"""
Universal File Converter
========================
A simple drag-and-drop desktop app for converting images, documents,
audio, and video files. Built with Tkinter so it packages into a single
lightweight .exe with PyInstaller.
"""
import os
import queue
import sys
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from converters.images import IMAGE_FORMATS, SUPPORTED_INPUT_EXTENSIONS as IMAGE_EXTS, convert_image
from converters.documents import DOCUMENT_FORMATS, SUPPORTED_INPUT_EXTENSIONS as DOC_EXTS, convert_document
from converters.video import VIDEO_FORMATS, AUDIO_FORMATS, SUPPORTED_INPUT_EXTENSIONS as VIDEO_EXTS, convert_video

APP_TITLE = "Universal File Converter"


def classify(path: str) -> str:
    """Return 'image', 'document', 'video', or 'unknown' for a file path."""
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in DOC_EXTS:
        return "document"
    if ext in VIDEO_EXTS:
        return "video"
    return "unknown"


def output_options_for(category: str, ext: str):
    """Return the list of valid target format strings for a category/extension."""
    if category == "image":
        return list(IMAGE_FORMATS.keys())
    if category == "document":
        opts = DOCUMENT_FORMATS.get(ext, [])
        return [o.lstrip(".").upper() for o in opts]
    if category == "video":
        return [f.upper() for f in VIDEO_FORMATS + AUDIO_FORMATS]
    return []


class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("640x480")
        self.root.minsize(520, 400)

        self.files = []  # list of str paths
        self.output_dir = tk.StringVar(value="")
        self.target_format = tk.StringVar(value="")
        self.status_queue = queue.Queue()

        self._build_ui()
        self._poll_queue()

    # ---------------------------------------------------------- UI setup
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        header = ttk.Label(
            self.root, text=APP_TITLE, font=("Segoe UI", 16, "bold")
        )
        header.pack(anchor="w", **pad)

        sub = "Drag files here, or click Add Files" if DND_AVAILABLE else "Click Add Files to choose files"
        ttk.Label(self.root, text=sub, foreground="#555").pack(anchor="w", padx=10)

        # Drop zone / file list
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, **pad)

        self.listbox = tk.Listbox(list_frame, selectmode="extended")
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        if DND_AVAILABLE:
            self.listbox.drop_target_register(DND_FILES)
            self.listbox.dnd_bind("<<Drop>>", self._on_drop)

        # Buttons row: add / remove files
        btn_row = ttk.Frame(self.root)
        btn_row.pack(fill="x", **pad)
        ttk.Button(btn_row, text="Add Files...", command=self._add_files).pack(side="left")
        ttk.Button(btn_row, text="Remove Selected", command=self._remove_selected).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Clear All", command=self._clear_files).pack(side="left")

        # Output format + folder
        options_frame = ttk.Frame(self.root)
        options_frame.pack(fill="x", **pad)

        ttk.Label(options_frame, text="Convert to:").grid(row=0, column=0, sticky="w")
        self.format_combo = ttk.Combobox(
            options_frame, textvariable=self.target_format, state="readonly", width=15
        )
        self.format_combo.grid(row=0, column=1, sticky="w", padx=(6, 20))

        ttk.Label(options_frame, text="Save to:").grid(row=0, column=2, sticky="w")
        self.output_label = ttk.Label(options_frame, textvariable=self.output_dir, foreground="#555")
        self.output_label.grid(row=0, column=3, sticky="w", padx=6)
        ttk.Button(options_frame, text="Choose...", command=self._choose_output_dir).grid(row=0, column=4)

        # Convert button + progress
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", **pad)
        self.convert_btn = ttk.Button(action_frame, text="Convert", command=self._start_conversion)
        self.convert_btn.pack(side="left")
        self.progress = ttk.Progressbar(action_frame, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=10)

        # Status log
        self.status_text = tk.Text(self.root, height=6, state="disabled", wrap="word")
        self.status_text.pack(fill="both", expand=False, padx=10, pady=(0, 10))

    # ---------------------------------------------------------- file mgmt
    def _on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        self._add_paths(paths)

    def _add_files(self):
        paths = filedialog.askopenfilenames(title="Select files to convert")
        if paths:
            self._add_paths(paths)

    def _add_paths(self, paths):
        for p in paths:
            p = str(p)
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", os.path.basename(p))
        self._refresh_format_options()
        if self.files and not self.output_dir.get():
            self.output_dir.set(str(Path(self.files[0]).parent / "converted"))

    def _remove_selected(self):
        selected = list(self.listbox.curselection())
        for idx in reversed(selected):
            self.listbox.delete(idx)
            del self.files[idx]
        self._refresh_format_options()

    def _clear_files(self):
        self.listbox.delete(0, "end")
        self.files.clear()
        self._refresh_format_options()

    def _choose_output_dir(self):
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            self.output_dir.set(d)

    def _refresh_format_options(self):
        if not self.files:
            self.format_combo["values"] = []
            self.target_format.set("")
            return
        categories = {classify(f) for f in self.files}
        if len(categories) > 1 or "unknown" in categories:
            self.format_combo["values"] = []
            self.target_format.set("")
            self._log("Please convert one file type at a time (all images, all documents, or all video/audio).")
            return
        category = categories.pop()
        ext = Path(self.files[0]).suffix.lower()
        options = output_options_for(category, ext)
        self.format_combo["values"] = options
        if options:
            self.target_format.set(options[0])

    # ---------------------------------------------------------- convert
    def _start_conversion(self):
        if not self.files:
            messagebox.showwarning(APP_TITLE, "Add at least one file first.")
            return
        if not self.target_format.get():
            messagebox.showwarning(APP_TITLE, "Choose an output format.")
            return
        if not self.output_dir.get():
            self.output_dir.set(str(Path(self.files[0]).parent / "converted"))

        self.convert_btn.config(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.files)

        thread = threading.Thread(target=self._run_conversion, daemon=True)
        thread.start()

    def _run_conversion(self):
        target = self.target_format.get()
        out_dir = Path(self.output_dir.get())
        successes, failures = 0, 0

        for f in self.files:
            src = Path(f)
            category = classify(f)
            out_ext = target.lower() if not target.lower().startswith(".") else target.lower()
            out_ext = out_ext.lstrip(".")
            out_path = out_dir / f"{src.stem}.{out_ext}"
            try:
                if category == "image":
                    convert_image(str(src), str(out_path), target)
                elif category == "document":
                    convert_document(str(src), str(out_path), f".{out_ext}")
                elif category == "video":
                    convert_video(str(src), str(out_path), out_ext)
                else:
                    raise ValueError("Unknown file type")
                self.status_queue.put(("ok", f"Converted: {src.name} -> {out_path.name}"))
                successes += 1
            except Exception as e:
                self.status_queue.put(("err", f"Failed: {src.name} ({e})"))
                traceback.print_exc()
                failures += 1
            self.status_queue.put(("progress", None))

        self.status_queue.put(("done", (successes, failures, str(out_dir))))

    # ---------------------------------------------------------- polling
    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.status_queue.get_nowait()
                if kind in ("ok", "err"):
                    self._log(payload)
                elif kind == "progress":
                    self.progress["value"] += 1
                elif kind == "done":
                    successes, failures, out_dir = payload
                    self.convert_btn.config(state="normal")
                    self._log(f"Done. {successes} succeeded, {failures} failed. Output: {out_dir}")
                    messagebox.showinfo(
                        APP_TITLE,
                        f"{successes} file(s) converted successfully.\n"
                        f"{failures} failed.\nSaved to:\n{out_dir}",
                    )
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _log(self, message: str):
        self.status_text.config(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.config(state="disabled")


def main():
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

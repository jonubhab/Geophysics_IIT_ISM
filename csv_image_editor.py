"""
Batch CSV Editor with paired Image Viewer
------------------------------------------
Requires: Pillow  ->  pip install Pillow

Usage:
    python csv_image_editor.py

On launch, folder pickers appear directly (Choose Image Folder, then
Choose CSV Folder). Files are paired by ALPHABETICAL SORT ORDER.
If your filenames aren't zero-padded (img1, img2, ... img10), sorting
will misorder them after the 9th file.

Each CSV is assumed to have one header row followed by data rows, with
exactly two columns. The 1st column and header are read-only.

Editing (deletion-first workflow):
  - Plain click on a row   -> toggle that row in/out of the selection
  - Shift-click             -> range-select rows
  - Ctrl-click a 2nd-column cell -> open inline editor for that cell
  - Delete / Backspace      -> clear the 2nd-column value for all
                                selected rows
  - Ctrl+Z / Undo button    -> undo the last edit or clear (per file;
                                undo history resets when you navigate)

Navigation autosaves the current CSV: Previous, Next, and the
"Jump to file" box. The Delete button removes the current image+CSV
pair from disk with NO confirmation (by design) -- this is NOT
undoable.
"""

import os
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"}

SHIFT_MASK = 0x0001
CTRL_MASK = 0x0004


class CSVImageEditor(tk.Tk):
    EDITABLE_COLUMN = "#2"
    EDITABLE_COL_INDEX = 1
    MAX_UNDO = 50

    def __init__(self):
        super().__init__()
        self.title("Batch CSV Editor")

        self.dark_mode = False
        self.current_index = 0
        self.edit_entry = None
        self._edit_row_id = None
        self.original_pil_image = None
        self.tree_columns = []
        self.undo_stack = []

        self.withdraw()
        self.image_dir, self.csv_dir = self._prompt_for_folders()
        self.deiconify()
        if not self.image_dir or not self.csv_dir:
            self.destroy()
            return

        self.image_files = self._list_files(self.image_dir, IMAGE_EXTS)
        self.csv_files = self._list_files(self.csv_dir, {".csv"})

        self.image_files, self.csv_files = self._match_pairs_by_convention(
            self.image_files, self.csv_files
        )

        self.pair_count = len(self.image_files)
        if self.pair_count == 0:
            messagebox.showerror("No files", "No image/CSV pairs matched the naming convention.")
            self.destroy()
            return

        self._rebuild_pair_labels()

        self._build_ui()
        self._bind_shortcuts()
        self._maximize_window()
        self.load_pair(0)

    # ---------------------------------------------------------------- setup
    def _prompt_for_folders(self):
        image_dir = filedialog.askdirectory(title="Choose Image Folder",initialdir="/home/arjun/WESTERN-TIBET/Control/DISP CURVE PLOTS/01")
        if not image_dir:
            return None, None
        csv_dir = filedialog.askdirectory(title="Choose CSV Folder",initialdir="/home/arjun/WESTERN-TIBET/Control/TOMO_DISP/01")
        if not csv_dir:
            return None, None
        return image_dir, csv_dir

    def _list_files(self, folder, exts):
        files = [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in exts]
        return sorted(files)

    def _match_pairs_by_convention(self, image_files, csv_files):
        """Pair by filename convention, not by list order/position.

        Image:  'A - B.ext'          (e.g. 'Y2.GARY - Y2.GUGE.png')
        CSV:    'A_B_MEAN.csv'       (e.g. 'Y2_GARY_Y2_GUGE_MEAN.csv')
        derived by replacing '.' -> '_' in each side of the image stem.

        Assumes the station order is identical on both sides (A_B, not
        B_A). Reversed-order matches are NOT attempted -- a silent
        reversed match would be worse than a visible drop.
        """
        csv_lookup = {f.lower(): f for f in csv_files}
        paired_images, paired_csvs = [], []
        unmatched_images = []

        for img in image_files:
            stem = os.path.splitext(img)[0]
            if " - " not in stem:
                unmatched_images.append(img)
                continue
            left, right = (p.strip() for p in stem.split(" - ", 1))
            expected = f"{left.replace('.', '_')}_{right.replace('.', '_')}_MEAN.csv"
            match = csv_lookup.pop(expected.lower(), None)
            if match is None:
                unmatched_images.append(img)
                continue
            paired_images.append(img)
            paired_csvs.append(match)

        unmatched_csvs = list(csv_lookup.values())

        if unmatched_images or unmatched_csvs:
            lines = []
            if unmatched_images:
                lines.append(f"{len(unmatched_images)} image(s) with no matching CSV:")
                lines += [f"  {f}" for f in unmatched_images[:10]]
                if len(unmatched_images) > 10:
                    lines.append(f"  ...and {len(unmatched_images) - 10} more.")
            if unmatched_csvs:
                lines.append(f"{len(unmatched_csvs)} CSV(s) with no matching image:")
                lines += [f"  {f}" for f in unmatched_csvs[:10]]
                if len(unmatched_csvs) > 10:
                    lines.append(f"  ...and {len(unmatched_csvs) - 10} more.")
            messagebox.showwarning(
                "Unmatched files excluded",
                f"{len(paired_images)} pairs matched.\n\n"
                "These files were dropped (not shown, not editable):\n\n"
                + "\n".join(lines),
            )

        # Sort matched pairs by image name so navigation order is stable
        # and deterministic across runs.
        order = sorted(range(len(paired_images)), key=lambda i: paired_images[i].lower())
        paired_images = [paired_images[i] for i in order]
        paired_csvs = [paired_csvs[i] for i in order]
        return paired_images, paired_csvs

    def _rebuild_pair_labels(self):
        # Label = image filename without extension. Used verbatim as the
        # search key in the jump box -- no filename parsing needed since
        # it's already unique and human-readable.
        self.pair_labels = [os.path.splitext(f)[0] for f in self.image_files[: self.pair_count]]

    def _maximize_window(self):
        # Maximized, not true fullscreen: keeps title bar with
        # minimize/maximize/close buttons (Ubuntu/X11 -> -zoomed;
        # Windows -> state('zoomed')).
        try:
            self.attributes("-zoomed", True)
        except tk.TclError:
            try:
                self.state("zoomed")
            except tk.TclError:
                self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

    def _bind_shortcuts(self):
        self.bind("<Left>", lambda e: self.go_previous())
        self.bind("<Right>", lambda e: self.go_next())
        self.bind_all("<Control-z>", lambda e: self.undo())
        self.bind_all("<Control-Z>", lambda e: self.undo())

    # ------------------------------------------------------------- UI build
    def _build_ui(self):
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        # Status bar
        self.status_label = tk.Label(self.main_frame, font=("Segoe UI", 11, "bold"))
        self.status_label.pack(side="top", fill="x", pady=(4, 0))

        # Search / jump-to-file bar
        search_bar = tk.Frame(self.main_frame)
        search_bar.pack(side="top", fill="x", pady=(2, 4), padx=8)
        self.search_label = tk.Label(search_bar, text="Jump to file (type to search, Enter to go):")
        self.search_label.pack(side="left")
        self.search_box = ttk.Combobox(search_bar, values=self.pair_labels, width=60)
        self.search_box.pack(side="left", padx=6)
        self.search_box.bind("<<ComboboxSelected>>", self._on_search_select)
        self.search_box.bind("<Return>", self._on_search_enter)

        # Panels
        panels = tk.Frame(self.main_frame)
        panels.pack(fill="both", expand=True)

        # Left: image panel
        self.image_frame = tk.Frame(panels, bd=2, relief="groove")
        self.image_frame.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        self.image_canvas = tk.Canvas(self.image_frame, highlightthickness=0)
        self.image_canvas.pack(fill="both", expand=True)
        self.image_canvas.bind("<Configure>", lambda e: self._render_image())

        # Right: csv panel
        self.csv_frame = tk.Frame(panels, bd=2, relief="groove")
        self.csv_frame.pack(side="right", fill="both", expand=True, padx=4, pady=4)

        tree_container = tk.Frame(self.csv_frame)
        tree_container.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_container, show="headings", selectmode="extended")
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        # Deletion-first click model: our instance-level binding fires
        # BEFORE ttk's built-in class-level selection binding (Tk processes
        # the widget's own bindtag first), so returning "break" here
        # suppresses the default behavior when we want to override it.
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Delete>", self._delete_selected_cells)
        self.tree.bind("<BackSpace>", self._delete_selected_cells)

        # Bottom: button panel
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(side="bottom", fill="x", pady=6)

        self.next_btn = tk.Button(self.button_frame, text="Next", width=15, command=self.go_next)
        self.next_btn.pack(side="right", padx=10)

        self.prev_btn = tk.Button(self.button_frame, text="Previous", width=15, command=self.go_previous)
        self.prev_btn.pack(side="right", padx=10)

        self.dark_btn = tk.Button(self.button_frame, text="Toggle Dark Mode", width=18, command=self.toggle_dark_mode)
        self.dark_btn.pack(side="left", padx=10)

        self.delete_btn = tk.Button(
            self.button_frame, text="Delete", width=15, bg="#c0392b", fg="white",
            activebackground="#a93226", activeforeground="white",
            command=self.delete_current_pair,
        )
        self.delete_btn.pack(side="left", padx=(30, 30))

        self.undo_btn = tk.Button(self.button_frame, text="Undo (Ctrl+Z)", width=15, command=self.undo)
        self.undo_btn.pack(side="left", padx=10)



        self._apply_theme()

    # ------------------------------------------------------------ data I/O
    def load_pair(self, index):
        self.current_index = index
        self.undo_stack = []
        img_path = os.path.join(self.image_dir, self.image_files[index])
        csv_path = os.path.join(self.csv_dir, self.csv_files[index])

        try:
            self.original_pil_image = Image.open(img_path)
            self.original_pil_image.load()
        except Exception as e:
            messagebox.showerror("Image load error", f"Could not open {img_path}\n{e}")
            self.original_pil_image = None
        self._render_image()

        self._load_csv_into_tree(csv_path)

        self.status_label.config(
            text=f"Pair {index + 1} / {self.pair_count}   |   "
                 f"Image: {self.image_files[index]}   |   CSV: {self.csv_files[index]}"
        )
        self.prev_btn.config(state="normal" if index > 0 else "disabled")
        self.next_btn.config(state="normal" if index < self.pair_count - 1 else "disabled")
        self.search_box.set(self.pair_labels[index])

    def _render_image(self):
        self.image_canvas.delete("all")
        if self.original_pil_image is None:
            return
        cw = self.image_canvas.winfo_width()
        ch = self.image_canvas.winfo_height()
        if cw < 2 or ch < 2:
            return
        img = self.original_pil_image.copy()
        img.thumbnail((cw, ch), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(img)
        self.image_canvas.create_image(cw // 2, ch // 2, image=self.tk_image, anchor="center")

    def _load_csv_into_tree(self, csv_path):
        self._cancel_edit()
        with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))

        header, rows = (reader[0], reader[1:]) if reader else ([], [])

        self.tree_columns = header
        self.tree["columns"] = header
        for col in header:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="w")

        self.tree.delete(*self.tree.get_children())
        for row in rows:
            row = (row + [""] * len(header))[: len(header)]
            self.tree.insert("", "end", values=row)

    def save_current_csv(self):
        self._commit_edit()
        csv_path = os.path.join(self.csv_dir, self.csv_files[self.current_index])
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.tree_columns)
            for item in self.tree.get_children():
                writer.writerow(self.tree.item(item, "values"))

    # ------------------------------------------------------------ selection / editing
    def _on_click(self, event):
        self.tree.focus_set()
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            # Blank space (below the last row, or margin) -> deselect all.
            self._commit_edit()
            self.tree.selection_set([])
            return "break"

        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)

        shift = bool(event.state & SHIFT_MASK)
        ctrl = bool(event.state & CTRL_MASK)

        if shift:
            # Let ttk's built-in range-select behavior run unmodified.
            return

        if ctrl:
            # Inverted mapping: ctrl+click now opens the editor.
            if column == self.EDITABLE_COLUMN:
                self._start_cell_edit(row_id)
            return "break"

        # Plain click: inverted mapping -> toggle this row in/out of the
        # selection (old ctrl+click behavior), instead of editing.
        current = set(self.tree.selection())
        if row_id in current:
            current.discard(row_id)
        else:
            current.add(row_id)
        self.tree.selection_set(list(current))
        return "break"

    def _start_cell_edit(self, row_id):
        bbox = self.tree.bbox(row_id, self.EDITABLE_COLUMN)
        if not bbox:
            return
        x, y, width, height = bbox
        value = self.tree.item(row_id, "values")[self.EDITABLE_COL_INDEX]

        self._cancel_edit()
        self.edit_entry = tk.Entry(self.tree)
        self.edit_entry.insert(0, value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus()
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self._edit_row_id = row_id

        self.edit_entry.bind("<Return>", lambda e: self._commit_edit())
        self.edit_entry.bind("<FocusOut>", lambda e: self._commit_edit())
        self.edit_entry.bind("<Escape>", lambda e: self._cancel_edit())

    def _snapshot(self):
        return [list(self.tree.item(i, "values")) for i in self.tree.get_children()]

    def _push_undo(self):
        self.undo_stack.append(self._snapshot())
        if len(self.undo_stack) > self.MAX_UNDO:
            self.undo_stack.pop(0)

    def _delete_selected_cells(self, event=None):
        """Clear the editable-column value for every selected row (Del/Backspace)."""
        self._cancel_edit()
        selected = self.tree.selection()
        if not selected:
            return
        self._push_undo()
        for row_id in selected:
            values = list(self.tree.item(row_id, "values"))
            values[self.EDITABLE_COL_INDEX] = ""
            self.tree.item(row_id, values=values)

    def _commit_edit(self):
        if self.edit_entry is None:
            return
        new_value = self.edit_entry.get()
        old_values = list(self.tree.item(self._edit_row_id, "values"))
        if old_values[self.EDITABLE_COL_INDEX] != new_value:
            self._push_undo()
            old_values[self.EDITABLE_COL_INDEX] = new_value
            self.tree.item(self._edit_row_id, values=old_values)
        self._cancel_edit()

    def _cancel_edit(self):
        if self.edit_entry is not None:
            self.edit_entry.destroy()
            self.edit_entry = None

    def undo(self):
        if not self.undo_stack:
            return
        self._cancel_edit()
        snapshot = self.undo_stack.pop()
        children = self.tree.get_children()
        for item_id, vals in zip(children, snapshot):
            self.tree.item(item_id, values=vals)

    # ------------------------------------------------------------ navigation
    def _jump_to_index(self, index):
        if index < 0 or index >= self.pair_count or index == self.current_index:
            return
        self.save_current_csv()
        self.load_pair(index)

    def go_next(self):
        self._jump_to_index(self.current_index + 1)

    def go_previous(self):
        self._jump_to_index(self.current_index - 1)

    def _on_search_select(self, event=None):
        label = self.search_box.get()
        if label in self.pair_labels:
            self._jump_to_index(self.pair_labels.index(label))
        self.tree.focus_set()

    def _on_search_enter(self, event=None):
        typed = self.search_box.get().strip().lower()
        if not typed:
            return
        if typed in (lbl.lower() for lbl in self.pair_labels):
            self._jump_to_index([l.lower() for l in self.pair_labels].index(typed))
            self.tree.focus_set()
            return
        matches = [i for i, lbl in enumerate(self.pair_labels) if typed in lbl.lower()]
        if matches:
            self._jump_to_index(matches[0])
        else:
            messagebox.showinfo("Not found", f"No file matching '{typed}'.")
        self.tree.focus_set()

    # ------------------------------------------------------------ delete pair
    def delete_current_pair(self):
        """Delete the current image+CSV pair from disk. No confirmation.
        This is NOT undoable -- files are gone once clicked."""
        idx = self.current_index
        img_path = os.path.join(self.image_dir, self.image_files[idx])
        csv_path = os.path.join(self.csv_dir, self.csv_files[idx])

        for path in (img_path, csv_path):
            try:
                os.remove(path)
            except OSError:
                pass

        del self.image_files[idx]
        del self.csv_files[idx]
        self.pair_count -= 1
        self._rebuild_pair_labels()
        self.search_box["values"] = self.pair_labels

        if self.pair_count == 0:
            messagebox.showinfo("Done", "No files remain.")
            self.destroy()
            return

        self.undo_stack = []
        new_index = min(idx, self.pair_count - 1)
        self.load_pair(new_index)

    # ------------------------------------------------------------ theming
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()

    def _apply_theme(self):
        if self.dark_mode:
            bg, fg, panel_bg = "#1e1e1e", "#e0e0e0", "#2a2a2a"
            btn_bg = "#3a3a3a"
        else:
            bg, fg, panel_bg = "#f0f0f0", "#000000", "#ffffff"
            btn_bg = "#e0e0e0"

        self.configure(bg=bg)
        self.main_frame.configure(bg=bg)
        self.status_label.configure(bg=bg, fg=fg)
        self.search_label.configure(bg=bg, fg=fg)
        self.image_frame.configure(bg=panel_bg)
        self.image_canvas.configure(bg=panel_bg)
        self.csv_frame.configure(bg=panel_bg)
        self.button_frame.configure(bg=bg)

        for widget in (self.prev_btn, self.next_btn, self.undo_btn, self.dark_btn):
            widget.configure(bg=btn_bg, fg=fg, activebackground=btn_bg, activeforeground=fg)
        # delete_btn keeps its fixed warning color regardless of theme

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=panel_bg, fieldbackground=panel_bg, foreground=fg)
        style.configure("Treeview.Heading", background=btn_bg, foreground=fg)
        style.map("Treeview", background=[("selected", "#4a6984")])


if __name__ == "__main__":
    app = CSVImageEditor()
    app.mainloop()
r"""Multiline coding UI for Hinagpis / SadBoy CodeX.

Run with:
    python .\hinagpis_ui.py
"""

import contextlib
import io
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from hinagpis import CodeXError, Interpreter, Lexer, compile_source


DEFAULT_CODE = """# Hinagpis / SadBoy CodeX multiline editor

gawa factorial(n) {
    kung (n <= 1) {
        balikan 1
    } o_else {
        balikan n * factorial(n - 1)
    }
}

numbers = [1, 2, 3, 4, 5]
sum = 0

para item sa numbers {
    sum = sum + item
}

print("sum =", sum)
print("factorial(5) =", factorial(5))
"""


class HinagpisUI:
    """Small Tkinter IDE for writing and running Hinagpis code."""

    def __init__(self, root):
        self.root = root
        self.root.title("Hinagpis / SadBoy CodeX IDE")
        self.root.geometry("1050x720")
        self.current_file = None

        self._configure_style()
        self._build_menu()
        self._build_layout()
        self._bind_shortcuts()

        self.editor.insert("1.0", DEFAULT_CODE)
        self._update_status("Ready")

    def _configure_style(self):
        self.root.configure(bg="#111827")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=6)
        style.configure("TLabel", background="#111827", foreground="#e5e7eb")
        style.configure("TFrame", background="#111827")

    def _build_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)

        run_menu = tk.Menu(menu_bar, tearoff=False)
        run_menu.add_command(label="Run", accelerator="F5", command=self.run_code)
        run_menu.add_command(label="Validate", accelerator="Ctrl+Enter", command=self.validate_code)
        run_menu.add_command(label="Show Tokens", command=self.show_tokens)
        run_menu.add_command(label="Clear Output", command=self.clear_output)

        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Run", menu=run_menu)
        self.root.config(menu=menu_bar)

    def _build_layout(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 4))

        ttk.Button(toolbar, text="New", command=self.new_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Run ▶ F5", command=self.run_code).pack(side=tk.LEFT, padx=12)
        ttk.Button(toolbar, text="Validate", command=self.validate_code).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Tokens", command=self.show_tokens).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=3)

        main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        editor_frame = ttk.Frame(main_pane)
        output_frame = ttk.Frame(main_pane)
        main_pane.add(editor_frame, weight=4)
        main_pane.add(output_frame, weight=1)

        editor_label = ttk.Label(editor_frame, text="Code Editor")
        editor_label.pack(anchor=tk.W)

        editor_container = ttk.Frame(editor_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)

        self.line_numbers = tk.Text(
            editor_container,
            width=5,
            padx=4,
            takefocus=0,
            border=0,
            background="#0f172a",
            foreground="#94a3b8",
            state=tk.DISABLED,
            font=("Consolas", 12),
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = tk.Text(
            editor_container,
            wrap=tk.NONE,
            undo=True,
            background="#020617",
            foreground="#e5e7eb",
            insertbackground="#f9fafb",
            selectbackground="#334155",
            font=("Consolas", 12),
            padx=10,
            pady=10,
        )
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        editor_scroll_y = ttk.Scrollbar(editor_container, orient=tk.VERTICAL, command=self._scroll_both)
        editor_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        editor_scroll_x = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=self.editor.xview)
        editor_scroll_x.pack(fill=tk.X)
        self.editor.configure(yscrollcommand=editor_scroll_y.set, xscrollcommand=editor_scroll_x.set)

        output_label = ttk.Label(output_frame, text="Output / Errors")
        output_label.pack(anchor=tk.W)

        self.output = tk.Text(
            output_frame,
            height=10,
            wrap=tk.WORD,
            background="#111827",
            foreground="#d1d5db",
            insertbackground="#f9fafb",
            font=("Consolas", 11),
            padx=10,
            pady=8,
        )
        self.output.pack(fill=tk.BOTH, expand=True)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=(4, 10))
        self.status = ttk.Label(status_frame, text="")
        self.status.pack(side=tk.LEFT)

        self.editor.bind("<KeyRelease>", lambda _event: self._refresh_line_numbers())
        self.editor.bind("<MouseWheel>", lambda _event: self._refresh_line_numbers())
        self.editor.bind("<ButtonRelease-1>", lambda _event: self._refresh_line_numbers())
        self._refresh_line_numbers()

    def _bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda _event: self.new_file())
        self.root.bind("<Control-o>", lambda _event: self.open_file())
        self.root.bind("<Control-s>", lambda _event: self.save_file())
        self.root.bind("<F5>", lambda _event: self.run_code())
        self.root.bind("<Control-Return>", lambda _event: self.validate_code())

    def _scroll_both(self, *args):
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

    def _refresh_line_numbers(self):
        line_count = int(self.editor.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.configure(state=tk.NORMAL)
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.configure(state=tk.DISABLED)

    def _get_code(self):
        return self.editor.get("1.0", "end-1c")

    def _write_output(self, text):
        self.output.insert(tk.END, text)
        if not text.endswith("\n"):
            self.output.insert(tk.END, "\n")
        self.output.see(tk.END)

    def _set_output(self, text):
        self.output.delete("1.0", tk.END)
        self._write_output(text)

    def _update_status(self, text):
        filename = self.current_file if self.current_file else "Untitled"
        self.status.configure(text=f"{text} | {filename}")

    def new_file(self):
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", DEFAULT_CODE)
        self.current_file = None
        self.clear_output()
        self._refresh_line_numbers()
        self._update_status("New file")

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open Hinagpis Code",
            filetypes=[("CodeX files", "*.codex"), ("Python files", "*.py"), ("All files", "*.*")],
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8-sig") as file:
            content = file.read()
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", content)
        self.current_file = path
        self._refresh_line_numbers()
        self._update_status("Opened")

    def save_file(self):
        if not self.current_file:
            return self.save_file_as()
        self._save_to_path(self.current_file)

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Hinagpis Code",
            defaultextension=".codex",
            filetypes=[("CodeX files", "*.codex"), ("All files", "*.*")],
        )
        if not path:
            return
        self.current_file = path
        self._save_to_path(path)

    def _save_to_path(self, path):
        with open(path, "w", encoding="utf-8") as file:
            file.write(self._get_code())
        self._update_status("Saved")

    def validate_code(self):
        try:
            compile_source(self._get_code(), optimize=True)
            self._set_output("Valid Hinagpis program. No syntax or semantic errors found.")
            self._update_status("Validated")
        except CodeXError as error:
            self._set_output(str(error))
            self._update_status("Validation failed")

    def show_tokens(self):
        try:
            tokens = Lexer(self._get_code()).tokenize()
            self._set_output("\n".join(str(token) for token in tokens))
            self._update_status("Tokens generated")
        except CodeXError as error:
            self._set_output(str(error))
            self._update_status("Tokenization failed")

    def run_code(self):
        code = self._get_code()
        stream = io.StringIO()
        try:
            ast = compile_source(code, optimize=True)
            interpreter = Interpreter()
            with contextlib.redirect_stdout(stream):
                result = interpreter.run(ast)
            output = stream.getvalue()
            if result is not None:
                output += str(result) + os.linesep
            self._set_output(output if output.strip() else "Program finished with no output.")
            self._update_status("Run complete")
        except CodeXError as error:
            captured = stream.getvalue()
            message = (captured + "\n" if captured else "") + str(error)
            self._set_output(message)
            self._update_status("Run failed")

    def clear_output(self):
        self.output.delete("1.0", tk.END)
        self._update_status("Output cleared")


def main():
    root = tk.Tk()
    app = HinagpisUI(root)
    root.mainloop()
    return app


if __name__ == "__main__":
    main()

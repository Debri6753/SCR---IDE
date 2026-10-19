from tkinter import *
from tkinter import filedialog
from tkinter import scrolledtext
from tkinter import ttk
from tkinter import messagebox
from tkinter import TclError
import os
import re
import webbrowser
import sys
import subprocess
import tempfile
import threading

root = Tk()
menu = Menu(root)
root.config(menu=menu)

root.title("scr")
root.state("zoomed")
root.configure(bg="#0d1117")

try:
    icon = PhotoImage(file="assets/image.png")
    root.iconphoto(True, icon)
except Exception as e:
    print(f"Failed to load icon: {e}")

# ==========================================
# CUSTOM SCROLLBAR
# ==========================================
class CustomScrollbar(Canvas):
    def __init__(self, parent, command, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self.first = 0.0
        self.last = 1.0
        
        self.configure(width=12, bg="#0d1117", bd=0, highlightthickness=0)
        
        self.track = self.create_rectangle(3, 0, 9, self.winfo_height(), fill="#0d1117", outline="")
        self.thumb = self.create_rectangle(3, 0, 9, 100, fill="#30363d", outline="", activefill="#8b949e")
        
        self.bind("<Configure>", self.on_configure)
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Enter>", lambda e: self.itemconfig(self.thumb, fill="#484f58"))
        self.bind("<Leave>", lambda e: self.itemconfig(self.thumb, fill="#30363d"))

    def set(self, first, last):
        self.first = float(first)
        self.last = float(last)
        self.update_thumb()

    def update_thumb(self):
        height = self.winfo_height()
        if height <= 1: return
        
        thumb_start = self.first * height
        thumb_end = self.last * height
        
        if thumb_end - thumb_start < 20:
            thumb_end = thumb_start + 20
            
        self.coords(self.thumb, 3, thumb_start, 9, thumb_end)
        self.coords(self.track, 3, 0, 9, height)

    def on_configure(self, event):
        self.update_thumb()

    def on_click(self, event):
        y = event.y / self.winfo_height()
        self.command("moveto", y - (self.last - self.first) / 2)

    def on_drag(self, event):
        y = event.y / self.winfo_height()
        self.command("moveto", y - (self.last - self.first) / 2)

# ==========================================
# SEARCH IN CODE
# ==========================================
def show_search(event=None):
    search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
    search_entry.focus_set()
    search_entry.select_range(0, END)
    return "break"

def hide_search(event=None):
    search_frame.grid_remove()
    edit_widget.tag_remove("search_highlight", "1.0", END)
    edit_widget.focus_set()
    return "break"

def do_search(forward=True, event=None):
    query = search_entry.get()
    if not query:
        return "break"

    edit_widget.tag_remove("search_highlight", "1.0", END)
    
    start_pos = "1.0"
    count = IntVar()

    while True:
        idx = edit_widget.search(query, start_pos, stopindex=END, nocase=True, count=count)
        if not idx:
            break
        end_idx = f"{idx}+{count.get()}c"
        edit_widget.tag_add("search_highlight", idx, end_idx)
        start_pos = end_idx

    if forward:
        start_idx = edit_widget.index(INSERT)
        idx = edit_widget.search(query, start_idx, stopindex=END, nocase=True, count=count)
        if not idx:
            idx = edit_widget.search(query, "1.0", stopindex=END, nocase=True, count=count) # From start
    else:
        start_idx = edit_widget.index(INSERT)
        idx = edit_widget.search(query, start_idx, stopindex="1.0", backwards=True, nocase=True, count=count)
        if not idx:
            idx = edit_widget.search(query, END, stopindex="1.0", backwards=True, nocase=True, count=count) # From end

    if idx:
        end_idx = f"{idx}+{count.get()}c"
        edit_widget.mark_set(INSERT, end_idx)
        edit_widget.see(idx)
        edit_widget.tag_remove(SEL, "1.0", END)
        edit_widget.tag_add(SEL, idx, end_idx)
    return "break"

# ==========================================
# RUN CODE
# ==========================================
def run_code(event=None):
    console_text.config(state="normal")
    console_text.delete("1.0", END)
    console_text.config(state="disabled")
    
    code = edit_widget.get("1.0", "end-1c")
    if not code.strip():
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    def execute():
        try:
            process = subprocess.Popen(
                [sys.executable, temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8"
            )
            
            for line in process.stdout:
                console_text.config(state="normal")
                console_text.insert(END, line)
                console_text.see(END)
                console_text.config(state="disabled")
            
            process.wait()
            
        except Exception as e:
            console_text.config(state="normal")
            console_text.insert(END, f"Launch error: {e}\n")
            console_text.config(state="disabled")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    threading.Thread(target=execute, daemon=True).start()

def clear_console():
    console_text.config(state="normal")
    console_text.delete("1.0", END)
    console_text.config(state="disabled")

# ==========================================
# MAIN FUNCTIONS
# ==========================================
def telegram():
    webbrowser.open("t.me/FFLHP")

def about():
    messagebox.showinfo("About SCR")

def open_file(event=None):
    file_path = filedialog.askopenfilename(
        title="Open file",
        filetypes=[("Py file", "*.py"), ("All File", "*.*")]
    )

    if file_path:
        edit_widget.delete("1.0", END)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        edit_widget.insert("1.0", content)
        highlight_syntax()
        update_line_numbers()

def save_file():
    file_path = filedialog.asksaveasfilename(
        title="Save File",
        defaultextension=".py",
        filetypes=[("Py file", "*.py"), ("All file", "*.*")]
    )
    
    if file_path:
        content = edit_widget.get("1.0", END)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

def change_menu_bg(color):
    file_menu.config(bg=color)
    run_menu.config(bg=color)
    edit_menu.config(bg=color)
    theme_menu.config(bg=color)
    help_menu.config(bg=color)

def change_menu_fg(color):
    file_menu.config(fg=color)
    run_menu.config(fg=color)
    edit_menu.config(fg=color)
    theme_menu.config(fg=color)
    help_menu.config(fg=color)

def zoom_in(event=None):
    current_size = int(edit_widget['font'].split()[1])
    new_size = current_size + 1
    edit_widget.config(font=("Consolas", new_size))
    line_numbers.config(font=("Consolas", new_size))
    update_line_numbers()

def zoom_out(event=None):
    current_size = int(edit_widget['font'].split()[1])
    if current_size > 8:
        new_size = current_size - 1
        edit_widget.config(font=("Consolas", new_size))
        line_numbers.config(font=("Consolas", new_size))
        update_line_numbers()

def reset_zoom(event=None):
    edit_widget.config(font=("Consolas", 15))
    line_numbers.config(font=("Consolas", 15))
    update_line_numbers()

def highlight_syntax():
    edit_widget.tag_remove("keyword", "1.0", END)
    edit_widget.tag_remove("string", "1.0", END)
    edit_widget.tag_remove("comment", "1.0", END)
    edit_widget.tag_remove("function", "1.0", END)
    edit_widget.tag_remove("number", "1.0", END)
    edit_widget.tag_remove("false", "1.0", END)

    content = edit_widget.get("1.0", "end-1c")
    lines = content.split('\n')
    
    keywords = ['def', 'class', 'import', 'from', 'as', 'if', 'elif', 'else', 'while', 'for', 'in', 'return', 'try', 'except', 'finally', 'with', 'self', 'True','and', 'or', 'is', 'lambda', 'print']
    
    false_patterns=['None', 'False', 'not']

    for i, line in enumerate(lines):
        line_start = f"{i+1}.0"
        
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            for match in re.finditer(pattern, line):
                start = f"{i+1}.{match.start()}"
                end = f"{i+1}.{match.end()}"
                edit_widget.tag_add("keyword", start, end)
        
        for false_pattern in false_patterns:
            pattern = r'\b' + re.escape(false_pattern) + r'\b'
            for match in re.finditer(pattern, line):
                start = f"{i+1}.{match.start()}"
                end = f"{i+1}.{match.end()}"
                edit_widget.tag_add("false", start, end)

        string_pattern = r'(\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|\".*?\"|\'.*?\')'
        for match in re.finditer(string_pattern, line, re.DOTALL):
            start = f"{i+1}.{match.start()}"
            end = f"{i+1}.{match.end()}"
            edit_widget.tag_add("string", start, end)
        
        if '#' in line:
            comment_start = line.find('#')
            start = f"{i+1}.{comment_start}"
            end = f"{i+1}.end"
            edit_widget.tag_add("comment", start, end)
        
        function_pattern = r'\b\w+(?=\()'
        for match in re.finditer(function_pattern, line):
            start = f"{i+1}.{match.start()}"
            end = f"{i+1}.{match.end()}"
            edit_widget.tag_add("function", start, end)
        
        number_pattern = r'\b\d+(\.\d+)?\b'
        for match in re.finditer(number_pattern, line):
            start = f"{i+1}.{match.start()}"
            end = f"{i+1}.{match.end()}"
            edit_widget.tag_add("number", start, end)

def on_text_change(event=None):
    root.after(10, highlight_syntax)
    root.after(20, update_line_numbers)

def update_line_numbers():
    line_numbers.config(state="normal")
    content = edit_widget.get("1.0", "end-1c")
    lines = content.count("\n") + 1 if content else 1
    line_numbers_text = "\n".join(str(i) for i in range(1, lines + 1))
    line_numbers.delete("1.0", END)
    line_numbers.insert("1.0", line_numbers_text)
    line_numbers.config(state="disabled")
    line_numbers.yview_moveto(edit_widget.yview()[0])

def on_editor_yscroll(first, last):
    scrollbar.set(first, last)
    line_numbers.yview_moveto(first)

def on_scroll(*args):
    edit_widget.yview(*args)

def on_mousewheel(event):
    if event.delta:
        scroll_amount = -1 if event.delta > 0 else 1
    else:
        scroll_amount = -1 if event.num == 4 else 1

    edit_widget.yview_scroll(scroll_amount, "units")
    return "break"

BRACKET_PAIRS = {
    "(": ")",
    "[": "]",
    "{": "}",
    '"': '"',
    "'": "'",
}

def auto_pair(event=None):
    char = event.char
    if char not in BRACKET_PAIRS:
        return
    closing = BRACKET_PAIRS[char]

    prev_char = edit_widget.get("insert-1c", "insert")
    next_char = edit_widget.get("insert", "insert+1c")

    if char in ('"', "'"):
        if prev_char.isalnum() or prev_char in ')]}':
            return
        if next_char == char:
            edit_widget.mark_set(INSERT, "insert+1c")
            return "break"

    if next_char and (next_char.isalnum() or next_char in '_'):
        return

    try:
        sel_start = edit_widget.index("sel.first")
        sel_end = edit_widget.index("sel.last")
        selected = edit_widget.get(sel_start, sel_end)
        edit_widget.delete(sel_start, sel_end)
        edit_widget.insert(sel_start, char + selected + closing)
        edit_widget.mark_set(INSERT, f"{sel_start}+{len(char + selected + closing)}c")
        return "break"
    except TclError:
        pass

    edit_widget.insert(INSERT, char + closing)
    edit_widget.mark_set(INSERT, "insert-1c")
    return "break"

def handle_backspace(event=None):
    prev_char = edit_widget.get("insert-1c", "insert")
    next_char = edit_widget.get("insert", "insert+1c")
    if prev_char in BRACKET_PAIRS and BRACKET_PAIRS[prev_char] == next_char:
        edit_widget.delete("insert-1c", "insert+1c")
        return "break"

    line_start = edit_widget.index("insert linestart")
    before = edit_widget.get(line_start, "insert")
    if before and before.strip() == "" and len(before) >= 4 and before.endswith("    "):
        edit_widget.delete("insert-4c", "insert")
        return "break"

    return

def auto_indent(event=None):
    line_start = edit_widget.index("insert linestart")
    line_before_cursor = edit_widget.get(line_start, "insert")

    indent_match = re.match(r'^[ \t]*', line_before_cursor)
    current_indent = indent_match.group(0) if indent_match else ""

    stripped = line_before_cursor.rstrip()

    dedent_keywords = ("elif ", "else:", "except", "finally:")
    is_dedent = any(stripped.lstrip().startswith(kw) for kw in dedent_keywords)

    if stripped.endswith(":") and not is_dedent:
        new_indent = current_indent + "    "
    else:
        new_indent = current_indent

    edit_widget.insert(INSERT, "\n" + new_indent)
    return "break"

# ==========================================
# WIDGETS AND LAYOUT
# ==========================================
menu_frame = Frame(root, bg="Black", width=2000, height=30)
menu_frame.grid(row=0, column=0, sticky="ew")

paned_window = PanedWindow(root, orient=VERTICAL, bg="#0d1117", sashwidth=5, sashrelief=FLAT)
paned_window.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

text_frame = Frame(paned_window, bg="#0d1117")
paned_window.add(text_frame, stretch="always")

line_numbers = Text(text_frame, width=4, padx=5, wrap=NONE, font=("Consolas", 15), 
                    bg="#0d1117", fg="#6e7681", state="disabled", bd=0, 
                    highlightthickness=0, spacing1=0, spacing3=0)
line_numbers.grid(row=0, column=0, sticky="ns")

edit_widget = Text(text_frame, wrap=NONE, font=("Consolas", 15), 
                   bg="#0d1117", fg="White", insertbackground="white", bd=0, 
                   highlightthickness=0, spacing1=0, spacing3=0)
edit_widget.grid(row=0, column=1, sticky="nsew")

scrollbar = CustomScrollbar(text_frame, command=on_scroll)
scrollbar.grid(row=0, column=2, sticky="ns", padx=(5, 0))

edit_widget.config(yscrollcommand=on_editor_yscroll)
line_numbers.config(yscrollcommand=scrollbar.set)

text_frame.grid_columnconfigure(1, weight=1)
text_frame.grid_rowconfigure(0, weight=1)

# --- SEARCH PANEL (HIDDEN BY DEFAULT) ---
search_frame = Frame(text_frame, bg="#161b22", bd=0)

search_entry = Entry(search_frame, bg="#0d1117", fg="white", insertbackground="white", bd=1, relief=FLAT, width=30)
search_entry.pack(side=LEFT, padx=5, pady=5)
search_entry.bind("<Return>", lambda e: do_search(forward=True))
search_entry.bind("<Escape>", hide_search)
search_entry.bind("<KeyRelease>", lambda e: do_search(forward=True))

Button(search_frame, text="Next", command=lambda: do_search(forward=True), bg="#21262d", fg="white", bd=0, padx=10).pack(side=LEFT, padx=2, pady=5)
Button(search_frame, text="Prev", command=lambda: do_search(forward=False), bg="#21262d", fg="white", bd=0, padx=10).pack(side=LEFT, padx=2, pady=5)
Button(search_frame, text="X", command=hide_search, bg="#21262d", fg="white", bd=0, padx=8).pack(side=RIGHT, padx=5, pady=5)


console_frame = Frame(paned_window, bg="#161b22")
paned_window.add(console_frame, height=200, stretch="never")

console_header = Frame(console_frame, bg="#161b22")
console_header.pack(fill=X, side=TOP)

Label(console_header, text="CONSOLE", bg="#161b22", fg="#8b949e", font=("Consolas", 10, "bold")).pack(side=LEFT, padx=5, pady=2)
Button(console_header, text="Clear", command=clear_console, bg="#21262d", fg="white", bd=0, padx=5, pady=2).pack(side=RIGHT, padx=5, pady=2)

console_text = Text(console_frame, wrap=WORD, font=("Consolas", 12), 
                    bg="#0d1117", fg="#e6edf3", bd=0, 
                    highlightthickness=0, state="disabled")
console_text.pack(expand=True, fill=BOTH, padx=5, pady=(0, 5))

edit_widget.tag_configure("keyword", foreground="#569cd6")
edit_widget.tag_configure("string", foreground="#ce9178")
edit_widget.tag_configure("comment", foreground="#6a9955")
edit_widget.tag_configure("function", foreground="#dcdcaa")
edit_widget.tag_configure("number", foreground="#b5cea8")
edit_widget.tag_configure("false", foreground="#8b0000")

# SEARCH HIGHLIGHT TAG
edit_widget.tag_configure("search_highlight", background="#5a4a00", foreground="white")

edit_widget.bind("<KeyRelease>", on_text_change)
edit_widget.bind("<Control-plus>", zoom_in)
edit_widget.bind("<Control-equal>", zoom_in)
edit_widget.bind("<Control-minus>", zoom_out)
edit_widget.bind("<Control-0>", reset_zoom)
edit_widget.bind("<MouseWheel>", on_mousewheel)
edit_widget.bind("<Button-4>", on_mousewheel)
edit_widget.bind("<Button-5>", on_mousewheel)
line_numbers.bind("<MouseWheel>", on_mousewheel)
line_numbers.bind("<Button-4>", on_mousewheel)
line_numbers.bind("<Button-5>", on_mousewheel)

edit_widget.bind("<KeyPress>", auto_pair)
edit_widget.bind("<Return>", auto_indent)
edit_widget.bind("<BackSpace>", handle_backspace)

# ==========================================
# MENU
# ==========================================
file_menu = Menu(menu, tearoff=0, bg="#1e1e1e", fg="white")
run_menu = Menu(menu, tearoff=0, bg="#1e1e1e", fg="white")
edit_menu = Menu(menu, tearoff=0, bg="#1e1e1e", fg="white")
theme_menu = Menu(menu, tearoff=0, bg="#1e1e1e", fg="white")
help_menu = Menu(menu, tearoff=0, bg="#1e1e1e", fg="white")

menu.add_cascade(label="File", menu=file_menu)
menu.add_cascade(label="Run", menu=run_menu)
menu.add_cascade(label="Edit", menu=edit_menu)
menu.add_cascade(label="Theme", menu=theme_menu)
menu.add_cascade(label="Help", menu=help_menu)

file_menu.add_command(label="Open Ctrl+O", command=open_file)
file_menu.add_command(label="Save Ctrl+S", command=save_file)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

run_menu.add_command(label="Run Code F5", command=run_code)
run_menu.add_command(label="Clear Console", command=clear_console)

edit_menu.add_command(label="Find Ctrl+F", command=show_search)
edit_menu.add_separator()
edit_menu.add_command(label="Cut Ctrl+X", command=lambda: root.focus_get().event_generate("<<Cut>>"))
edit_menu.add_command(label="Copy Ctrl+C", command=lambda: root.focus_get().event_generate("<<Copy>>"))
edit_menu.add_command(label="Paste Ctrl+V", command=lambda: root.focus_get().event_generate("<<Paste>>"))
edit_menu.add_separator()
edit_menu.add_command(label="Increase Ctrl++", command=zoom_in)
edit_menu.add_command(label="Decrease Ctrl+-", command=zoom_out)
edit_menu.add_command(label="Reset size Ctrl+0", command=reset_zoom)

theme_menu.add_command(label="Darked menu", command=lambda: change_menu_bg("#1e1e1e"))
theme_menu.add_command(label="Lighted menu", command=lambda: change_menu_bg("#f0f0f0"))
theme_menu.add_command(label="Blue menu", command=lambda: change_menu_bg("#1a237e"))
theme_menu.add_separator()
theme_menu.add_command(label="White text", command=lambda: change_menu_fg("white"))
theme_menu.add_command(label="Black text", command=lambda: change_menu_fg("black"))
theme_menu.add_command(label="Yellow text", command=lambda: change_menu_fg("yellow"))

help_menu.add_command(label="Report Bug")
help_menu.add_command(label="Documentation")
help_menu.add_command(label="Telegram", command=telegram)
help_menu.add_separator()
help_menu.add_command(label="About SCR", command=about)

root.bind('<Control-o>', open_file)
root.bind('<Control-O>', open_file)
root.bind('<Control-s>', lambda e: save_file())
root.bind('<Control-S>', lambda e: save_file())
root.bind('<Control-plus>', zoom_in)
root.bind('<Control-equal>', zoom_in)
root.bind('<Control-minus>', zoom_out)
root.bind('<Control-0>', reset_zoom)
root.bind('<Control-f>', show_search)
root.bind('<F5>', run_code)

root.config(menu=menu)
root.mainloop()

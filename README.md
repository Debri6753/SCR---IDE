# SCR — Simple Python Code Editor

A lightweight, dark-themed Python code editor built entirely with Tkinter. Write, edit, and run Python scripts without leaving the app.

---

## Features

- **Syntax highlighting** — Python keywords, strings, comments, function names, numbers, and boolean literals (`None`, `False`, `not`)
- **Built-in code runner** — press `F5` to execute your script; output streams live into the integrated console
- **Line numbers** — synchronized with editor scrolling
- **Custom scrollbar** — styled to match the dark theme
- **Smart editing**
  - Auto-pairing of brackets and quotes (`()`, `[]`, `{}`, `""`, `''`)
  - Auto-indentation after lines ending with `:`
  - Smart backspace — deletes paired brackets/quotes together, removes 4-space indents
- **Search panel** (`Ctrl+F`) — live highlighting, next/previous navigation
- **Zoom controls** — `Ctrl++` / `Ctrl+-` / `Ctrl+0` to adjust font size
- **File operations** — open and save `.py` files
- **Theme customization** — change menu background and text colors
- **Resizable layout** — vertical paned window separates editor and console

---

## Requirements

- Python 3.x
- Tkinter (included with standard Python installations)

No third-party dependencies required.

---

## Installation & Usage

1. Clone or download the repository.
2. (Optional) Place an `image.png` in the same directory as `scr.py` to use it as the app icon.
3. Run the editor:

```bash
python scr.py

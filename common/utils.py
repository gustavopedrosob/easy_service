import tkinter as tk


def copy_to_clipboard(tk_object: tk.Widget, text: str):
    tk_object.clipboard_clear()
    tk_object.clipboard_append(text)
    tk_object.clipboard_get()


def get_clipboard_content(tk_object: tk.Widget) -> str:
    try:
        content = tk_object.clipboard_get()
    except tk.TclError:
        return ""
    else:
        return content

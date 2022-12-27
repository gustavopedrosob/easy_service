import tkinter as tk
import typing


def copy_to_clipboard(tk_object: typing.Union[tk.Widget, tk.Tk, tk.Toplevel], text: str):
    tk_object.clipboard_clear()
    tk_object.clipboard_append(text)
    tk_object.clipboard_get()


def get_clipboard_content(tk_object: typing.Union[tk.Widget, tk.Tk, tk.Toplevel]) -> str:
    try:
        content = tk_object.clipboard_get()
    except tk.TclError:
        return ""
    else:
        return content

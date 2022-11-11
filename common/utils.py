import tkinter as tk
import typing


def copy_to_clipboard(tk_object: typing.Union[tk.Tk, tk.Toplevel, tk.Widget], text):
    tk_object.clipboard_clear()
    tk_object.clipboard_append(text)
    tk_object.clipboard_get()

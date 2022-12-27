from tkinter import ttk

import tkinter as tk
from common import config


class AboutWindow:
    def __init__(self):
        self.top_level = tk.Toplevel()
        self.top_level.title("Sobre")
        self.top_level.configure(padx=20, pady=30)
        self.top_level.resizable(False, False)
        self.top_level.withdraw()
        self.top_level.protocol("WM_DELETE_WINDOW", self.top_level.withdraw)
        ttk.Label(self.top_level,
                  text=f"Programa desenvolvido por Gustavo Pedroso Bernardes\nVersão: {config.VERSION}").pack()

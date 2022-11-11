import tkinter as tk


class AboutWindow:
    def __init__(self):
        self.top_level = tk.Toplevel()
        self.top_level.title("Sobre")
        self.top_level.configure(padx=20, pady=30)
        self.top_level.resizable(False, False)
        self.top_level.withdraw()
        self.top_level.protocol("WM_DELETE_WINDOW", self.top_level.withdraw)
        tk.Label(self.top_level, text="Programa desenvolvido por Gustavo Pedroso Bernardes\nVersão: 1.0.0").pack()

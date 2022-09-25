from tkinter import Toplevel, Label


class AboutWindow(Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Sobre")
        self.configure(padx=20, pady=30)
        self.resizable(False, False)
        self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        Label(self, text="Programa desenvolvido por Gustavo Pedroso Bernardes\nVersão: 1.0").pack()


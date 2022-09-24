from tkinter import Tk, Button, Label, Text, END, StringVar, IntVar, W
from tkinter.ttk import Treeview
from datetime import datetime, timedelta
from tkinter.ttk import Combobox

from pyperclip import copy
from proposed import Proposed


class RefusalWindow:
    def __init__(self):
        self.window = Tk()
        self.window.title("Facil tabulação!")
        self.window.configure(padx=10, pady=10)
        self.proposed_count = 0
        validate_instalment = self.window.register(self.validate_instalment_entry), "%P"
        validate_times = self.window.register(self.validate_times), "%P"
        self.proposals = Treeview(columns=("first_instalment", "instalments", "else_instalments"), show='headings')
        self.proposals.heading("first_instalment", text="Entrada")
        self.proposals.heading("instalments", text="Parcelas")
        self.proposals.heading("else_instalments", text="Valor das parcelas")
        self.proposals.grid(row=0, column=0, columnspan=3)
        productvariable = StringVar()
        timesvariable = IntVar()
        self.proposed = Proposed(productvariable, timesvariable)
        self.proposed.grid(row=1, column=0)
        self.product = Combobox(values=("Cbrcrel", "Ccrcfi", "Epcfi"), state="readonly", width=10, textvariable=productvariable)
        self.product.grid(row=1, column=1)
        self.add = Button(text="Adicionar", command=self.add_instalment)
        self.add.grid(row=1, column=2, pady=10)
        Label(name="label_refusal_reason", text="Motivo da recusa").grid(row=2, column=0, columnspan=3)
        Text(name="refusal_reason", width=50, height=4).grid(row=3, column=0, columnspan=3)
        Button(name="copy", text="Copiar", command=self.copy).grid(row=4, column=0, pady=10)
        Button(name="reset", text="Redefinir", command=self.reset_fields).grid(row=4, column=2, pady=10)
        self.log = Label()
        self.log.grid(row=5, column=3, columnspan=3, sticky=W)
        self.window.mainloop()

    def set_log_text(self, something):
        self.log.config(text=something)
        self.window.after(5000, lambda: self.log.config(text=""))

    def add_instalment(self):
        first_instalment = self.proposed.first_instalment.get()
        times = self.proposed.times.get()
        else_instament = self.proposed.else_instalment.get()
        if all((first_instalment, times, else_instament)):
            self.proposals.insert("", END, values=(first_instalment, times, else_instament))
            self.proposed.reset()
        elif first_instalment:
            self.proposals.insert("", END, values=(first_instalment,))
            self.proposed.reset()
        else:
            self.set_log_text("Preencha os valores corretamente antes de adicionar uma proposta.")

    def copy(self):
        text = self.window.children["text"].get("1.0", END)
        refusal_reason_text = self.window.children["refusal_reason"].get("1.0", END)
        text = "{}\nMotivo da recusa: {}".format(text, refusal_reason_text)
        copy(text)

    @staticmethod
    def validate_instalment_entry(something):
        try:
            value = float(something)
        except ValueError:
            if something:
                return False
            else:
                return True
        else:
            if value < 0:
                return False
            else:
                return True

    @staticmethod
    def validate_times(something):
        try:
            value = int(something)
        except ValueError:
            if something:
                return False
            else:
                return True
        else:
            if value > 24 or value < 0:
                return False
            else:
                return True

    def reset_fields(self):
        for name in ("first_instalment", "times", "else_instalment"):
            self.window.children[name].delete(0, END)
        for name in ("text", "refusal_reason"):
            self.window.children[name].delete("1.0", END)
        self.proposed_count = 0


if __name__ == '__main__':
    RefusalWindow()

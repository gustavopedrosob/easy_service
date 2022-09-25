import locale
import re
from tkinter import Tk, Label, Entry, Button, W, Menu, Toplevel, END, Spinbox, E, IntVar, Frame, StringVar, LEFT, X
from tkinter.ttk import Combobox
from pyperclip import copy

from brl_string import BRLString
from cpf_string import CPFString
from proposed import Proposed, validate_max_and_min_value_for_integer_string


class ExceptionProposalWindow:
    def __init__(self):
        self.window = Tk()
        self.about_window = Toplevel()
        self.about_window.title("Sobre")
        self.about_window.configure(padx=20, pady=30)
        self.about_window.resizable(False, False)
        self.about_window.withdraw()
        self.about_window.protocol("WM_DELETE_WINDOW", self.about_window.withdraw)
        self.timesvariable = IntVar(value=1)
        product = StringVar(value="Cbrcrel")
        Label(self.about_window, text="Programa desenvolvido por Gustavo Pedroso Bernardes\nVersão: 1.0").pack()
        self.window.title("Proposta de exceção")
        self.window.resizable(False, False)
        menu = Menu(self.window)
        menu.add_command(label="Sobre", command=self.about_window.deiconify)
        self.window.configure(pady=10, padx=10, menu=menu)
        validate_cpf = self.window.register(lambda string: CPFString(string).is_valid_for_input()), "%P"
        validate_delayed_days = self.window.register(self.validate_delayed_days), "%P"
        validate_phone_number = self.window.register(self.validate_phone_number), "%P"
        validate_instalment = self.window.register(lambda string: BRLString(string).is_valid_for_input()), "%P"
        validate_proposed_payment_date = self.window.register(self.validate_proposed_payment_date), "%P"
        validate_email = self.window.register(self.validate_email), "%P"
        Label(name="cpf_label", text="CPF").grid(row=0, column=0, sticky=W, pady=5, columnspan=2)
        self.cpf = Entry(validate="key", validatecommand=validate_cpf)
        self.cpf.grid(row=0, column=2, columnspan=2, sticky=E)
        Label(name="product_label", text="Produto").grid(row=1, column=0, sticky=W, pady=5, columnspan=2)
        self.product = Combobox(values=("Cbrcrel", "Ccrcfi", "Epcfi"), state="readonly", width=10, textvariable=product)
        self.product.grid(row=1, column=2, columnspan=2, sticky=E)
        Label(name="updated_value_label", text="Valor atualizado").grid(row=2, column=0, sticky=W, pady=5, columnspan=2)
        self.updated_value = Entry(validate="key", validatecommand=validate_instalment, width=10)
        self.updated_value.grid(row=2, column=2, columnspan=2, sticky=E)
        Label(name="promotion_value_label", text="Valor com desconto").grid(row=3, column=0, sticky=W, pady=5)
        self.promotion = Proposed(product, self.timesvariable)
        self.promotion.grid(row=3, column=1, columnspan=3, sticky=E)
        Label(name="delayed_days_label", text="Dias em atraso").grid(row=4, column=0, sticky=W, pady=5, columnspan=2)
        self.delayed_days = Spinbox(validate="key", validatecommand=validate_delayed_days, width=5, from_=1, to=999)
        self.delayed_days.grid(row=4, column=2, columnspan=2, sticky=E)
        Label(name="proposed_payment_date_label", text="Data proposta para pagamento").grid(row=5, column=0, sticky=W,
                                                                                            pady=5, columnspan=2)
        self.proposed_payment_date = Spinbox(validate="key", validatecommand=validate_proposed_payment_date, width=5,
                                             from_=1, to=5)
        self.proposed_payment_date.grid(row=5, column=2, columnspan=2, sticky=E)
        Label(name="proposed_payment_value_label", text="Valor proposto para pagamento").grid(row=6, column=0, sticky=W,
                                                                                              pady=5)
        self.proposed_payment = Proposed(product, self.timesvariable)
        self.proposed_payment.grid(row=6, column=1, columnspan=3, sticky=E)
        Label(name="phone_number_label", text="Telefone").grid(row=7, column=0, sticky=W, pady=5, columnspan=2)
        self.phone_number = Entry(validate="key", validatecommand=validate_phone_number)
        self.phone_number.grid(row=7, column=2, columnspan=2, sticky=E)
        Label(name="email_address_label", text="E-mail").grid(row=8, column=0, sticky=W, pady=5)
        self.email_address = Entry(name="", validate="key", validatecommand=validate_email, width=35)
        self.email_address.grid(row=8, column=1, columnspan=3, sticky=E)
        frame = Frame()
        frame.grid(row=9, column=0, columnspan=4, sticky="nsew")
        Button(master=frame, name="copy", text="Copiar", command=self.copy).pack(side=LEFT, fill=X, expand=1, padx=40)
        Button(master=frame, name="reset", text="Redefinir", command=self.reset).pack(side=LEFT, fill=X, expand=1, padx=40)
        self.log = Label()
        self.log.grid(row=10, column=0, columnspan=4, sticky=W)
        self.apply_default_values()
        self.window.mainloop()

    def set_log(self, something: str):
        self.log.config(text=something)
        self.window.after(5000, lambda: self.log.config(text=""))

    def apply_default_values(self):
        self.product.current(0)

    @staticmethod
    def validate_proposed_payment_date(something: str):
        return validate_max_and_min_value_for_integer_string(something, 6, 0)

    @staticmethod
    def validate_delayed_days(something: str):
        return validate_max_and_min_value_for_integer_string(something, 999, 0)

    @staticmethod
    def validate_phone_number(something: str):
        matched = re.match(r"(?:\(\d{2,3}\)|\d{2,3}) +\d{4,5}-?\d{4}", something)
        if matched or len(something) == 0:
            return True
        else:
            return False

    @staticmethod
    def validate_email(something: str):
        matched = re.match(r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+", something)
        if matched or len(something) == 0:
            return True
        else:
            return False

    def copy(self):
        if not (cpf := self.cpf.get()):
            self.set_log("Lembre-se de preencher o campo de CPF.")
        elif not (updated_value := self.updated_value.get()):
            self.set_log("Lembre-se de preencher o campo de valor atualizado.")
        elif self.promotion.is_empty():
            self.set_log("Lembre-se de preencher o campo de valor com desconto.")
        elif not (delayed_days := self.delayed_days.get()):
            self.set_log("Lembre-se de preencher os dias em atraso.")
        elif not (proposed_payment_date := self.proposed_payment_date.get()):
            self.set_log("Lembre-se de preencher o campo de data proposta para pagamento.")
        elif self.proposed_payment.is_empty():
            self.set_log("Lembre-se de preencher o campo de valor proposto para pagamento.")
        elif not (phone_number := self.phone_number.get()):
            self.set_log("Lembre-se de preencher o campo de telefone.")
        elif not (email_address := self.email_address.get()):
            self.set_log("Lembre-se de preencher o campo de e-mail.")
        else:
            lines = (
                f'CPF: {CPFString(cpf).get_formated()}',
                f'Produto: {self.product.get()}',
                f'Valor atualizado: {BRLString(updated_value).get_formated()}',
                f'Valor com desconto: {self.promotion.get_instalment_formated()}',
                f'Dias em atraso: {delayed_days}',
                f'Data proposta para pagamento: D+{proposed_payment_date}',
                f'Proposta para pagamento: {"À vista" if self.timesvariable.get() == 1 else "Parcelamento"}',
                f'Valor proposto para pagamento: {self.proposed_payment.get_instalment_formated()}',
                f'Telefone: {phone_number}',
                f'E-mail: {email_address}'
            )
            copy("\n".join(lines))

    def reset(self):
        for object_ in (self.cpf, self.updated_value, self.phone_number, self.email_address):
            object_.delete(0, END)
        self.promotion.reset()
        self.proposed_payment.reset()
        self.timesvariable.set(1)
        self.apply_default_values()
        for object_ in (self.delayed_days, self.proposed_payment_date):
            object_.delete(0, END)
            object_.insert(0, "1")


if __name__ == '__main__':
    ExceptionProposalWindow()

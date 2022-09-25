import locale
import re
from datetime import datetime, timedelta
from tkinter import Tk, Label, Entry, Button, W, Menu, Toplevel, END, Spinbox, E, IntVar, Frame, StringVar, LEFT, X
from tkinter.ttk import Combobox
from pyperclip import copy

from DplusX import DplusX
from about_window import AboutWindow
from brl_string import BRLString
from cpf_string import CPFString
from email_string import EmailString
from phone_str import PhoneString
from proposed import Proposed, validate_max_and_min_value_for_integer_string


class ExceptionProposalWindow:
    def __init__(self):
        self.window = Tk()
        self.timesvariable = IntVar(value=1)
        product = StringVar(value="Cbrcrel")
        self.datevariable = IntVar(value=1)
        self.datevariable.trace("w", self.on_date_change)
        self.window.title("Proposta de exceção")
        self.window.resizable(False, False)
        self.about_window = AboutWindow()
        menu = Menu(self.window)
        menu.add_command(label="Sobre", command=self.about_window.deiconify)
        self.window.configure(menu=menu)
        validate_cpf = self.window.register(lambda string: CPFString(string).is_valid_for_input()), "%P"
        validate_delayed_days = self.window.register(self.validate_delayed_days), "%P"
        validate_phone_number = self.window.register(lambda string: PhoneString(string).is_valid_for_input()), "%P"
        validate_instalment = self.window.register(lambda string: BRLString(string).is_valid_for_input()), "%P"
        validate_proposed_payment_date = self.window.register(self.validate_proposed_payment_date), "%P"
        validate_email = self.window.register(lambda string: EmailString(string).is_valid_for_input()), "%P"
        frame_1 = Frame()
        frame_1.pack(padx=20, pady=20)
        Label(master=frame_1, name="cpf_label", text="CPF").grid(row=0, column=0, sticky=W, pady=5, columnspan=2)
        self.cpf = Entry(master=frame_1, validate="key", validatecommand=validate_cpf)
        self.cpf.grid(row=0, column=2, columnspan=2, sticky=E)
        Label(master=frame_1, name="product_label", text="Produto").grid(row=1, column=0, sticky=W, pady=5, columnspan=2)
        self.product = Combobox(master=frame_1, values=("Cbrcrel", "Ccrcfi", "Epcfi"), state="readonly", width=10, textvariable=product)
        self.product.grid(row=1, column=2, columnspan=2, sticky=E)
        Label(master=frame_1, name="updated_value_label", text="Valor atualizado").grid(row=2, column=0, sticky=W, pady=5, columnspan=2)
        self.updated_value = Entry(master=frame_1, validate="key", validatecommand=validate_instalment, width=10)
        self.updated_value.grid(row=2, column=2, columnspan=2, sticky=E)
        Label(master=frame_1, name="promotion_value_label", text="Valor com desconto").grid(row=3, column=0, sticky=W, pady=5)
        self.promotion = Proposed(product, self.timesvariable, master=frame_1)
        self.promotion.grid(row=3, column=1, columnspan=3, sticky=E)
        Label(master=frame_1, name="delayed_days_label", text="Dias em atraso").grid(row=4, column=0, sticky=W, pady=5, columnspan=2)
        self.delayed_days = Spinbox(master=frame_1, validate="key", validatecommand=validate_delayed_days, width=5, from_=1, to=999)
        self.delayed_days.grid(row=4, column=2, columnspan=2, sticky=E)
        Label(master=frame_1, name="proposed_payment_date_label", text="Data proposta para pagamento").grid(row=5, column=0, sticky=W,
                                                                                            pady=5, columnspan=2)
        self.date = Label(master=frame_1)
        self.date.grid(row=5, column=2, sticky=E)
        self.proposed_payment_date = Spinbox(master=frame_1, validate="key", validatecommand=validate_proposed_payment_date, width=5,
                                             from_=1, to=5, textvariable=self.datevariable)
        self.proposed_payment_date.grid(row=5, column=3, sticky=E)
        Label(master=frame_1, name="proposed_payment_value_label", text="Valor proposto para pagamento").grid(row=6, column=0, sticky=W,
                                                                                              pady=5)
        self.proposed_payment = Proposed(product, self.timesvariable, master=frame_1)
        self.proposed_payment.grid(row=6, column=1, columnspan=3, sticky=E)
        Label(master=frame_1, name="phone_number_label", text="Telefone").grid(row=7, column=0, sticky=W, pady=5, columnspan=2)
        self.phone_number = Entry(master=frame_1, validate="key", validatecommand=validate_phone_number)
        self.phone_number.grid(row=7, column=2, columnspan=2, sticky=E)
        Label(master=frame_1, name="email_address_label", text="E-mail").grid(row=8, column=0, sticky=W, pady=5)
        self.email_address = Entry(master=frame_1, name="", validate="key", validatecommand=validate_email, width=35)
        self.email_address.grid(row=8, column=1, columnspan=3, sticky=E)
        frame_2 = Frame()
        frame_2.pack()
        Button(master=frame_2, name="copy", text="Copiar", command=self.copy).pack(side=LEFT, fill=X, expand=1, padx=40)
        Button(master=frame_2, name="reset", text="Redefinir", command=self.reset).pack(side=LEFT, fill=X, expand=1, padx=40)
        self.log = Label()
        self.log.pack(side=LEFT)
        self.apply_default_values()
        self.window.mainloop()

    def set_log(self, something: str):
        self.log.config(text=something)
        self.window.after(5000, lambda: self.log.config(text=""))

    def apply_default_values(self):
        self.product.current(0)

    def on_date_change(self, *args):
        self.date.config(text=DplusX(self.datevariable.get()).get_date_formated())

    @staticmethod
    def validate_proposed_payment_date(something: str):
        return validate_max_and_min_value_for_integer_string(something, 6, 0)

    @staticmethod
    def validate_delayed_days(something: str):
        return validate_max_and_min_value_for_integer_string(something, 999, 0)

    def copy(self):
        if not (cpf := self.cpf.get()):
            self.set_log("Lembre-se de preencher o campo de CPF.")
        elif not CPFString(cpf).is_valid():
            self.set_log("Digite um CPF valido.")
        elif not (updated_value := self.updated_value.get()):
            self.set_log("Lembre-se de preencher o campo de valor atualizado.")
        elif not BRLString(updated_value).is_valid():
            self.set_log("Digite um valor atualizado valido.")
        elif self.promotion.is_empty():
            self.set_log("Lembre-se de preencher o campo de valor com desconto.")
        elif not self.promotion.is_valid():
            self.set_log("Digite um valor com desconto valido.")
        elif not (delayed_days := self.delayed_days.get()):
            self.set_log("Lembre-se de preencher os dias em atraso.")
        elif not (datevariable := self.datevariable.get()):
            self.set_log("Lembre-se de preencher o campo de data proposta para pagamento.")
        elif not self.proposed_payment.is_valid():
            self.set_log("Digite um valor proposto para pagamento valido.")
        elif self.proposed_payment.is_empty():
            self.set_log("Lembre-se de preencher o campo de valor proposto para pagamento.")
        elif not (phone_number := self.phone_number.get()):
            self.set_log("Lembre-se de preencher o campo de telefone.")
        elif not PhoneString(phone_number).is_valid():
            self.set_log("Digite um telefone valido.")
        elif not (email_address := self.email_address.get()):
            self.set_log("Lembre-se de preencher o campo de e-mail.")
        elif not EmailString(email_address).is_valid():
            self.set_log("Digite um e-mail valido.")
        else:
            lines = (
                f'CPF: {CPFString(cpf).get_formated()}',
                f'Produto: {self.product.get()}',
                f'Valor atualizado: {BRLString(updated_value).get_formated()}',
                f'Valor com desconto: {self.promotion.get_instalment_formated()}',
                f'Dias em atraso: {delayed_days}',
                f'Data proposta para pagamento: {DplusX(datevariable).get_date_formated()}',
                f'Proposta para pagamento: {"À vista" if self.timesvariable.get() == 1 else "Parcelamento"}',
                f'Valor proposto para pagamento: {self.proposed_payment.get_instalment_formated()}',
                f'Telefone: {PhoneString(phone_number).get_formated()}',
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

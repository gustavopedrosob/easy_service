import re
from datetime import datetime, timedelta
from sqlite3 import connect, PARSE_DECLTYPES
from tkinter import StringVar
from typing import Optional

from common.constants import CBRCREL, IN_CASH, INSTALLMENT
from common.tk_util import StrVar, IntStr, BRLVar
from json import load, dump


class Config:
    def __init__(self, **kwargs):
        self.save_on_copy = kwargs["save_on_copy"]

    @staticmethod
    def load():
        try:
            file = open("config.json", "r")
        except FileNotFoundError:
            file = open("config.json", "w+")
            config = Config(save_on_copy=True)
            dump(config.__dict__, file)
            file.close()
            return config
        else:
            content = load(file)
            file.close()
            return Config(**content)

    def save(self):
        with open("config.json", "w") as file:
            dump(self.__dict__, file)


class NoKind(Exception):
    pass


class Email(StrVar):
    def is_valid_for_input(self) -> bool:
        return self.is_text_valid_for_input(self.get())

    @staticmethod
    def is_text_valid_for_input(text: str):
        if text:
            compiled = re.compile(r"^[A-Za-z0-9.\-_]+(@[A-Za-z0-9]*)?(\.[A-Za-z]*)*$")
            return bool(compiled.match(text))
        else:
            return True

    def is_valid(self) -> bool:
        compiled = re.compile(r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+$")
        return bool(compiled.match(self.get()))

    def validate(self):
        if not self.is_valid():
            raise ValueError("Entrada para e-mail inválida.")


class UpdatedValue(BRLVar):
    def validate(self):
        if not self.is_valid():
            raise ValueError("Entrada para valor atualizado inválida.")


class Product(StrVar):
    def get_max_instalments(self):
        if self.get() == CBRCREL:
            return 23
        else:
            return 17

    def validate(self):
        if self.is_empty():
            raise ValueError("Entrada para produto não preenchida.")


class Instalments(IntStr):
    def is_valid(self, max_: Optional[int] = 24, min_: Optional[int] = 0, product: Optional[Product] = None):
        if product:
            return super().is_valid(product.get_max_instalments(), min_)
        else:
            return super().is_valid(max_, min_)

    def get_kind(self):
        if self.get() == 0 or self.is_empty():
            return IN_CASH
        else:
            return INSTALLMENT

    def validate(self):
        if not self.is_valid():
            raise ValueError("Entrada para quantidade de parcelas inválida.")

    def copy(self):
        return Instalments(value=self.get())


class Proposed:
    def __init__(self, first_instalment: BRLVar, instalments: Instalments, else_instalment: BRLVar):
        self.first_instalment = first_instalment
        self.instalments = instalments
        self.else_instalment = else_instalment

    def get_formatted(self, date: Optional[datetime] = None) -> str:
        if self.get_kind() == INSTALLMENT:
            text = "{} + {}x {}".format(self.first_instalment.get_formatted(), self.instalments.get(),
                                        self.else_instalment.get_formatted())
        else:
            text = self.first_instalment.get_formatted()
        if date:
            return f"{text} até {date.strftime('%d/%m')};"
        else:
            return text

    def is_valid(self, product: Optional[StringVar] = None) -> bool:
        try:
            kind = self.get_kind()
        except NoKind:
            return False
        else:
            if kind == INSTALLMENT:
                return self.first_instalment.is_valid() and self.instalments.is_valid(product=product) and \
                       self.else_instalment.is_valid()
            else:
                return self.first_instalment.is_valid()

    def is_empty(self):
        return self.first_instalment.is_empty() and self.instalments.is_empty() and self.else_instalment.is_empty()

    def reset(self):
        self.first_instalment.reset()
        self.instalments.reset()
        self.else_instalment.reset()

    def get_values_formatted(self):
        if self.first_instalment.get() and self.instalments.get() and self.else_instalment.get():
            return self.first_instalment.get_formatted(), self.instalments.get(), self.else_instalment.get_formatted()
        elif self.first_instalment.get():
            return self.first_instalment.get_formatted(),
        else:
            raise NoKind("Proposta sem tipo!")

    def get_kind(self):
        if self.first_instalment.get() and self.instalments.get() and self.else_instalment.get():
            return INSTALLMENT
        elif self.first_instalment.get():
            return IN_CASH
        else:
            raise NoKind("Proposta sem tipo!")

    def copy(self):
        return Proposed(self.first_instalment.copy(), self.instalments.copy(), self.else_instalment.copy())

    def update(self, proposed):
        self.first_instalment.set(proposed.first_instalment.get())
        self.instalments.set(proposed.instalments.get())
        self.else_instalment.set(proposed.else_instalment.get())

    def validate(self, product: Optional[StringVar] = None):
        if self.is_empty():
            raise ValueError("Entrada para valor proposto não preenchido.")
        if not self.is_valid(product):
            raise ValueError("Entrada para valor proposto inválida.")


class Promotion(Proposed):
    def validate(self, product: Optional[StringVar] = None):
        if self.is_empty():
            raise ValueError("Entrada para proposta com desconto não preenchida.")
        if not self.is_valid(product):
            raise ValueError("Entrada para proposta com desconto inválida.")


class Delayed(IntStr):
    def validate(self):
        if self.is_empty():
            raise ValueError("Entrada para dias em atraso não preenchida.")


class ExceptionProposal:
    def __init__(self, master):
        self.cpf = CPF(master)
        self.d_plus = DPlus(master)
        self.updated_value = UpdatedValue(master)
        self.instalments = Instalments(master)
        self.promotion = Promotion(BRLVar(master), self.instalments, BRLVar(master))
        self.proposed = Proposed(BRLVar(master), self.instalments, BRLVar(master))
        self.email = Email(master)
        self.delayed = Delayed(master)
        self.product = Product(master)
        self.phone = Phone(master)

    def get_text_to_copy(self):
        lines = (
            f'CPF: {self.cpf.get_formatted()}',
            f'Produto: {self.product.get()}',
            f'Valor atualizado: {self.updated_value.get_formatted()}',
            f'Valor com desconto: {self.promotion.get_formatted()}',
            f'Dias em atraso: {self.delayed.get()}',
            f'Data proposta para pagamento: {self.d_plus.get_date_formatted()}',
            f'Proposta para pagamento: {self.instalments.get_kind()}',
            f'Valor proposto para pagamento: {self.proposed.get_formatted()}',
            f'Telefone: {self.phone.get_formatted()}',
            f'E-mail: {self.email.get()}'
        )
        return "\n".join(lines)

    def get_vars(self):
        return (self.cpf, self.d_plus, self.updated_value, self.instalments, self.promotion, self.proposed, self.email,
                self.delayed, self.product, self.phone)

    def validate(self):
        for object_ in self.get_vars():
            object_.validate()

    def reset(self):
        for object_ in self.get_vars():
            object_.reset()


class DPlus(IntStr):
    def get_date_formatted(self) -> str:
        return self.get_date().strftime("%d/%m/%Y")

    def get_date(self) -> datetime:
        return datetime.now() + timedelta(days=int(self.get()))

    def validate(self):
        if self.is_empty():
            raise ValueError("Entrada para data proposta para pagamento não preenchida.")


class CPF(StrVar):
    def is_valid(self) -> bool:
        compiled = re.compile(r"^(\d)(?!\1{10}|\1{2}\.\1{3}\.\1{3}-\1{2})(\d{10}|\d{2}\.\d{3}\.\d{3}-\d{2})$")
        return bool(compiled.match(self.get()))

    def is_valid_for_input(self) -> bool:
        return self.is_text_valid_for_input(self.get())

    @staticmethod
    def is_text_valid_for_input(text: str):
        compiled = re.compile(
            r"^(\d{0,11}|\d{0,3}((?<=\d{3})\.\d{0,3}((?<=\d{3}\.\d{3})\.\d{0,3}((?<=\d{3}\.\d{3}.\d{3})-\d{0,2})?)?)?)$"
        )
        return bool(compiled.match(text))

    def get_formatted(self, pretty: bool = True):
        return self.get_text_formatted(self.get(), pretty)

    @staticmethod
    def get_text_formatted(text: str, pretty: bool = True) -> str:
        compiled = re.compile(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})")
        if pretty:
            return compiled.sub(r"\1.\2.\3-\4", text)
        else:
            return compiled.sub(r"\1\2\3\4", text)

    def validate(self):
        if not self.is_valid():
            raise ValueError("Entrada para CPF inválida.")


class Phone(StrVar):
    def is_valid_for_input(self) -> str:
        return self.is_text_valid_for_input(self.get())

    @staticmethod
    def is_text_valid_for_input(text: str):
        if text:
            compiled = re.compile(r"^\(?([14689][1-9]?|2[12478]?|3[1234578]?|5[1345]?|7[13457]?)?"
                                  r"((?<=\(\d{2}))?\)?\s{0,2}9?\s?\d{0,4}[\s-]?\d{0,4}$")
            return bool(compiled.match(text))
        else:
            return True

    def is_valid(self) -> str:
        compiled = re.compile(
            r"^\(?([14689][1-9]|2[12478]|3[1234578]|5[1345]|7[13457])((?<=\(\d{2}))?\)?\s{0,2}9?\s?\d{4}[\s-]?\d{4}$")
        return bool(compiled.match(self.get()))

    def get_formatted(self) -> str:
        compiled = re.compile(r"^\(?(\d{2})\)?\s{0,2}(9?)\s?(\d{4})[\s-]?(\d{4})$")
        return compiled.sub(r"(\1) \2\3-\4", self.get())

    def validate(self):
        if not self.is_valid():
            raise ValueError("Entrada para telefone inválida.")


class Historic:
    def __init__(self):
        self.sqlite_connection = connect("historic.db", detect_types=PARSE_DECLTYPES)
        self.cursor = self.sqlite_connection.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS historic (
        cpf char(11) PRIMARY KEY,
        date timestamp NOT NULL)""")
        self.sqlite_connection.commit()

    def add_exception_proposal(self, proposal: ExceptionProposal, date: datetime):
        self.cursor.execute("INSERT INTO historic (cpf, date) VALUES (?, ?)", (proposal.cpf.get_formatted(False), date))
        self.sqlite_connection.commit()

    def get_historic(self):
        self.cursor.execute("SELECT * FROM historic;")
        return self.cursor.fetchall()

    def delete_old_historic(self):
        self.cursor.execute("SELECT * FROM historic;")
        for cpf, date in self.cursor.fetchall():
            timedelta_ = datetime.now() - date
            if timedelta_ > timedelta(days=31):
                self.cursor.execute("DELETE FROM historic WHERE cpf=?", (cpf,))
        self.sqlite_connection.commit()

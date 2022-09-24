import locale
from tkinter import Frame, Entry, Spinbox, END, E
import re


def validate_max_and_min_value_for_integer_string(something: str, max_: int, min_: int):
    if something.isdigit():
        if max_ > int(something) > min_:
            return True
        else:
            return False
    elif something:
        return False
    else:
        return True


def validate_instalment(something: str):
    match = re.match(r"^\d{0,3}(?:\.(?<=\.)\d{0,3})?(?:,(?<=,)\d{0,2})?$", something)
    if match or not something:
        return True
    else:
        return False


def brl_to_float(something: str):
    return float(something.replace(".", "").replace(",", "."))


class Proposed(Frame):
    def __init__(self, productvariable, timesvariable, **kwargs):
        super().__init__(**kwargs)
        validate_times = self.register(self.validate_times), "%P"
        validate_instalment_ = self.register(validate_instalment), "%P"
        self.productvariable = productvariable
        self.timesvariable = timesvariable
        productvariable.trace("w", lambda *args: self.on_product_variable_change())
        self.first_instalment = Entry(self, width=10, validate="key", validatecommand=validate_instalment_)
        self.first_instalment.grid(row=0, column=0, sticky=E)
        self.times = Spinbox(self, width=5, validate="key", validatecommand=validate_times, textvariable=timesvariable)
        self.times.grid(row=0, column=1, sticky=E)
        self.else_instalment = Entry(self, width=10, validate="key", validatecommand=validate_instalment_)
        self.else_instalment.grid(row=0, column=2, sticky=E)

    def on_product_variable_change(self):
        if self.productvariable.get() == "Cbrcrel":
            self.times.config(from_=1, to=24)
        else:
            self.times.config(from_=1, to=18)

    def validate_times(self, something: str):
        if self.productvariable.get() == "Cbrcrel":
            return validate_max_and_min_value_for_integer_string(something, 25, 0)
        else:
            return validate_max_and_min_value_for_integer_string(something, 19, 0)

    def get_instalment_formated(self):
        if all((self.first_instalment.get(), self.times.get(), self.else_instalment.get())):
            return "{} + {}x {}".format(self.get_currency_of_entry(self.first_instalment), self.timesvariable.get(),
                                        self.get_currency_of_entry(self.else_instalment))
        else:
            return "{}".format(self.get_currency_of_entry(self.first_instalment))

    @staticmethod
    def get_currency_of_entry(object_):
        return locale.currency(brl_to_float(object_.get()), grouping=True)

    def is_empty(self):
        if all((self.first_instalment.get(), self.times.get(),
                self.else_instalment.get())) or self.first_instalment.get():
            return False
        else:
            return True

    def reset(self):
        self.first_instalment.delete(0, END)
        self.else_instalment.delete(0, END)

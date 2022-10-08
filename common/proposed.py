from functools import partial
from tkinter import Frame, Spinbox, E, Label, W

from common.tk_util import Entry, Spinbox, IntStr, BRLVar
from exception_proposal import Proposed, Product


class ProposedFrame(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_instalment = Entry(
            self,
            width=10)
        self.instalments = Spinbox(
            self,
            width=5,
            from_=1,
            to=23
        )
        self.else_instalment = Entry(
            self,
            width=10)
        validate_times = self.first_instalment.register(lambda string: IntStr.is_text_valid(string, 23, 0)), "%P"
        validate_instalment = self.first_instalment.register(BRLVar.is_text_valid_for_input), "%P"
        self.instalments.config(validate="key", validatecommand=validate_times)
        self.first_instalment.config(validate="key", validatecommand=validate_instalment)
        self.else_instalment.config(validate="key", validatecommand=validate_instalment)

    def connect_variables(self, proposed: Proposed):
        self.first_instalment.config(textvariable=proposed.first_instalment)
        self.instalments.config(textvariable=proposed.instalments)
        self.else_instalment.config(textvariable=proposed.else_instalment)

    def update_validate(self, product: Product):
        function_ = partial(IntStr.is_text_valid, max_=product.get_max_instalments(), min_=0)
        validate_times = self.first_instalment.register(function_), "%P"
        self.instalments.config(validatecommand=validate_times)


class ProposedLine(ProposedFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_instalment.grid(
            row=0,
            column=0,
            sticky=E
        )
        self.instalments.grid(
            row=0,
            column=1,
            sticky=E
        )
        self.else_instalment.grid(
            row=0,
            column=2,
            sticky=E
        )


class ProposedBox(ProposedFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config(pady=20, padx=20)
        Label(
            self,
            text="Entrada"
        ).grid(
            row=0,
            column=0,
            pady=10,
            sticky=W
        )
        self.first_instalment.grid(
            row=0,
            column=2,
            sticky=E
        )
        Label(
            self,
            text="Quantidade de parcelas"
        ).grid(
            row=1,
            column=0,
            pady=10,
            sticky=W
        )
        self.instalments.grid(
            row=1,
            column=2,
            sticky=E
        )
        Label(
            self,
            text="Valor das outras parcelas"
        ).grid(
            row=2,
            column=0,
            pady=10,
            sticky=W
        )
        self.else_instalment.grid(
            row=2,
            column=2,
            sticky=E
        )

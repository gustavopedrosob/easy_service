from datetime import datetime
from sqlite3 import IntegrityError
from tkinter import Tk, Label, Button, W, Menu, E, Frame, LEFT, X, Toplevel, END, BooleanVar
from tkinter.ttk import Combobox

from pyperclip import copy

from common.constants import PRODUCTS
from common.about_window import AboutWindow
from exception_proposal import Email, ExceptionProposal, CPF, Phone, Historic, Config
from common.tk_util import IntStr, BRLVar, Spinbox, Entry, Treeview
from common.proposed import ProposedLine


class HistoricTreeView(Treeview):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            columns=("cpf", "date"),
            show="headings",
            selectmode="browse",
            **kwargs
        )
        self.column(
            "cpf",
            width=150
        )
        self.column(
            "date",
            width=150
        )
        self.heading(
            "cpf",
            text="CPF"
        )
        self.heading(
            "date",
            text="Data"
        )
        self.popup.add_command(label="Copiar", command=self.on_copy)

    def on_copy(self):
        selected = self.selection()
        item = self.item(selected)
        cpf = CPF.get_text_formatted(item["values"][0], False)
        return copy(cpf)

    def add_exception_proposal_by(self, cpf: str, date: str):
        self.insert('', END, values=[cpf, date])

    def add_exception_proposal(self, proposal: ExceptionProposal, date: datetime):
        self.insert('', END, values=[proposal.cpf.get_formatted(), date.strftime("%d/%m")])

    def insert_saved_historic(self, historic: Historic):
        _historic = historic.get_historic()
        for cpf, date in _historic:
            self.add_exception_proposal_by(CPF.get_text_formatted(cpf), date.strftime("%d/%m"))


class HistoricWindow(Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.withdraw()
        self.title("Histórico")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.historic = HistoricTreeView(self)
        self.historic.pack(padx=10, pady=10)


class ExceptionProposalApp:
    def __init__(self):
        self.config = Config.load()
        self.historic = Historic()
        self.window = ExceptionProposalWindow()
        self.save_on_copy = BooleanVar()
        self.exception_proposal = ExceptionProposal(self.window)
        self.about_window = AboutWindow()
        self.historic_window = HistoricWindow()
        self.setup_window()
        self.setup_historic_window()
        self.window.mainloop()

    def setup_window(self):
        self.window.protocol("WM_DELETE_WINDOW", self.on_close_main_window)
        self.save_on_copy.set(self.config.save_on_copy)
        self.window.menu.add_command(label="Sobre", command=self.about_window.deiconify)
        historic_menu = Menu(tearoff=False)
        historic_menu.add_command(label="Mostrar", command=self.historic_window.deiconify)
        historic_menu.add_command(label="Salvar", command=self.on_save)
        historic_menu.add_checkbutton(
            label="Salvar ao copiar",
            onvalue=True,
            offvalue=False,
            variable=self.save_on_copy
        )
        self.window.menu.add_cascade(label="Histórico", menu=historic_menu)
        self.window.save.config(command=self.on_save)
        self.window.copy.config(command=self.on_copy)
        self.window.reset.config(command=self.on_reset)
        self.window.cpf.config(textvariable=self.exception_proposal.cpf)
        self.window.d_plus.config(textvariable=self.exception_proposal.d_plus)
        self.window.updated_value.config(textvariable=self.exception_proposal.updated_value)
        self.window.promotion.connect_variables(self.exception_proposal.promotion)
        self.window.proposed.connect_variables(self.exception_proposal.proposed)
        self.window.email.config(textvariable=self.exception_proposal.email)
        self.window.delayed.config(textvariable=self.exception_proposal.delayed)
        self.window.product.config(textvariable=self.exception_proposal.product)
        self.window.phone.config(textvariable=self.exception_proposal.phone)
        self.exception_proposal.d_plus.trace("w", lambda *args: self.on_date_change())
        self.exception_proposal.product.trace("w", lambda *args: self.on_product_change())

    def on_close_main_window(self):
        self.save_config()
        self.window.destroy()

    def save_config(self):
        self.config.save_on_copy = self.save_on_copy.get()
        self.config.save()

    def setup_historic_window(self):
        self.historic.delete_old_historic()
        self.historic_window.historic.insert_saved_historic(self.historic)

    def on_copy(self):
        try:
            self.exception_proposal.validate()
        except ValueError as exception:
            self.window.set_log(exception.__str__())
        else:
            copy(self.exception_proposal.get_text_to_copy())
            if self.save_on_copy.get():
                self.save_current_exception_proposal()

    def on_reset(self):
        self.exception_proposal.reset()
        self.window.date.config(text="")

    def save_current_exception_proposal(self):
        now = datetime.now()
        try:
            self.add_exception_proposal_to_historic(self.exception_proposal, now)
        except IntegrityError:
            self.window.set_log("Um registro com o mesmo CPF já existe!")

    def on_save(self):
        try:
            self.exception_proposal.validate()
        except ValueError as exception:
            self.window.set_log(exception.__str__())
        else:
            self.save_current_exception_proposal()

    def add_exception_proposal_to_historic(self, proposal: ExceptionProposal, date: datetime):
        self.historic.add_exception_proposal(proposal, date)
        self.historic_window.historic.add_exception_proposal(proposal, date)

    def on_date_change(self):
        if self.exception_proposal.d_plus.is_empty():
            self.window.date.config(text="")
        else:
            self.window.date.config(text=self.exception_proposal.d_plus.get_date_formatted())

    def on_product_change(self):
        self.window.proposed.update_validate(self.exception_proposal.product)
        self.window.promotion.update_validate(self.exception_proposal.product)


class ExceptionProposalWindow(Tk):
    def __init__(self, *args, **kwargs):
        super(ExceptionProposalWindow, self).__init__(*args, **kwargs)
        self.title("Proposta de exceção")
        self.resizable(False, False)
        self.menu = Menu(self)
        self.configure(menu=self.menu)

        frame_1 = Frame()
        frame_1.pack(
            padx=20,
            pady=10
        )
        Label(
            frame_1,
            text="CPF"
        ).grid(
            row=0,
            column=0,
            sticky=W,
            pady=5,
            columnspan=2
        )
        self.cpf = Entry(
            frame_1,
            validate="key",
            validatecommand=(self.register(CPF.is_text_valid_for_input), "%P")
        )
        self.cpf.grid(
            row=0,
            column=2,
            columnspan=2,
            sticky=E
        )
        Label(
            frame_1,
            text="Produto"
        ).grid(
            row=1,
            column=0,
            sticky=W,
            pady=5,
            columnspan=2
        )
        self.product = Combobox(
            frame_1,
            values=PRODUCTS,
            state="readonly",
            width=10
        )
        self.product.grid(
            row=1,
            column=2,
            columnspan=2,
            sticky=E
        )
        Label(
            frame_1,
            text="Valor atualizado"
        ).grid(
            row=2,
            column=0,
            sticky=W,
            pady=5,
            columnspan=2
        )
        self.updated_value = Entry(
            frame_1,
            validate="key",
            validatecommand=(self.register(BRLVar.is_text_valid_for_input), "%P"),
            width=10
        )
        self.updated_value.grid(
            row=2,
            column=2,
            columnspan=2,
            sticky=E
        )
        Label(
            frame_1,
            text="Valor com desconto"
        ).grid(
            row=3,
            column=0,
            sticky=W,
            pady=5)
        self.promotion = ProposedLine(
            frame_1
        )
        self.promotion.grid(
            row=3,
            column=1,
            columnspan=3,
            sticky=E
        )
        Label(
            frame_1,
            text="Dias em atraso").grid(
            row=4,
            column=0,
            sticky=W,
            pady=5,
            columnspan=2
        )
        self.delayed = Spinbox(
            master=frame_1,
            validate="key",
            validatecommand=(self.register(lambda string: IntStr.is_text_valid(string, 1000, 0)), "%P"),
            width=5,
            from_=1,
            to=999
        )
        self.delayed.grid(
            row=4,
            column=2,
            columnspan=2,
            sticky=E
        )
        Label(
            frame_1,
            text="Data proposta para pagamento").grid(
            row=5,
            column=0,
            sticky=W,
            pady=5,
            columnspan=2
        )
        self.date = Label(
            frame_1
        )
        self.date.grid(
            row=5,
            column=2,
            sticky=E
        )
        self.d_plus = Spinbox(
            master=frame_1,
            validate="key",
            validatecommand=(self.register(lambda string: IntStr.is_text_valid(string, 5, 0)), "%P"),
            width=5,
            from_=1,
            to=5
        )
        self.d_plus.grid(
            row=5,
            column=3,
            sticky=E
        )
        Label(
            frame_1,
            text="Valor proposto para pagamento").grid(
            row=6,
            column=0,
            sticky=W,
            pady=5
        )
        self.proposed = ProposedLine(
            frame_1
        )
        self.proposed.grid(
            row=6,
            column=1,
            columnspan=3,
            sticky=E
        )
        Label(
            frame_1,
            text="Telefone"
        ).grid(
            row=7,
            column=0,
            sticky=W,
            pady=5,
            columnspan=2
        )
        self.phone = Entry(
            frame_1,
            validate="key",
            validatecommand=(self.register(Phone.is_text_valid_for_input), "%P")
        )
        self.phone.grid(
            row=7,
            column=2,
            columnspan=2,
            sticky=E)
        Label(
            frame_1,
            text="E-mail"
        ).grid(
            row=8,
            column=0,
            sticky=W,
            pady=5
        )
        self.email = Entry(
            frame_1,
            validate="key",
            validatecommand=(self.register(Email.is_text_valid_for_input), "%P"),
            width=35
        )
        self.email.grid(
            row=8,
            column=1,
            columnspan=3,
            sticky=E
        )
        frame_2 = Frame()
        frame_2.pack(
            pady=10,
            expand=True,
            fill=X
        )
        self.save = Button(
            master=frame_2,
            text="Salvar"
        )
        self.save.pack(
            side=LEFT,
            expand=True,
            fill=X,
            padx=30
        )
        self.copy = Button(
            master=frame_2,
            text="Copiar"
        )
        self.copy.pack(
            side=LEFT,
            expand=True,
            fill=X
        )
        self.reset = Button(
            master=frame_2,
            text="Redefinir"
        )
        self.reset.pack(
            side=LEFT,
            expand=True,
            fill=X,
            padx=30
        )
        self.log = Label(
            background="white",
            anchor=W
        )
        self.log.pack(
            side=LEFT,
            expand=1,
            fill=X
        )

    def set_log(self, something: str):
        self.log.config(text=something)
        self.after(5000, lambda: self.log.config(text=""))


if __name__ == '__main__':
    ExceptionProposalApp()

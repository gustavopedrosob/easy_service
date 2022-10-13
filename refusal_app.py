from datetime import datetime, timedelta
from tkinter import Tk, Button, Label, Text, END, W, Menu, Toplevel, E, Frame, X
from tkinter.ttk import Combobox
from typing import Optional

from pyperclip import copy

from common.about_window import AboutWindow
from common.constants import REFUSAL_REASONS
from common.tk_util import BRLVar, Treeview
from common.proposed import ProposedBox
from refusal import Proposals
from exception_proposal import Proposed, NoKind, Instalments


class ProposalsTreeView(Treeview):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            columns=("first_instalment", "instalments", "else_instalments"),
            show="headings",
            selectmode="browse",
            **kwargs
        )
        self.column(
            "first_instalment",
            width=150
        )
        self.column(
            "instalments",
            width=100
        )
        self.column(
            "else_instalments",
            width=150
        )
        self.heading(
            "first_instalment",
            text="Entrada"
        )
        self.heading(
            "instalments",
            text="Parcelas"
        )
        self.heading(
            "else_instalments",
            text="Valor das parcelas"
        )

    def insert_proposal(self, proposed: Proposed, key: Optional[str] = None) -> str:
        if key:
            self.item(key, values=proposed.get_values_formated())
            return key
        else:
            return self.insert("", END, values=proposed.get_values_formated())

    def remove_proposal(self, key):
        self.delete(key)

    def get_key_from_selected(self):
        try:
            selection = self.selection()[0]
        except IndexError:
            return None
        else:
            return selection

    def reset(self):
        self.delete(*self.get_children())


class ProposedWindow(Toplevel):
    def __init__(self, *args, **kwargs):
        super(ProposedWindow, self).__init__(*args, **kwargs)
        self.withdraw()
        self.resizable(False, False)
        self.instalment_frame = ProposedBox(self)
        self.instalment_frame.grid(
            row=0,
            column=0
        )
        self.confirm = Button(
            self,
            text="Confirmar"
        )
        self.confirm.grid(
            row=1,
            column=0
        )
        self.log = Label(self)
        self.log.grid(
            row=2,
            column=0,
            sticky=W
        )

    def set_log_text(self, something):
        self.log.config(text=something)
        self.after(5000, lambda: self.log.config(text=""))

    def on_add_proposal(self):
        self.deiconify()
        self.title("Adicionar")

    def on_edit_proposal(self):
        self.deiconify()
        self.title("Editar")


class RefusalWindow(Tk):
    def __init__(self, *args, **kwargs):
        super(RefusalWindow, self).__init__(*args, **kwargs)
        self.title("Tabulação recusa")
        self.menu = Menu(self)
        self.configure(menu=self.menu)
        self.resizable(False, False)
        frame = Frame()
        frame.pack(
            padx=15,
            pady=(10, 0)
        )
        self.proposals = ProposalsTreeView(frame)
        self.proposals.grid(
            row=0,
            column=0,
            columnspan=3
        )
        Label(
            frame,
            name="label_refusal_reason",
            text="Motivo da recusa"
        ).grid(
            row=1,
            column=0,
            columnspan=3,
            pady=5
        )
        self.preset_refusal_reason = Combobox(
            frame,
            values=tuple(REFUSAL_REASONS.keys())
        )
        self.preset_refusal_reason.grid(
            row=1,
            column=2,
            sticky=E
        )
        self.refusal_reason = Text(
            frame,
            width=50,
            height=4
        )
        self.refusal_reason.grid(
            row=2,
            column=0,
            columnspan=3
        )
        self.copy_button = Button(
            frame,
            text="Copiar"
        )
        self.copy_button.grid(
            row=3,
            column=0,
            columnspan=3,
            sticky=W,
            pady=10,
            padx=20
        )
        self.add = Button(
            frame,
            text="Adicionar"
        )
        self.add.grid(
            row=3,
            column=0,
            columnspan=3
        )
        self.reset_button = Button(
            frame,
            text="Redefinir"
        )
        self.reset_button.grid(
            row=3,
            column=2,
            columnspan=3,
            pady=10,
            padx=20,
            sticky=E
        )
        self.log = Label(
            self,
            background="white",
            anchor=W
        )
        self.log.pack(
            expand=1,
            fill=X
        )
        self.preset_refusal_reason.bind("<<ComboboxSelected>>", lambda args_: self.on_set_preset_refusal_reason())

    def set_log_text(self, something):
        self.log.config(text=something)
        self.after(5000, lambda: self.log.config(text=""))

    def on_set_preset_refusal_reason(self):
        self.refusal_reason.delete("0.0", END)
        self.refusal_reason.insert("0.0", REFUSAL_REASONS[self.preset_refusal_reason.get()])


class RefusalApp:
    def __init__(self):
        self.proposals = Proposals()
        self.window = RefusalWindow()
        self.proposal = Proposed(BRLVar(self.window), Instalments(self.window), BRLVar(self.window))
        self.proposed_window = ProposedWindow()
        self.about_window = AboutWindow()
        self.setup_proposed_window()
        self.setup_main_window()

    def insert_proposal(self, proposed: Proposed, key: Optional[str] = None):
        key = self.window.proposals.insert_proposal(proposed, key)
        self.proposals.insert_proposal(key, proposed)

    def remove_proposal(self, key: str):
        self.window.proposals.remove_proposal(key)
        self.proposals.remove_proposal(key)

    def reset_proposals(self):
        self.window.proposals.reset()
        self.proposals.reset()

    def setup_main_window(self):
        self.window.menu.add_command(label="Sobre", command=self.about_window.deiconify)
        self.window.add.config(command=self.on_add_proposal_button_pressed)
        self.window.proposals.popup.add_command(label="Editar", command=self.on_edit_proposal_context_button_pressed)
        self.window.proposals.popup.add_command(label="Remover", command=self.remove_proposed_selected)
        self.window.proposals.popup.add_separator()
        self.window.proposals.popup.add_command(label="Copiar", command=self.copy_proposed_selected)
        self.window.proposals.bind("<Delete>", lambda args: self.on_delete_pressed())
        self.window.proposals.bind("<Control-c>", lambda args: self.on_control_c_pressed())
        self.window.reset_button.config(command=self.on_reset_button_pressed)
        self.window.copy_button.config(command=self.on_copy_button_pressed)
        self.window.mainloop()

    def setup_proposed_window(self):
        self.proposed_window.protocol("WM_DELETE_WINDOW", self.on_close_proposed_window)
        self.proposed_window.instalment_frame.first_instalment.config(textvariable=self.proposal.first_instalment)
        self.proposed_window.instalment_frame.instalments.config(textvariable=self.proposal.instalments)
        self.proposed_window.instalment_frame.else_instalment.config(textvariable=self.proposal.else_instalment)

    def on_reset_button_pressed(self):
        self.reset_proposals()
        self.window.refusal_reason.delete("0.0", END)
        self.window.preset_refusal_reason.delete(0, END)

    def on_confirm_button_pressed(self, key: Optional[str] = None):
        try:
            self.insert_proposal(self.proposal, key)
        except NoKind:
            self.proposed_window.set_log_text("Proposta inválida.")
        else:
            self.proposed_window.withdraw()
            self.proposal.reset()

    def on_add_proposal_button_pressed(self):
        self.proposed_window.confirm.config(command=self.on_confirm_button_pressed)
        self.proposed_window.on_add_proposal()

    def on_delete_pressed(self):
        if (key := self.window.proposals.get_key_from_selected()) is not None:
            self.remove_proposal(key)

    def on_edit_proposal_context_button_pressed(self):
        key = self.window.proposals.get_key_from_selected()
        old_proposed = self.proposals.get_proposal(key)
        self.proposal.update(old_proposed)
        self.proposed_window.confirm.config(command=lambda: self.on_confirm_button_pressed(key))
        self.proposed_window.on_edit_proposal()

    def remove_proposed_selected(self):
        key = self.window.proposals.get_key_from_selected()
        self.remove_proposal(key)

    def copy_proposed_selected(self):
        key = self.window.proposals.get_key_from_selected()
        proposed = self.proposals.get_proposal(key)
        if self.proposals.index(proposed) == 0:
            date = datetime.now() + timedelta(days=1)
        else:
            date = datetime.now() + timedelta(days=4)
        copy(proposed.get_formated(date))

    def on_control_c_pressed(self):
        if self.window.proposals.get_key_from_selected() is not None:
            self.copy_proposed_selected()

    def on_copy_button_pressed(self):
        refusal_reason = self.window.refusal_reason.get("0.0", END)
        if self.proposals.is_empty():
            self.window.set_log_text("Preencha pelo menos uma proposta para copiar.")
        elif not refusal_reason.strip():
            self.window.set_log_text("Preencha um motivo de recusa.")
        else:
            copy(self.proposals.get_text_to_copy() + "\n" + refusal_reason)

    def on_close_proposed_window(self):
        self.proposed_window.withdraw()
        self.proposal.reset()


if __name__ == '__main__':
    RefusalApp()

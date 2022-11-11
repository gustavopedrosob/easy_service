import datetime
import threading
import tkinter as tk
from tkinter import ttk

import typing

import about
import agreement
import database
from common import widgets, colors, formater, validators, converter, utils
from common import constants
import exception_proposal as ep


class AgreementControlTreeView(widgets.Treeview):
    def __init__(self, *args, **kwargs):
        cpf = "cpf"
        payed = "payed"
        value = "value"
        create_date = "create_date"
        due_date = "due_date"

        super().__init__(
            *args,
            columns=(cpf, payed, value, create_date, due_date),
            show="headings",
            selectmode="browse",
            **kwargs
        )
        self.column(cpf, width=150)
        self.column(payed, width=150)
        self.column(value, width=150)
        self.column(create_date, width=150)
        self.column(due_date, width=150)
        self.heading(cpf, text=constants.CPF)
        self.heading(payed, text=constants.PAYED)
        self.heading(value, text=constants.VALUE)
        self.heading(create_date, text=constants.CREATE_DATE)
        self.heading(due_date, text=constants.DUE_DATE)
        self.sorting_config = {"column": None, "reverse": False}
        self.context_menu_management.context_menu_selected.add_command(label="Copiar CPF", command=self.on_copy_cpf)

    def on_copy_cpf(self):
        id_, agreement_ = self.get_agreement(self.selection()[0])
        utils.copy_to_clipboard(self, formater.format_cpf(agreement_.cpf, False))

    def add_agreement(self, id_: int, agreement_: agreement.Agreement):
        self.insert("", tk.END, iid=str(id_), values=(
            formater.format_cpf(agreement_.cpf, True), converter.bool_to_str(agreement_.payed),
            formater.format_brl(agreement_.value), agreement_.create_date.strftime("%d/%m/%Y"),
            agreement_.get_due_date().strftime("%d/%m/%Y")))

    def get_agreement(self, key: str) -> typing.Tuple[int, agreement.Agreement]:
        item = self.item(key)
        cpf, payed, value, create_date, due_date = item["values"]
        create_date = converter.date_str_to_date(create_date)
        due_date = converter.date_str_to_date(due_date)
        d_plus = (due_date - create_date).days
        return int(key), agreement.Agreement(cpf, converter.str_to_bool(payed), converter.brl_to_float(value), create_date,
                                             d_plus)

    def get_agreements(self) -> typing.List[typing.Tuple[int, agreement.Agreement]]:
        agreements = []
        for child in self.get_children():
            agreements.append(self.get_agreement(child))
        return agreements

    def on_click(self, event):
        super().on_click(event)
        region = self.identify_region(event.x, event.y)
        if region == "heading":
            agreements = self.get_agreements()
            keys = {"#2": agreement.Agreement.is_payed, "#3": agreement.Agreement.get_value,
                    "#4": agreement.Agreement.get_create_date, "#5": agreement.Agreement.get_due_date}
            column = self.identify_column(event.x)
            if column in keys:
                self.sorting_config["column"] = column
                if column == self.sorting_config["column"]:
                    self.sorting_config["reverse"] = not self.sorting_config["reverse"]
                else:
                    self.sorting_config["reverse"] = False
                agreements.sort(key=keys[column], reverse=self.sorting_config["reverse"])
                self.update_agreements(agreements)
            else:
                self.sorting_config["column"] = None

    def update_agreements(self, agreements: typing.Iterable[typing.Tuple[int, agreement.Agreement]]) -> None:
        self.delete(*self.get_children())
        for id_, agreement_ in agreements:
            self.add_agreement(id_, agreement_)


class AgreementControlWindow:
    def __init__(self, database_: database.DataBase):
        self.top_level = tk.Toplevel()
        self.top_level.withdraw()
        self.top_level.title(constants.AGREEMENT_CONTROL)
        self.top_level.resizable(False, False)
        self.top_level.protocol("WM_DELETE_WINDOW", self.top_level.withdraw)

        filter_label_frame = ttk.LabelFrame(self.top_level, text="Filtrar")
        filter_label_frame.pack(padx=10, pady=10, fill=tk.BOTH)

        state_label_frame = ttk.LabelFrame(filter_label_frame, text="Estado")
        state_label_frame.pack(side=tk.LEFT, padx=5, pady=5)
        self.state = ttk.Combobox(state_label_frame, values=("Ativo", "Pago", "Atrasado", "Cancelado"))
        self.state.pack(padx=5, pady=5)

        self.historic = AgreementControlTreeView(self.top_level)
        self.historic.pack(padx=10)

        statistics_label_frame = ttk.LabelFrame(self.top_level, text="Estatísticas")
        statistics_label_frame.pack(padx=10, pady=10, fill=tk.BOTH)

        stats_frame = tk.Frame(statistics_label_frame)
        stats_frame.pack(side=tk.LEFT)
        filter_frame = tk.Frame(statistics_label_frame)
        filter_frame.pack(side=tk.RIGHT, fill=tk.Y)
        period_filter_label_frame = ttk.LabelFrame(filter_frame, text="Período")
        period_filter_label_frame.pack(padx=5)
        self.period = ttk.Combobox(period_filter_label_frame, values=("Hoje", "Esta semana", "Este mês"))
        self.period.pack(padx=5, pady=5)
        self.total_negotiated = tk.Label(stats_frame, text="Total negociado: N/A")
        self.total_negotiated.grid(row=0, column=0, sticky=tk.W)
        self.total_payed = tk.Label(stats_frame, text="Total pago: N/A")
        self.total_payed.grid(row=1, column=0, sticky=tk.W)
        self.total_canceled = tk.Label(stats_frame, text="Total cancelado: N/A")
        self.total_canceled.grid(row=2, column=0, sticky=tk.W)
        self.total_overdue = tk.Label(stats_frame, text="Total atrasado: N/A")
        self.total_overdue.grid(row=3, column=0, sticky=tk.W)
        self.agreements_quantity = tk.Label(stats_frame, text="Acordos: N/A")
        self.agreements_quantity.grid(row=0, column=1, sticky=tk.W)
        self.agreements_payed = tk.Label(stats_frame, text="Acordos pagos: N/A")
        self.agreements_payed.grid(row=1, column=1, sticky=tk.W)
        self.agreements_canceled = tk.Label(stats_frame, text="Acordos cancelados: N/A")
        self.agreements_canceled.grid(row=2, column=1, sticky=tk.W)
        self.agreements_overdue = tk.Label(stats_frame, text="Acordos atrasados: N/A")
        self.agreements_overdue.grid(row=3, column=1, sticky=tk.W)
        self.state.bind("<<ComboboxSelected>>", lambda event: self.on_select_state(event, database_))
        self.period.bind("<<ComboboxSelected>>", self.on_select_period)
        self.update(database_.get_agreement_historic())
        self.historic.context_menu_management.context_menu_selected.add_command(
            label="Definir como pago",
            command=lambda: self.on_set_agreement_as_payed(database_)
        )
        self.historic.context_menu_management.context_menu_selected.add_command(
            label="Deletar",
            command=lambda: self.on_delete_agreement(database_)
        )

    def on_set_agreement_as_payed(self, database_):
        agreement_ = self.historic.get_agreement(self.historic.selection()[0])
        database_.set_agreement_as_payed(agreement_.cpf)
        self.update(database_.get_agreement_historic())

    def on_select_state(self, event, database_):
        agreements = database_.get_agreement_historic()
        state = self.state.get()
        filters = {"Pago": agreement.Agreement.is_payed, "Atrasado": agreement.Agreement.is_overdue,
                   "Cancelado": agreement.Agreement.is_cancelled, "Ativo": agreement.Agreement.is_active}
        filtered_agreements = list(filter(filters[state], agreements))
        self.update(filtered_agreements)

    def on_select_period(self, event):
        agreements = self.historic.get_agreements()
        period = self.period.get()

        today = datetime.date.today()
        first_week_day = today.replace(day=today.day - today.weekday())
        last_week_day = first_week_day + datetime.timedelta(days=7)
        first_month_day = today.replace(day=1)
        last_month_day = first_month_day + datetime.timedelta(days=30)

        filters = {"Hoje": lambda agreement_: agreement_.create_date == datetime.date.today(),
                   "Esta semana": lambda agreement_: first_week_day < agreement_.create_date < last_week_day,
                   "Este mês": lambda agreement_: first_month_day < agreement_.create_date < last_month_day}

        filtered_agreements = list(filter(filters[period], agreements))
        self.update_statistics(filtered_agreements)

    def update(self, agreements: typing.List[typing.Tuple[int, agreement.Agreement]]):
        self.historic.update_agreements(agreements)
        if len(agreements) > 0:
            self.update_statistics(agreements)

    def update_statistics(self, agreements: typing.List[typing.Tuple[int, agreement.Agreement]]):
        agreements = list(map(lambda agreement_and_id: agreement_and_id[1], agreements))
        agreements_payed = list(filter(agreement.Agreement.is_payed, agreements))
        agreements_cancelled = list(filter(agreement.Agreement.is_cancelled, agreements))
        agreements_overdue = list(filter(agreement.Agreement.is_overdue, agreements))

        agreements_quantity = len(agreements)
        agreements_payed_quantity = len(agreements_payed)
        agreements_cancelled_quantity = len(agreements_cancelled)
        agreements_overdue_quantity = len(agreements_overdue)

        agreements_payed_ratio = agreements_payed_quantity / agreements_quantity
        agreements_cancelled_ratio = agreements_cancelled_quantity / agreements_quantity
        agreements_overdue_ratio = agreements_overdue_quantity / agreements_quantity

        total_negotiated = sum(map(agreement.Agreement.get_value, agreements))
        total_payed = sum(map(agreement.Agreement.get_value, agreements_payed))
        total_canceled = sum(map(agreement.Agreement.get_value, agreements_cancelled))
        total_overdue = sum(map(agreement.Agreement.get_value, agreements_overdue))

        total_payed_ratio = total_payed / total_negotiated
        total_canceled_ratio = total_canceled / total_negotiated
        total_overdue_ratio = total_overdue / total_negotiated

        self.total_negotiated.config(text=f"Total negociado: {formater.format_brl(total_negotiated)}")
        self.total_payed.config(
            text=f"Total pago: {formater.format_brl(total_payed)} ({round(total_payed_ratio * 100, 2)}%)"
        )
        self.total_canceled.config(
            text=f"Total cancelado: {formater.format_brl(total_canceled)} ({round(total_canceled_ratio * 100, 2)}%)")
        self.total_overdue.config(
            text=f"Total atrasado: {formater.format_brl(total_overdue)} ({round(total_overdue_ratio * 100, 2)}%)"
        )
        self.agreements_quantity.config(text=f"Acordos: {agreements_quantity}")
        self.agreements_payed.config(
            text=f"Acordos pagos: {agreements_payed_quantity} ({round(agreements_payed_ratio * 100, 2)}%)"
        )
        self.agreements_canceled.config(
            text=f"Acordos cancelados: {agreements_cancelled_quantity} ({round(agreements_cancelled_ratio * 100, 2)}%)"
        )
        self.agreements_overdue.config(
            text=f"Acordos atrasados: {agreements_overdue_quantity} ({round(agreements_overdue_ratio * 100, 2)}%)"
        )

    def on_delete_agreement(self, database_):
        selection = self.historic.selection()[0]
        id_, agreement_selected = self.historic.get_agreement(selection)
        self.historic.delete(selection)
        database_.delete_agreement_by_id(id_)
        agreements = self.historic.get_agreements()
        self.update_statistics(agreements)


class HistoricTreeView(widgets.Treeview):
    def __init__(self, *args, **kwargs):
        cpf = "cpf"
        create_date = "create_date"
        due_date = "due_date"
        counter_proposal = "counter_proposal"
        installments = "installments"
        super().__init__(
            *args,
            columns=(cpf, create_date, due_date, counter_proposal, installments),
            show="headings",
            selectmode="browse",
            **kwargs
        )
        self.column(cpf, width=150)
        self.column(create_date, width=150)
        self.column(due_date, width=150)
        self.column(counter_proposal, width=150)
        self.column(installments, width=150)
        self.heading(cpf, text=constants.CPF)
        self.heading(create_date, text=constants.CREATE_DATE)
        self.heading(due_date, text=constants.DUE_DATE)
        self.heading(counter_proposal, text=constants.COUNTER_PROPOSAL)
        self.heading(installments, text=constants.INSTALLMENTS)

        self.context_menu_management.context_menu_selected.add_command(label="Copiar", command=self.on_copy)

    def on_copy(self):
        pass
        # selected = self.selection()
        # item = self.item(selected)
        # cpf = ep.CPF.get_text_formatted(item["values"][0], False)
        # return copy(cpf)

    def add_exception_proposal(self, proposal: ep.ExceptionProposalSent):
        values = formater.format_cpf(proposal.cpf, True), proposal.create_date.strftime("%d/%m/%Y"),\
                 proposal.get_due_date().strftime("%d/%m/%Y"), proposal.counter_proposal, proposal.installments
        self.insert("", tk.END, values=values)


class ExceptionProposalHistoricWindow:
    def __init__(self, *args, **kwargs):
        self.top_level = tk.Toplevel(*args, **kwargs)
        self.top_level.withdraw()
        self.top_level.title(constants.EXCEPTION_PROPOSAL_HISTORIC)
        self.top_level.resizable(False, False)
        self.top_level.protocol("WM_DELETE_WINDOW", self.top_level.withdraw)
        self.historic = HistoricTreeView(self.top_level)
        self.historic.pack(padx=10, pady=10)


class ProposalsTreeView(widgets.Treeview):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            columns=("installments", "first_installment", "else_installments", "due_date", "total"),
            show="headings",
            selectmode="browse",
            height=22,
            **kwargs
        )
        self.column(
            "installments",
            width=50,
            minwidth=25,
            stretch=True
        )
        self.column(
            "first_installment",
            width=75,
            minwidth=50,
            stretch=True
        )
        self.column(
            "else_installments",
            width=75,
            minwidth=50,
            stretch=True
        )
        self.column(
            "due_date",
            width=75,
            minwidth=50,
            stretch=True
        )
        self.column(
            "total",
            width=75,
            minwidth=50,
            stretch=True
        )
        self.heading(
            "installments",
            text=constants.INSTALLMENTS
        )
        self.heading(
            "first_installment",
            text=constants.FIRST_INSTALLMENT
        )
        self.heading(
            "else_installments",
            text=constants.ELSE_INSTALLMENT
        )
        self.heading(
            "due_date",
            text=constants.DUE_DATE
        )
        self.heading(
            "total",
            text=constants.TOTAL
        )
        self.context_menu_management.context_menu_selected.add_command(label="Remover", command=self.on_remove)
        self.context_menu_management.context_menu_selected.add_command(label="Copiar", command=self.on_copy)

    def on_remove(self):
        key = self.get_key_from_selected()
        self.remove_proposal(key)

    def on_copy(self):
        key = self.get_key_from_selected()
        proposal = self.get_proposal(key)
        self.clipboard_clear()
        self.clipboard_append(proposal.get_formatted_with_date())
        self.clipboard_get()

    def insert_proposal(self, proposal: ep.ProposalWithDate, key: typing.Optional[str] = None) -> str:
        if proposal.is_installments():
            values = proposal.installments, formater.format_brl(proposal.first_installment), \
                     formater.format_brl(proposal.else_installment), proposal.due_date.strftime("%d/%m/%Y"), \
                     formater.format_brl(proposal.get_total())
        else:
            values = proposal.installments, formater.format_brl(proposal.first_installment), \
                     "", proposal.due_date.strftime("%d/%m/%Y"), ""
        if key:
            self.item(key, values=values)
            return key
        else:
            return self.insert("", tk.END, values=values)

    def get_proposal(self, key: str) -> typing.Optional[ep.ProposalWithDate]:
        try:
            installments, first_installments, else_installments, date, _ = self.item(key)["values"]
        except tk.TclError:
            return None
        else:
            return ep.ProposalWithDate(
                int(installments),
                converter.brl_to_float(first_installments),
                converter.brl_to_float(else_installments) if validators.is_brl_valid(else_installments) else None,
                converter.date_str_to_date(date)
            )

    def remove_proposal(self, key: str):
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

    def get_proposals(self) -> typing.List[ep.ProposalWithDate]:
        proposals = []
        for key in self.get_children():
            proposal = self.get_proposal(key)
            if proposal is not None:
                proposals.append(proposal)
        return proposals


class Proposal:
    def __init__(self, master: tk.Widget,
                 brl_validate_command,
                 product_variable: tk.StringVar,
                 max_instalments_24_validate_command,
                 max_instalments_18_validate_command,
                 **kwargs
                 ):
        self._master = master
        self.installments = widgets.Spinbox(
            master,
            placeholder=constants.INSTALLMENTS,
            validate="key",
            validatecommand=max_instalments_18_validate_command,
        )
        self.installments.pack(
            fill=tk.X,
            pady=5,
            padx=5
        )
        self.first_installment = widgets.Entry(
            master,
            placeholder=constants.FIRST_INSTALLMENT,
            validate="key",
            validatecommand=brl_validate_command
        )
        self.first_installment.pack(
            fill=tk.X,
            pady=(0, 5),
            padx=5
        )
        self.else_installment = widgets.Entry(
            master,
            placeholder=constants.ELSE_INSTALLMENT,
            validate="key",
            validatecommand=brl_validate_command
        )
        self.else_installment.pack(
            fill=tk.X,
            pady=(0, 5),
            padx=5
        )
        self.product_variable = product_variable
        self.product_variable.trace("w", lambda *args: self.on_product_change())
        self.respective_validate_command = {
            18: max_instalments_18_validate_command,
            24: max_instalments_24_validate_command
        }

    def on_product_change(self):
        max_instalments = constants.MAX_INSTALMENTS[self.product_variable.get()]
        was_with_placeholder = self.installments.is_using_placeholder()
        vc = self.respective_validate_command[max_instalments]
        self.installments.placeholder_config(
            validatecommand=vc,
            validate="key",
            from_=1,
            to=max_instalments,
        )
        self.installments.set_placeholder(was_with_placeholder)

    def get_proposal(self) -> ep.Proposal:
        else_installment = self.else_installment.get()
        return ep.Proposal(
            int(self.installments.get()),
            converter.brl_to_float(self.first_installment.get()),
            converter.brl_to_float(else_installment) if validators.is_brl_valid(else_installment) else None,
        )

    def reset(self):
        for object_ in (self.installments, self.first_installment, self.else_installment):
            object_.set_placeholder(True)


class ProposalWithDate(Proposal):
    def __init__(self, master,
                 brl_validate_command,
                 d_plus_validate_command,
                 product_variable: tk.StringVar,
                 max_instalments_24_validate_command,
                 max_instalments_18_validate_command,
                 d_plus_max: int,
                 **kwargs):
        super().__init__(master,
                         brl_validate_command,
                         product_variable,
                         max_instalments_24_validate_command,
                         max_instalments_18_validate_command,
                         **kwargs)
        self.d_plus = widgets.Spinbox(
            master,
            placeholder=constants.D_PLUS,
            validate="key",
            validatecommand=d_plus_validate_command,
            from_=1,
            to=d_plus_max
        )
        self.d_plus.pack(
            fill=tk.X,
            padx=5
        )

    def reset(self):
        super().reset()
        self.d_plus.set_placeholder(True)

    def get_proposal_with_date(self) -> ep.ProposalWithDate:
        else_installment = self.else_installment.get()
        return ep.ProposalWithDate(
            int(self.installments.get()),
            converter.brl_to_float(self.first_installment.get()),
            converter.brl_to_float(else_installment) if validators.is_brl_valid(else_installment) else None,
            datetime.date.today() + datetime.timedelta(days=int(self.d_plus.get()))
        )


class EasyServiceWindow:
    def __init__(self, window, database_, agreement_control_window, ep_historic_window, about_window):
        self.window = window
        self.window.minsize(800, 600)
        self.window.geometry("800x600")

        brl_vc = self.new_vc(validators.is_brl_valid_for_input)
        d_plus_3_vc = self.new_vc(lambda string: validators.is_int_text_valid_for_input(string, 3, 1))
        d_plus_5_vc = self.new_vc(lambda string: validators.is_int_text_valid_for_input(string, 5, 1))
        max_instalments_24_vc = self.new_vc(lambda string: validators.is_int_text_valid_for_input(string, 24, 1))
        max_instalments_18_vc = self.new_vc(lambda string: validators.is_int_text_valid_for_input(string, 18, 1))

        self.product_variable = tk.StringVar()
        self.menu = tk.Menu(self.window)

        self.window.title(constants.EASY_SERVICE)
        self.window.configure(menu=self.menu)

        left_frame = tk.Frame()
        top_frame = tk.Frame()
        bottom_frame = tk.Frame()
        right_frame = tk.Frame()
        self.log = tk.Label(
            background=colors.WHITE,
            anchor=tk.W
        )
        self.log.pack(
            side=tk.BOTTOM,
            fill=tk.X
        )
        bottom_frame.pack(
            side=tk.BOTTOM,
            fill=tk.BOTH
        )
        left_frame.pack(
            side=tk.LEFT,
            fill=tk.BOTH
        )
        right_frame.pack(
            side=tk.RIGHT,
            fill=tk.BOTH
        )
        top_frame.pack(
            side=tk.TOP,
            expand=True,
            fill=tk.BOTH,
            padx=5
        )
        costumer_label_frame = ttk.LabelFrame(
            left_frame,
            text="Sobre o cliente"
        )
        costumer_label_frame.pack(
            ipadx=10,
            ipady=10,
            expand=True,
            fill=tk.BOTH
        )
        self.cpf = widgets.Entry(
            costumer_label_frame,
            placeholder=constants.CPF,
            placeholder_color="grey",
            validate="key",
            validatecommand=self.new_vc(validators.is_cpf_valid_for_input),
        )
        self.cpf.pack(
            fill=tk.X,
            pady=5,
            padx=5
        )
        self.phone = widgets.Entry(
            costumer_label_frame,
            placeholder=constants.PHONE,
            validate="key",
            validatecommand=self.new_vc(validators.is_phone_valid_for_input)
        )
        self.phone.pack(
            fill=tk.X,
            pady=(0, 5),
            padx=5
        )
        self.email = widgets.Entry(
            costumer_label_frame,
            placeholder=constants.EMAIL,
            validate="key",
            validatecommand=self.new_vc(validators.is_email_valid_for_input)
        )
        self.email.pack(
            fill=tk.X,
            pady=(0, 5),
            padx=5
        )
        debit_label_frame = ttk.LabelFrame(
            left_frame,
            text="Sobre o debito"
        )
        debit_label_frame.pack(
            ipadx=10,
            ipady=10,
            expand=True,
            fill=tk.BOTH
        )
        self.product = ttk.Combobox(
            debit_label_frame,
            textvariable=self.product_variable,
            values=constants.PRODUCTS
        )
        self.product.pack(
            fill=tk.X,
            pady=5,
            padx=5
        )
        self.delayed = widgets.Spinbox(
            master=debit_label_frame,
            placeholder=constants.DELAYED,
            validate="key",
            validatecommand=self.new_vc(lambda string: validators.is_int_text_valid_for_input(string, 1000, 0)),
            from_=1,
            to=999
        )
        self.delayed.pack(
            fill=tk.X,
            pady=(0, 5),
            padx=5
        )
        self.main_value = widgets.Entry(
            debit_label_frame,
            placeholder="Valor principal",
            validate="key",
            validatecommand=brl_vc
        )
        self.main_value.pack(
            fill=tk.X,
            pady=(0, 5),
            padx=5
        )
        proposes_label_frame = ttk.LabelFrame(
            top_frame,
            text="Propostas"
        )
        proposes_label_frame.pack(
            ipadx=10,
            ipady=10,
            expand=True,
            fill=tk.BOTH
        )
        self.proposals = ProposalsTreeView(proposes_label_frame)
        self.proposals.pack(
            side=tk.TOP,
            expand=True,
            fill=tk.X,
            padx=10,
            pady=10
        )

        self.refusal_reason = ttk.Combobox(
            proposes_label_frame,
            values=tuple(constants.REFUSAL_REASONS.keys()),
            state="readonly"
        )
        self.refusal_reason.pack(
            side=tk.RIGHT,
            fill=tk.X,
            padx=(0, 10),
            pady=(0, 10)
        )
        refusal_reason_label = tk.Label(
            proposes_label_frame,
            text="Motivo de recusa"
        )
        refusal_reason_label.pack(
            side=tk.RIGHT,
            fill=tk.X,
            padx=(0, 10),
            pady=(0, 10)
        )
        self.agreement = widgets.Button(
            bottom_frame,
            text="Acordo"
        )
        self.agreement.pack(
            side=tk.LEFT,
            expand=True,
            fill=tk.X
        )
        self.refusal = widgets.Button(
            bottom_frame,
            text="Recusa"
        )
        self.refusal.pack(
            side=tk.LEFT,
            expand=True,
            fill=tk.X
        )
        self.exception_proposal = widgets.Button(
            bottom_frame,
            text="Proposta de exceção"
        )
        self.exception_proposal.pack(
            side=tk.LEFT,
            expand=True,
            fill=tk.X
        )
        self.next_costumer = widgets.Button(
            bottom_frame,
            text="Próximo cliente"
        )
        self.next_costumer.pack(
            side=tk.LEFT,
            expand=True,
            fill=tk.X
        )
        proposal_label_frame = ttk.LabelFrame(
            right_frame,
            text="Proposta"
        )
        proposal_label_frame.pack(
            ipadx=10,
            ipady=10,
            expand=True,
            fill=tk.BOTH
        )
        self.proposal = ProposalWithDate(
            proposal_label_frame,
            brl_vc,
            d_plus_3_vc,
            self.product_variable,
            max_instalments_24_vc,
            max_instalments_18_vc,
            d_plus_max=3
        )
        self.add = widgets.Button(
            proposal_label_frame,
            hover_text=constants.ADD,
            text="+"
        )
        self.add.place(
            x=0,
            y=0,
            rely=1,
            height=20,
            width=20,
            anchor=tk.SW
        )
        promotion_label_frame = ttk.LabelFrame(
            right_frame,
            text="Valor com desconto"
        )
        promotion_label_frame.pack(
            ipadx=10,
            ipady=10,
            expand=True,
            fill=tk.BOTH
        )
        self.promotion = Proposal(
            promotion_label_frame,
            brl_vc,
            self.product_variable,
            max_instalments_24_vc,
            max_instalments_18_vc
        )
        costumer_proposal_frame = ttk.LabelFrame(
            right_frame,
            text="Proposta do cliente"
        )
        costumer_proposal_frame.pack(
            ipadx=10,
            ipady=10,
            expand=True,
            fill=tk.BOTH
        )
        self.costumer_proposal = ProposalWithDate(
            costumer_proposal_frame,
            brl_vc,
            d_plus_5_vc,
            self.product_variable,
            max_instalments_24_vc,
            max_instalments_18_vc,
            5
        )
        self.product_variable.set(constants.CCRCFI)
        self.refusal.config(command=self.on_refusal)
        self.proposals.own_bind("<OnUnselect>", self.on_unselect_proposal)
        self.proposals.own_bind("<OnSelect>", self.on_select_proposal)
        self.proposal.installments.bind("<Return>", lambda *args: self.on_any_edit(self.on_installments_edit))
        self.proposal.first_installment.bind("<Return>", lambda *args: self.on_any_edit(self.on_first_installment_edit))
        self.proposal.else_installment.bind("<Return>", lambda *args: self.on_any_edit(self.on_else_installment_edit))
        self.proposal.d_plus.bind("<Return>", lambda *args: self.on_any_edit(self.on_d_plus_edit))
        self.exception_proposal.config(command=lambda: self.on_exception_proposal(database_))
        self.agreement.config(command=lambda: self.on_agreement(database_, agreement_control_window))
        self.add.config(command=self.on_add_click)
        self.next_costumer.config(command=self.reset)
        self.menu.add_command(label=constants.OPTIONS)
        tools_menu = tk.Menu(tearoff=False)
        tools_menu.add_command(
            label=constants.EXCEPTION_PROPOSAL_HISTORIC,
            command=ep_historic_window.top_level.deiconify
        )
        tools_menu.add_command(
            label=constants.AGREEMENT_CONTROL,
            command=agreement_control_window.top_level.deiconify
        )
        self.menu.add_cascade(label=constants.TOOLS, menu=tools_menu)
        self.menu.add_command(label=constants.ABOUT, command=about_window.top_level.deiconify)

    def do_log(self, log: str):
        self.log.config(text=log)
        timer = threading.Timer(3, lambda: self.log.config(text=""))
        timer.start()

    def reset(self):
        for object_ in (self.cpf, self.phone, self.email, self.delayed, self.main_value):
            object_.set_placeholder(True)
        for object_ in (self.costumer_proposal, self.proposal, self.promotion):
            object_.reset()
        self.product_variable.set(constants.CCRCFI)
        self.refusal_reason.config(state=tk.NORMAL)
        self.refusal_reason.delete("0", tk.END)
        self.refusal_reason.config(state="readonly")

    def new_vc(self, command, args="%P"):
        return self.window.register(command), args

    def on_select_proposal(self, key):
        proposal = self.proposals.get_proposal(key)
        self.proposal.installments.set_text(str(proposal.installments))
        self.proposal.first_installment.set_text(formater.format_brl(proposal.first_installment, False))
        self.proposal.d_plus.set_text(str((proposal.due_date - datetime.date.today()).days))
        if proposal.is_installments():
            self.proposal.else_installment.set_text(formater.format_brl(proposal.else_installment, False))
        else:
            self.proposal.else_installment.set_placeholder(True)

    def on_unselect_proposal(self, key):
        print(f"Unselected proposal {key}")
        self.proposal.installments.set_placeholder(True)
        self.proposal.first_installment.set_placeholder(True)
        self.proposal.else_installment.set_placeholder(True)
        self.proposal.d_plus.set_placeholder(True)

    def on_any_edit(self, command):
        current_proposal = self.proposals.get_key_from_selected()
        if current_proposal:
            command(current_proposal)

    def on_installments_edit(self, current_proposal: str):
        if self.proposal.installments.get() != "":
            self.proposals.insert_proposal(self.proposal.get_proposal_with_date(), current_proposal)

    def on_first_installment_edit(self, current_proposal: str):
        if validators.is_brl_valid(self.proposal.first_installment.get()):
            self.proposals.insert_proposal(self.proposal.get_proposal_with_date(), current_proposal)

    def on_else_installment_edit(self, current_proposal: str):
        if validators.is_brl_valid(self.proposal.else_installment.get()):
            self.proposals.insert_proposal(self.proposal.get_proposal_with_date(), current_proposal)

    def on_d_plus_edit(self, current_proposal: str):
        if self.proposal.d_plus.get() != "":
            self.proposals.insert_proposal(self.proposal.get_proposal_with_date(), current_proposal)

    def on_refusal(self):
        proposals = self.proposals.get_proposals()
        if len(proposals) == 0:
            self.do_log("Preencha pelo menos uma proposta para copiar o texto de recusa.")
        else:
            refusal_reason = self.refusal_reason.get()
            refusal = constants.REFUSAL_REASONS.get(refusal_reason)
            proposals_text = "\n".join([proposal.get_formatted_with_date() for proposal in proposals])
            if refusal:
                final_text = proposals_text + "\n" + refusal
            else:
                final_text = proposals_text
            utils.copy_to_clipboard(self.window, final_text)
            self.do_log("Texto para recusa copiado com sucesso.")

    def on_agreement(self, database_, agreement_control_window):
        current_key_proposal_selected = self.proposals.get_key_from_selected()
        if current_key_proposal_selected is None:
            self.do_log("Selecione a proposta que você fez o acordo.")
        elif self.cpf.is_using_placeholder():
            self.do_log("Preencha o CPF para fazer um acordo.")
        else:
            proposal = self.proposals.get_proposal(current_key_proposal_selected)
            agreement_ = agreement.Agreement(
                self.cpf.get(),
                False,
                proposal.get_total(),
                datetime.date.today(),
                (proposal.due_date - datetime.date.today()).days
            )
            id_ = database_.add_agreement(agreement_)
            agreement_control_window.historic.add_agreement(id_, agreement_)
            self.do_log("Acordo salvo com sucesso.")

    def on_exception_proposal(self, database_):
        if not validators.is_cpf_valid(self.cpf.get()):
            self.do_log("Preencha o CPF corretamente para fazer uma proposta de exceção.")
        elif not validators.is_phone_valid(self.phone.get()):
            self.do_log("Preencha o telefone corretamente para fazer uma proposta de exceção.")
        elif not validators.is_email_valid(self.email.get()):
            self.do_log("Preencha o email corretamente para fazer uma proposta de exceção.")
        elif not validators.is_int_text_valid_for_input(self.delayed.get(), 1000, 1):
            self.do_log("Preencha os dias em atraso para fazer uma proposta de exceção.")
        elif not validators.is_brl_valid(self.main_value.get()):
            self.do_log("Preencha o valor principal corretamente para fazer uma proposta de exceção.")
        elif not self.promotion.get_proposal():
            self.do_log("Preencha o valor com desconto corretamente para fazer uma proposta de exceção.")
        elif not self.costumer_proposal.get_proposal_with_date():
            self.do_log("Preencha a proposta do cliente corretamente para fazer uma proposta de exceção.")
        else:
            exception_proposal = ep.ExceptionProposal(
                self.cpf.get(),
                converter.brl_to_float(self.main_value.get()),
                self.promotion.get_proposal(),
                self.costumer_proposal.get_proposal_with_date(),
                self.email.get(),
                int(self.delayed.get()),
                self.product.get(),
                self.phone.get()
            )
            utils.copy_to_clipboard(self.window, exception_proposal.get_text_to_copy())
            database_.add_exception_proposal(exception_proposal, datetime.datetime.now())
            self.do_log("Proposta de exceção copiada com sucesso.")

    def on_add_click(self):
        if self.proposal.installments.is_using_placeholder():
            self.do_log("Preencha as vezes para adicionar uma proposta.")
        elif not validators.is_brl_valid(self.proposal.first_installment.get()):
            self.do_log("Preencha a entrada para adicionar uma proposta.")
        elif self.proposal.d_plus.is_using_placeholder():
            self.do_log("Preencha o prazo para pagamento para adicionar uma proposta.")
        else:
            installments = self.proposal.installments.get()
            if int(installments) > 1 and not validators.is_brl_valid(self.proposal.else_installment.get()):
                self.do_log("Preencha o valor de parcelas corretamente para adicionar uma proposta.")
            else:
                else_installment = self.proposal.else_installment.get()
                proposal = ep.ProposalWithDate(
                    int(installments),
                    converter.brl_to_float(self.proposal.first_installment.get()),
                    converter.brl_to_float(else_installment) if validators.is_brl_valid(else_installment) else None,
                    datetime.datetime.today() + datetime.timedelta(days=int(self.proposal.d_plus.get()))
                )
                self.proposals.insert_proposal(proposal)
                self.do_log("Proposta adicionada com sucesso.")


class EasyServiceApp:
    def __init__(self):
        self.database = database.DataBase()
        window = tk.Tk()
        self.agreement_control_window = AgreementControlWindow(self.database)
        self.about_window = about.AboutWindow()
        self.ep_historic_window = ExceptionProposalHistoricWindow()
        self.mie_window = EasyServiceWindow(window, self.database, self.agreement_control_window,
                                            self.ep_historic_window, self.about_window)
        self.mie_window.window.mainloop()


if __name__ == '__main__':
    EasyServiceApp()

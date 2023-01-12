from __future__ import annotations
import functools
import json
import os.path

from common import widgets, formater, converter, utils, regex, config, validators
from common import constants
from tkinter import ttk

import datetime
import threading
import tkinter as tk
import typing
import about
import agreement
import database
import exception_proposal as ep
import sv_ttk


class LabelAndWidget(ttk.Frame):
    def __init__(self, master, text: str, widget: typing.Union[
            typing.Type[ttk.Combobox], typing.Type[ttk.Entry], typing.Type[ttk.Spinbox]], **widget_config):
        super().__init__(master)
        self.label = ttk.Label(self, text=text)
        self.widget = widget(self, **widget_config)
        self.label.pack(anchor=tk.W)
        self.widget.pack(fill=tk.X)
        self.widget.bind("<FocusOut>", self._on_focus_out)

    def get(self):
        return self.widget.get()

    def validate(self):
        return self.widget.validate()

    def delete(self, first: typing.Union[str, int], last: typing.Union[str, int, None] = None):
        self.widget.delete(first, last)

    def config(self, *args, **kwargs):
        self.widget.config(*args, **kwargs)

    def insert(self, index: typing.Union[str, int], string: str):
        self.widget.insert(index, string)

    @staticmethod
    def _on_focus_out(event):
        if event.widget.get() == "":
            event.widget.state(["!invalid"])

    def set_text(self, string: str):
        self.delete(0, tk.END)
        self.insert(0, string)


Installments = functools.partial(LabelAndWidget, widget=ttk.Spinbox, text="Quantidade de parcelas",
                                 from_=1, to=24, increment=1)
Cpf = functools.partial(LabelAndWidget, widget=ttk.Entry, text="CPF")


class AgreementTreeView(widgets.BrowseTreeview):
    SORTING_TABLE = {"#1": lambda agreement_: agreement_.cpf, "#2": lambda agreement_: agreement_.first,
                     "#3": lambda agreement_: agreement_.create_date,
                     "#4": lambda agreement_: agreement_.get_due_date(), "#5": lambda agreement_: agreement_.payed,
                     "#6": lambda agreement_: agreement_.promise}

    def __init__(self, *args, **kwargs):
        cpf = "cpf"
        payed = "payed"
        value = "value"
        create_date = "create_date"
        due_date = "due_date"
        promise = "promise"
        columns = (cpf, value, create_date, due_date, payed, promise)
        super().__init__(
            *args,
            columns=columns,
            show="headings",
            **kwargs
        )
        for column in columns:
            self.column(column, minwidth=32, width=1, stretch=True)
        self.heading(cpf, text="CPF")
        self.heading(payed, text="Pago")
        self.heading(value, text="Valor")
        self.heading(create_date, text="Criação")
        self.heading(due_date, text="Vencimento")
        self.heading(promise, text="Promessa")
        self.context_menu_management.context_menu_selected.add_command(label="Copiar CPF", command=self.on_copy_cpf)
        self.own_bind("<Sort>", self.on_sort)

    def on_sort(self, column: str, reverse: bool):
        self.update_agreements(self.get_agreements(self.get_children()), sort_key=self.SORTING_TABLE[column],
                               reverse_sort=reverse)

    def on_copy_cpf(self):
        agreement_ = self.get_agreement(self.selection()[0])
        utils.copy_to_clipboard(self, formater.format_cpf(agreement_.cpf, False))

    def add_agreements(self, agreements: typing.Iterable[agreement.Agreement]):
        for agreement_ in agreements:
            self.add_agreement(agreement_)

    def add_agreement(self, agreement_):
        self.insert("", tk.END, iid=str(agreement_.id), values=(
            formater.format_cpf(agreement_.cpf, True), formater.format_brl(agreement_.value),
            agreement_.create_date.strftime("%d/%m/%Y"), agreement_.get_due_date().strftime("%d/%m/%Y"),
            converter.bool_to_str(agreement_.payed), converter.bool_to_str(agreement_.promise)))

    def get_agreements(self, keys: typing.Iterable[str]) -> typing.List[agreement.Agreement]:
        return [self.get_agreement(key) for key in keys]

    def get_agreement(self, key: str):
        item = self.item(key)
        cpf, value, create_date, due_date, payed, promise = item["values"]
        create_date = converter.parse_date(create_date)
        due_date = converter.parse_date(due_date)
        d_plus = (due_date - create_date).days
        agreement_ = agreement.Agreement(cpf, converter.brl_to_float(value), create_date, d_plus,
                                         converter.str_to_bool(payed), converter.str_to_bool(promise), int(key))
        return agreement_

    def update_agreements(self, agreements: typing.Iterable[agreement.Agreement], state: typing.Optional[int] = None,
                          sort_key: typing.Callable[[agreement.Agreement], typing.Any] = None,
                          reverse_sort: bool = False, cpf: typing.Optional[str] = None) -> None:
        self.delete(*self.get_children())
        if state is not None:
            agreements = list(filter(lambda agreement_: agreement_.get_state() == state, agreements))
        if cpf is not None:
            agreements = list(filter(lambda agreement_: cpf.replace(".", "") in formater.format_cpf(agreement_.cpf,
                                                                                                    False),
                                     agreements))
        if sort_key is not None:
            agreements.sort(key=sort_key, reverse=reverse_sort)
        self.add_agreements(agreements)


class Statistics(ttk.Label):
    def __init__(self, master, title: str):
        super().__init__(master)
        self.title = title
        self.pack(anchor=tk.W, padx=10)

    def set_title(self, value: typing.Optional[typing.Union[str, int]] = None):
        if value is None:
            self.config(text=f"{self.title}: N/A")
        else:
            self.config(text=f"{self.title}: {str(value)}")


class AgreementControlWindow:
    STATES = ("Pago", "Promessa", "Cancelado", "Atrasado", "Ativo")

    def __init__(self, database_: database.DataBase):
        self.top_level = tk.Toplevel()
        self.top_level.minsize(*config.MIN_RESOLUTION)
        self.top_level.geometry(f"{config.START_RESOLUTION[0]}x{config.START_RESOLUTION[1]}")
        self.top_level.withdraw()
        self.top_level.title("Controle de acordos")
        self.top_level.protocol("WM_DELETE_WINDOW", self.top_level.withdraw)
        self.top_level.iconbitmap("icon.ico")
        right_frame = ttk.LabelFrame(self.top_level, text="Estatísticas")
        right_frame.pack(fill=tk.Y, side=tk.RIGHT, padx=(5, 0))
        left_frame = ttk.LabelFrame(self.top_level, text="Histórico")
        left_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
        filters = ttk.LabelFrame(left_frame, text="Filtros")
        filters.pack(fill=tk.X, padx=10, pady=5)
        self.cpf = LabelAndWidget(filters, "CPF", ttk.Entry, width=15)
        self.cpf.pack(side=tk.LEFT, padx=5, pady=5)
        self.state = LabelAndWidget(filters, "Estado", ttk.Combobox, values=constants.STATES)
        self.state.pack(side=tk.LEFT, padx=5, pady=5)
        historic_frame = ttk.Frame(left_frame)
        historic_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        self.historic = AgreementTreeView(historic_frame)
        self.historic.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        historic_scroll_bar = ttk.Scrollbar(historic_frame, command=self.historic.yview)
        historic_scroll_bar.pack(fill=tk.Y, side=tk.LEFT)
        period_filter_label_frame = ttk.LabelFrame(right_frame, text="Filtro")
        period_filter_label_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        self.period = LabelAndWidget(period_filter_label_frame, "Período", ttk.Combobox,
                                     values=("Qualquer", "Hoje", "Esta semana", "Este mês"))
        self.period.pack(side=tk.LEFT, padx=5, pady=5)
        totals = ttk.LabelFrame(right_frame, text="Totais")
        totals.pack(fill=tk.BOTH, padx=5, pady=5, ipady=10, expand=True)
        self.total_negotiated = Statistics(totals, "Negociado")
        self.total_active = Statistics(totals, "Ativo")
        self.total_payed = Statistics(totals, "Pago")
        self.total_canceled = Statistics(totals, "Cancelado")
        self.total_overdue = Statistics(totals, "Atrasado")
        self.total_promise = Statistics(totals, "Promessa")
        quantities = ttk.LabelFrame(right_frame, text="Quantidades")
        quantities.pack(fill=tk.BOTH, padx=5, pady=5, ipady=10, expand=True)
        self.agreements_quantity = Statistics(quantities, "Acordos")
        self.agreements_active = Statistics(quantities, "Ativos")
        self.agreements_payed = Statistics(quantities, "Pagos")
        self.agreements_canceled = Statistics(quantities, "Cancelados")
        self.agreements_overdue = Statistics(quantities, "Atrasados")
        self.agreements_promise = Statistics(quantities, "Promessas")
        self.historic.config(yscrollcommand=historic_scroll_bar.set)
        self.state.widget.bind("<<ComboboxSelected>>", lambda _: self.on_select_state(database_))
        self.period.widget.bind("<<ComboboxSelected>>", lambda _: self.on_select_period(database_))
        self.update(database_.get_agreement_historic())
        self.historic.context_menu_management.context_menu_selected.add_command(
            label="Definir como pago",
            command=lambda: self.on_set_agreement_as_payed(database_)
        )
        self.historic.context_menu_management.context_menu_selected.add_command(
            label="Definir como promessa",
            command=lambda: self.on_set_agreement_as_promise(database_)
        )
        self.historic.context_menu_management.context_menu_selected.add_command(
            label="Deletar",
            command=lambda: self.on_delete_agreement(database_)
        )
        self.cpf.widget.bind("<KeyRelease>", lambda _: self.on_cpf_filter_change(database_))

    def on_set_agreement_as_promise(self, database_: database.DataBase):
        agreement_ = self.historic.get_agreement(self.historic.selection()[0])
        database_.set_agreement_as_promise(agreement_.id)
        self.update_agreements_with_context(database_)
        self.update_statistics(database_.get_agreement_historic())

    def on_set_agreement_as_payed(self, database_: database.DataBase):
        agreement_ = self.historic.get_agreement(self.historic.selection()[0])
        database_.set_agreement_as_payed(agreement_.id)
        self.update_agreements_with_context(database_)
        self.update_statistics(database_.get_agreement_historic())

    def on_select_state(self, database_: database.DataBase):
        self.update_agreements_with_context(database_)

    def on_cpf_filter_change(self, database_: database.DataBase):
        self.update_agreements_with_context(database_)

    def update_agreements_with_context(self, database_: database.DataBase):
        agreements = database_.get_agreement_historic()
        cpf = self.cpf.get() if self.cpf.validate() else None
        state = self.state.get()
        self.historic.update_agreements(agreements, self.STATES.index(state) if state in self.STATES else None,
                                        self.historic.SORTING_TABLE.get(self.historic.sorting_column),
                                        self.historic.reverse_sorting, cpf)

    def on_select_period(self, database_: database.DataBase):
        agreements = database_.get_agreement_historic()
        period = self.period.get()
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        yesterday = today - datetime.timedelta(days=1)
        first_week_day = today.replace(day=today.day - today.weekday())
        last_week_day = first_week_day + datetime.timedelta(days=7)
        first_month_day = today.replace(day=1)
        last_month_day = first_month_day + datetime.timedelta(days=30)
        filters = {"Hoje": lambda agreement_: yesterday < agreement_.create_date < tomorrow,
                   "Esta semana": lambda agreement_: first_week_day < agreement_.create_date < last_week_day,
                   "Este mês": lambda agreement_: first_month_day < agreement_.create_date < last_month_day}
        filter_ = filters.get(period)
        if filter_ is None:
            filtered_agreements = agreements
        else:
            filtered_agreements = list(filter(filter_, agreements))
        self.update_statistics(filtered_agreements)

    def update(self, agreements: typing.List[agreement.Agreement]):
        self.historic.update_agreements(agreements)
        self.update_statistics(agreements)

    def update_statistics(self, agreements: typing.List[agreement.Agreement]):
        def get_percentage(fraction: typing.Union[int, float], total: typing.Union[int, float]):
            return round(fraction / total * 100, 2)

        def get_agreements_sum(_agreements):
            return sum(map(lambda agreement_: agreement_.value, _agreements))

        def filter_agreements_by_state(_agreements, state: int):
            return tuple(filter(lambda agreement_: agreement_.get_state() == state, _agreements))

        def get_total_text(_agreements, total: typing.Union[int, float]):
            sum_ = get_agreements_sum(_agreements)
            return f"{formater.format_brl(sum_)} ({get_percentage(sum_, total)}%)"

        def get_quantity_text(_agreements, total: typing.Union[int, float]):
            len_ = len(_agreements)
            return f"{len_} ({get_percentage(len_, total)}%)"

        if agreements:
            active = filter_agreements_by_state(agreements, constants.ACTIVE)
            payed = filter_agreements_by_state(agreements, constants.PAYED)
            cancelled = filter_agreements_by_state(agreements, constants.CANCELED)
            overdue = filter_agreements_by_state(agreements, constants.OVERDUE)
            promise = filter_agreements_by_state(agreements, constants.PROMISE)
            agreements_sum = get_agreements_sum(agreements)
            agreements_quantity = len(agreements)
            self.total_negotiated.set_title(formater.format_brl(agreements_sum))
            self.total_active.set_title(get_total_text(active, agreements_sum))
            self.total_payed.set_title(get_total_text(payed, agreements_sum))
            self.total_canceled.set_title(get_total_text(cancelled, agreements_sum))
            self.total_overdue.set_title(get_total_text(overdue, agreements_sum))
            self.total_promise.set_title(get_total_text(promise, agreements_sum))
            self.agreements_quantity.set_title(agreements_quantity)
            self.agreements_active.set_title(get_quantity_text(active, agreements_quantity))
            self.agreements_payed.set_title(get_quantity_text(payed, agreements_quantity))
            self.agreements_canceled.set_title(get_quantity_text(cancelled, agreements_quantity))
            self.agreements_overdue.set_title(get_quantity_text(overdue, agreements_quantity))
            self.agreements_promise.set_title(get_quantity_text(promise, agreements_quantity))
        else:
            for statistic in (self.total_negotiated, self.total_active, self.total_payed, self.total_canceled,
                              self.total_overdue, self.total_promise, self.agreements_quantity, self.agreements_active,
                              self.agreements_payed, self.agreements_canceled, self.agreements_overdue,
                              self.agreements_promise):
                statistic.set_title()

    def on_delete_agreement(self, database_: database.DataBase):
        selection = self.historic.selection()[0]
        agreement_selected = self.historic.get_agreement(selection)
        self.historic.delete(selection)
        database_.delete_agreement(agreement_selected.id)
        self.update_statistics(database_.get_agreement_historic())


class ExceptionProposalHistoricTreeView(widgets.BrowseTreeview):
    def __init__(self, master):
        cpf = "cpf"
        value = "value"
        create_date = "create_date"
        due_date = "due_date"
        counter_proposal = "counter_proposal"
        installments = "installments"
        columns = (cpf, value, create_date, due_date, counter_proposal, installments)
        super().__init__(master, columns=columns, show="headings")
        for column in columns:
            self.column(column, minwidth=32, width=1, stretch=True)
        self.heading(cpf, text="CPF")
        self.heading(value, text="Valor")
        self.heading(create_date, text="Criação")
        self.heading(due_date, text="Vencimento")
        self.heading(counter_proposal, text="Contra")
        self.heading(installments, text="Parcelas")

        self.context_menu_management.context_menu_selected.add_command(label="Copiar", command=self.on_copy)

    def on_copy(self):
        item = self.item(self.selection()[0])
        cpf = formater.format_cpf(item["values"][0], False)
        return utils.copy_to_clipboard(self, cpf)

    def add_exception_proposal(self, proposal: ep.ExceptionProposalSent):
        values = formater.format_cpf(proposal.cpf), formater.format_brl(proposal.value), \
            proposal.create_date.strftime("%d/%m/%Y"), proposal.get_due_date().strftime("%d/%m/%Y"), \
            "" if proposal.counter_proposal is None else formater.format_brl(proposal.counter_proposal), \
            "" if proposal.installments is None else proposal.installments
        self.insert("", tk.END, iid=str(proposal.id), values=values)

    def get_exception_proposal(self, key: str):
        item = self.item(key)
        cpf, value, create_date, due_date, counter_proposal, installments = item["values"]
        create_date = converter.parse_date(create_date)
        due_date = converter.parse_date(due_date)
        d_plus = (due_date - create_date).days
        return ep.ExceptionProposalSent(formater.format_cpf(cpf, False), converter.brl_to_float(value),
                                        create_date, d_plus,
                                        None if counter_proposal == "" else converter.brl_to_float(counter_proposal),
                                        None if installments == "" else int(installments),
                                        int(key))


class ExceptionProposalHistoricWindow:
    def __init__(self, app, master):
        self.top_level = tk.Toplevel(master)
        self.top_level.withdraw()
        self.top_level.title("Histórico de propostas de exceção")
        self.top_level.minsize(*config.MIN_RESOLUTION)
        self.top_level.geometry(f"{config.START_RESOLUTION[0]}x{config.START_RESOLUTION[1]}")
        self.top_level.protocol("WM_DELETE_WINDOW", self.top_level.withdraw)
        self.top_level.iconbitmap("icon.ico")
        left_frame = ttk.LabelFrame(self.top_level, text="Editar")
        left_frame.pack(fill=tk.Y, side=tk.LEFT, padx=(0, 5))
        right_frame = ttk.LabelFrame(self.top_level, text="Histórico")
        right_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
        self.counter_proposal = LabelAndWidget(left_frame, "Contra-Proposta", ttk.Entry)
        self.counter_proposal.pack(fill=tk.X, padx=5)
        self.installments = Installments(left_frame)
        self.installments.pack(fill=tk.X, padx=5)
        self.confirm = widgets.Button(left_frame, text="Confirmar", command=lambda: self.on_confirm(app))
        self.confirm.pack(side=tk.BOTTOM, pady=10)
        self.historic = ExceptionProposalHistoricTreeView(right_frame)
        self.historic.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        exception_proposals = app.database.get_exception_proposals_historic()
        for exception_proposal in exception_proposals:
            self.historic.add_exception_proposal(exception_proposal)
        self.historic.context_menu_management.context_menu_selected.add_command(
            label="Remover",
            command=lambda: self.on_remove(app))

    def on_remove(self, app: EasyServiceApp):
        selected = self.historic.selection()[0]
        self.historic.delete(selected)
        app.database.delete_exception_proposal(int(selected))

    def on_confirm(self, app: EasyServiceApp):
        counter_proposal = self.counter_proposal.get()
        installments = self.installments.get()
        selected = self.historic.selection()
        if self.counter_proposal.validate() and self.installments.validate() and len(selected) > 0:
            selected = selected[0]
            cpf, value, create_date, due_date, _, _ = self.historic.item(selected)["values"]
            values_to_insert = (cpf, value, create_date, due_date, formater.format_brl(counter_proposal), installments)
            self.historic.item(selected, values=values_to_insert)
            app.database.edit_exception_proposal(int(selected), converter.brl_to_float(counter_proposal),
                                                 int(installments))


class ProposalsTreeView(widgets.BrowseTreeview):
    def __init__(self, master):
        installments = "installments"
        first_installment = "first_installment"
        else_installments = "else_installments"
        due_date = "due_date"
        total = "total"
        columns = (installments, first_installment, else_installments, due_date, total)
        super().__init__(master, columns=columns, show="headings")
        for column in columns:
            self.column(column, minwidth=32, width=1, stretch=True)
        self.heading(installments, text="Parcelas")
        self.heading(first_installment, text="Entrada")
        self.heading(else_installments, text="Valor de parc.")
        self.heading(due_date, text="Vencimento")
        self.heading(total, text="Total")
        self.context_menu_management.context_menu_selected.add_command(label="Remover", command=self.on_remove)
        self.context_menu_management.context_menu_selected.add_command(label="Copiar", command=self.on_copy)

    def on_remove(self):
        self.delete(self.selection()[0])

    def on_copy(self):
        proposal = self.get_proposal(self.selection()[0])
        utils.copy_to_clipboard(self, proposal.get_formatted_with_date())

    def insert_proposal(self, proposal: typing.Union[ep.InstallmentProposal, ep.Proposal],
                        key: typing.Optional[str] = None) -> str:
        proposal_dict = dict(installments="1",
                             first_installment=formater.format_brl(proposal.first),
                             due_date=proposal.due_date.strftime("%d/%m/%Y"))
        if isinstance(proposal, ep.InstallmentProposal):
            proposal_dict.update(dict(installments=str(proposal.installments),
                                      else_installments=formater.format_brl(proposal.rest),
                                      total=formater.format_brl(proposal.get_total())))
        return self.insert_values(key=key, **proposal_dict)

    def insert_values(self, installments: str, first_installment: str, due_date: str,
                      else_installments: str = "", total: str = "", key: typing.Optional[str] = None) -> str:

        if key:
            self.item(key, values=(installments, first_installment, else_installments, due_date, total))
            return key
        else:
            return self.insert("", tk.END, values=(installments, first_installment, else_installments, due_date, total))

    def get_proposal(self, key: str) -> typing.Union[ep.Proposal, ep.InstallmentProposal]:
        installments, first_installment, else_installments, date, total = self.item(key)["values"]
        if else_installments == "":
            return ep.Proposal(converter.brl_to_float(first_installment), converter.parse_date(date))
        else:
            return ep.InstallmentProposal(int(installments), converter.brl_to_float(first_installment),
                                          converter.brl_to_float(else_installments), converter.parse_date(date))

    def get_proposals(self) -> typing.List[ep.InstallmentProposal]:
        proposals = []
        for key in self.get_children():
            proposals.append(self.get_proposal(key))
        return proposals


class Proposal:
    def __init__(self, master: tk.Widget, brl_validate_command, installments_validate_command, date_validate_command):
        self.installments = Installments(master, **installments_validate_command)
        self.installments.pack(fill=tk.X, padx=5)
        self.first_installment = LabelAndWidget(master, "Entrada", ttk.Entry, **brl_validate_command)
        self.first_installment.pack(fill=tk.X, padx=5)
        self.else_installments = LabelAndWidget(master, "Valor de Parcelas", ttk.Entry, **brl_validate_command)
        self.else_installments.pack(fill=tk.X, padx=5)
        self.due_date = LabelAndWidget(master, "Data de Vencimento", ttk.Entry, **date_validate_command)
        self.due_date.pack(fill=tk.X, padx=5)

    def reset(self):
        for entry in (self.installments, self.first_installment, self.else_installments, self.due_date):
            entry.delete(0, tk.END)

    def get_proposal(self) -> typing.Union[ep.Proposal, ep.InstallmentProposal]:
        installments = int(self.installments.get())
        if installments > 1:
            return ep.InstallmentProposal(installments, converter.brl_to_float(self.first_installment.get()),
                                          converter.brl_to_float(self.else_installments.get()),
                                          datetime.datetime.strptime(self.due_date.get(), "%d/%m/%Y"))
        else:
            return ep.Proposal(converter.brl_to_float(self.first_installment.get()),
                               datetime.datetime.strptime(self.due_date.get(), "%d/%m/%Y"))

    def set_text(self, first_installment: str, due_date: str, installments="1", else_installments: str = ""):
        self.first_installment.set_text(first_installment)
        self.due_date.set_text(due_date)
        self.installments.set_text(installments)
        self.else_installments.set_text(else_installments)

    def set_due_date_with_d_plus(self, d_plus: int):
        date = datetime.date.today() + datetime.timedelta(days=d_plus)
        self.due_date.set_text(date.strftime("%d/%m/%Y"))


class DebitTreeView(widgets.Treeview):
    def __init__(self, master):
        product = "product"
        value = "value"
        delay_days = "delay_days"
        due_date = "due_date"
        columns = (product, value, delay_days, due_date)
        super().__init__(master, show="headings", columns=columns)
        for column in columns:
            self.column(column, minwidth=32, width=1, stretch=True)
        self.heading(product, text="Produto")
        self.heading(value, text="Valor")
        self.heading(delay_days, text="Dias em atraso")
        self.heading(due_date, text="Vencimento")

    def insert_debit(self, debit: ep.Debit):
        self.insert("", tk.END, values=(debit.product, formater.format_brl(debit.value), debit.get_delay_days(),
                                        debit.due_date.strftime("%d/%m/%Y")))


class EasyServiceWindow:
    def __init__(self, app, window: tk.Tk):
        self.window = window
        self.window.minsize(*config.MIN_RESOLUTION)
        self.window.geometry(f"{config.START_RESOLUTION[0]}x{config.START_RESOLUTION[1]}")
        self.window.protocol("WM_DELETE_WINDOW", self.on_delete_window)
        self.window.iconbitmap("icon.ico")
        self.menu = tk.Menu(self.window)
        tools_menu = tk.Menu(tearoff=False)
        tools_menu.add_command(label="Histórico de propostas de exceção",
                               command=app.ep_historic.top_level.deiconify)
        tools_menu.add_command(label="Controle de acordos", command=app.agreement_control.top_level.deiconify)
        themes_menu = tk.Menu(tearoff=False)
        themes_menu.add_command(label="Claro", command=sv_ttk.use_light_theme)
        themes_menu.add_command(label="Escuro", command=sv_ttk.use_dark_theme)
        self.menu.add_cascade(label="Ferramentas", menu=tools_menu)
        self.menu.add_cascade(label="Temas", menu=themes_menu)
        self.menu.add_command(label="Sobre", command=app.about.top_level.deiconify)
        self.window.title("Atendimento fácil")
        self.window.configure(menu=self.menu)
        left_notebook = ttk.Notebook()
        top_frame = ttk.Frame()
        bottom_frame = ttk.Frame()
        self.log = ttk.Label(anchor=tk.W, padding=5)
        self.log.pack(side=tk.BOTTOM, fill=tk.X)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH)
        left_notebook.pack(side=tk.LEFT, fill=tk.BOTH)
        top_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=5)
        data_frame = ttk.Frame(left_notebook)
        costumer_label_frame = ttk.LabelFrame(data_frame, text="Sobre o cliente")
        costumer_label_frame.pack(padx=5, pady=5, expand=True, fill=tk.BOTH)
        self.cpf = Cpf(costumer_label_frame, **app.new_validate_command(regex.CPF.fullmatch))
        self.cpf.pack(fill=tk.X, padx=5)
        self.phone = LabelAndWidget(costumer_label_frame, "Telefone", ttk.Entry,
                                    **app.new_validate_command(regex.PHONE.fullmatch))
        self.phone.pack(fill=tk.X, padx=5)
        self.email = LabelAndWidget(costumer_label_frame, "E-mail", ttk.Entry,
                                    **app.new_validate_command(regex.EMAIL.fullmatch))
        self.email.pack(fill=tk.X, padx=5)
        debit_label_frame = ttk.LabelFrame(data_frame, text="Sobre o débito")
        debit_label_frame.pack(padx=5, pady=5, expand=True, fill=tk.BOTH)
        self.product = LabelAndWidget(debit_label_frame, "Produto", ttk.Combobox, values=constants.PRODUCTS,
                                      **app.new_validate_command(regex.PRODUCT.fullmatch))
        self.product.pack(fill=tk.X, padx=5)
        self.delay_days = LabelAndWidget(debit_label_frame, "Dias em atraso", ttk.Spinbox, from_=1, to=999,
                                         **app.new_validate_command(regex.DAYS_IN_ARREARS.fullmatch))
        self.delay_days.pack(fill=tk.X, padx=5)
        self.main_value = LabelAndWidget(debit_label_frame, "Valor Principal", ttk.Entry,
                                         **app.brl_validate_command)
        self.main_value.pack(fill=tk.X, padx=5)
        self.promotion = LabelAndWidget(debit_label_frame, "Valor com Desconto", ttk.Entry,
                                        **app.brl_validate_command)
        self.promotion.pack(fill=tk.X, padx=5)
        left_notebook.add(data_frame)
        left_notebook.tab(0, text="Dados")
        self.proposals = ProposalsTreeView(top_frame)
        self.proposals.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refusal_reason = LabelAndWidget(top_frame, "Motivo de Recusa", ttk.Combobox,
                                             values=tuple(constants.REFUSAL_REASONS.keys()))
        self.refusal_reason.pack(side=tk.RIGHT, fill=tk.X, anchor=tk.SE, padx=(0, 10), pady=(0, 5))
        self.agreement = widgets.Button(
            bottom_frame, text="Acordo",
            command=lambda: self.validate_agreement(lambda agreement_: self.on_agreement(app, agreement_)))
        self.agreement.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0), pady=5)
        self.copy_agreement = widgets.Button(
            bottom_frame, text="⋯", hover_text="Copiar texto de acordo",
            command=lambda: self.validate_agreement(self.on_copy_agreement))
        self.copy_agreement.pack(side=tk.LEFT, padx=(2, 0))
        self.refusal = widgets.Button(bottom_frame, text="Recusa", command=self.on_refusal)
        self.refusal.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10), pady=5)
        self.exception_proposal = widgets.Button(
            bottom_frame, text="Proposta de exceção",
            command=lambda: self.validate_exception_proposal(
                lambda ep_: self.on_exception_proposal(app, ep_)))
        self.exception_proposal.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.copy_exception_proposal = widgets.Button(
            bottom_frame, text="⋯", hover_text="Copiar texto de proposta de exceção",
            command=lambda: self.validate_exception_proposal(self.on_copy_exception_proposal))
        self.copy_exception_proposal.pack(side=tk.LEFT, padx=(2, 0))
        self.next_costumer = widgets.Button(bottom_frame, text="Próximo cliente", command=lambda: self.reset())
        self.next_costumer.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 5), pady=5)
        negotiation_frame = ttk.Frame(left_notebook)
        proposal_label_frame = ttk.LabelFrame(negotiation_frame, text="Proposta")
        proposal_label_frame.pack(padx=5, pady=5, expand=True, fill=tk.BOTH)
        proposal_options = ttk.Frame(proposal_label_frame)
        self.proposal = Proposal(proposal_label_frame, app.brl_validate_command, app.installments_validate_command,
                                 app.new_validate_command(validators.validate_date))
        self.add = widgets.Button(proposal_options, hover_text="Adicionar", text="+", command=self.on_add_click)
        self.add.grid(row=0, column=0)
        proposal_options.grid_columnconfigure(0, weight=20)
        proposal_options.pack(side=tk.BOTTOM, anchor=tk.W, padx=5, pady=5)
        left_notebook.add(negotiation_frame)
        left_notebook.tab(1, text="Negociação")
        self.proposal.installments.widget.bind("<Return>", self.on_proposal_property_edit)
        self.proposal.first_installment.widget.bind("<Return>", self.on_proposal_property_edit)
        self.proposal.else_installments.widget.bind("<Return>", self.on_proposal_property_edit)
        self.proposal.due_date.widget.bind("<Return>", self.on_proposal_property_edit)
        self.proposals.own_bind("<Select>", self.on_select_proposal)
        self.proposals.own_bind("<Unselect>", lambda _: self.on_unselect_proposal())
        self.proposal.set_due_date_with_d_plus(1)
        if os.path.exists("theme.json"):
            sv_ttk.set_theme(self.load_saved_theme())
        else:
            sv_ttk.use_light_theme()

    def on_delete_window(self):
        with open("theme.json", "w") as file:
            json.dump(dict(theme=sv_ttk.get_theme()), file)
        self.window.destroy()

    @staticmethod
    def load_saved_theme():
        with open("theme.json", "r") as file:
            content = json.load(file)
            return content["theme"]

    def do_log(self, log: str):
        self.log.config(text=log)
        timer = threading.Timer(3, lambda: self.log.config(text=""))
        timer.start()

    def reset(self):
        for entry in (self.cpf, self.phone, self.email, self.delay_days, self.main_value, self.promotion,
                      self.refusal_reason):
            entry.delete(0, tk.END)
        self.proposal.reset()
        self.proposals.delete(*self.proposals.get_children())
        self.proposal.set_due_date_with_d_plus(1)
        self.window.focus_force()

    def on_select_proposal(self, key: str):
        proposal = self.proposals.get_proposal(key)
        if isinstance(proposal, ep.InstallmentProposal):
            self.proposal.set_text(formater.format_brl(proposal.first, False), proposal.due_date.strftime("%d/%m/%Y"),
                                   str(proposal.installments), formater.format_brl(proposal.rest, False))
        else:
            self.proposal.set_text(formater.format_brl(proposal.first, False), proposal.due_date.strftime("%d/%m/%Y"))

    def on_unselect_proposal(self):
        self.proposal.reset()

    def on_proposal_property_edit(self, event):
        current_proposal = self.proposals.selection()[0]
        if current_proposal:
            if event.widget.validate():
                self.proposals.insert_proposal(self.proposal.get_proposal(), current_proposal)

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

    def validate_agreement(self, callback: typing.Callable[[ep.InstallmentProposal], typing.Any]):
        selection = self.proposals.selection()
        if len(selection) == 0:
            self.do_log("Selecione a proposta que você fez o acordo.")
        elif not self.cpf.validate():
            self.do_log("Preencha o CPF corretamente para fazer um acordo.")
        elif not self.product.validate():
            self.do_log("Preencha o produto corretamente para fazer um acordo.")
        else:
            proposal = self.proposals.get_proposal(selection[0])
            callback(proposal)

    def on_agreement(self, app, proposal: typing.Union[ep.InstallmentProposal, ep.Proposal]):
        utils.copy_to_clipboard(self.window, proposal.get_formatted_to_register(self.product.get()))
        agreement_ = proposal.to_agreement(self.cpf.get())
        app.database.add_agreement(agreement_)
        app.agreement_control.historic.add_agreement(agreement_)
        agreements = app.database.get_agreement_historic()
        app.agreement_control.update_agreements_with_context(app.database)
        app.agreement_control.update_statistics(agreements)
        self.do_log("Acordo copiado e salvo com sucesso.")

    def on_copy_agreement(self, proposal: typing.Union[ep.InstallmentProposal, ep.Proposal]):
        utils.copy_to_clipboard(self.window, proposal.get_formatted_with_date())
        self.do_log("Acordo copiado com sucesso.")

    def validate_exception_proposal(self, callback: typing.Callable[[ep.ExceptionProposal], typing.Any]):
        selection = self.proposals.selection()
        if not self.cpf.validate():
            self.do_log("Preencha o CPF corretamente para fazer uma proposta de exceção.")
        elif not self.phone.validate():
            self.do_log("Preencha o telefone corretamente para fazer uma proposta de exceção.")
        elif not self.email.validate():
            self.do_log("Preencha o email corretamente para fazer uma proposta de exceção.")
        elif not self.product.validate():
            self.do_log("Preencha o produto corretamente para fazer uma proposta de exceção.")
        elif not self.delay_days.validate():
            self.do_log("Preencha os dias em atraso corretamente para fazer uma proposta de exceção.")
        elif not self.main_value.validate():
            self.do_log("Preencha o valor principal corretamente para fazer uma proposta de exceção.")
        elif not self.promotion.validate():
            self.do_log("Preencha o valor com desconto corretamente para fazer uma proposta de exceção.")
        elif len(selection) == 0:
            self.do_log("Selecione a proposta feita pelo cliente.")
        else:
            exception_proposal = ep.ExceptionProposal(
                self.cpf.get(),
                converter.brl_to_float(self.main_value.get()),
                converter.brl_to_float(self.promotion.get()),
                self.proposals.get_proposal(selection[0]),
                self.email.get(),
                int(self.delay_days.get()),
                self.product.get(),
                self.phone.get()
            )
            callback(exception_proposal)

    def on_exception_proposal(self, app, exception_proposal: ep.ExceptionProposal):
        utils.copy_to_clipboard(self.window, exception_proposal.get_text_to_copy())
        exception_proposal_sent = exception_proposal.to_exception_proposal_sent()
        app.database.add_exception_proposal(exception_proposal_sent)
        app.ep_historic.historic.add_exception_proposal(exception_proposal_sent)
        self.do_log("Proposta de exceção salva e copiada com sucesso.")

    def on_copy_exception_proposal(self, exception_proposal: ep.ExceptionProposal):
        utils.copy_to_clipboard(self.window, exception_proposal.get_text_to_copy())
        self.do_log("Proposta de exceção copiada com sucesso.")

    def on_add_click(self):
        if not self.proposal.installments.validate():
            self.do_log("Preencha a Quantidade de Parcelas corretamente para adicionar uma proposta.")
        elif not self.proposal.first_installment.validate():
            self.do_log("Preencha a Entrada corretamente para adicionar uma proposta.")
        else:
            installments = self.proposal.installments.get()
            if int(installments) > 1 and not self.proposal.else_installments.validate():
                self.do_log("Preencha o valor de parcelas corretamente para adicionar uma proposta.")
            else:
                self.proposals.insert_proposal(self.proposal.get_proposal())
                self.do_log("Proposta adicionada com sucesso.")
        if len(self.proposals.get_children()) >= 2:
            self.proposal.set_due_date_with_d_plus(3)


class EasyServiceApp:
    def __init__(self):
        self.database = database.DataBase()
        self.window = tk.Tk()
        self.brl_validate_command = self.new_validate_command(regex.BRL.fullmatch)
        self.installments_validate_command = self.new_validate_command(validators.validate_installments)
        self.agreement_control = AgreementControlWindow(self.database)
        self.about = about.AboutWindow()
        self.ep_historic = ExceptionProposalHistoricWindow(self, self.window)
        self.easy_service = EasyServiceWindow(self, self.window)
        self.window.mainloop()

    def new_validate_command(self, validate_command: typing.Union[typing.Callable[[str], bool], str, typing.Pattern]):
        return dict(validate="focusout",
                    validatecommand=(self.window.register(lambda string: bool(validate_command(string))), "%P"))


if __name__ == '__main__':
    EasyServiceApp()

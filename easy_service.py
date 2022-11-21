import datetime
import threading
import tkinter as tk
from tkinter import ttk

import typing

import about
import agreement
import database
from common import widgets, colors, formater, validators, converter, utils, regex, config
from common import constants
import exception_proposal as ep


class BRLEntry(widgets.Entry):
    validate_command = ""

    def __init__(self, *args, placeholder: str, **kwargs):
        super().__init__(*args, placeholder=placeholder, **kwargs)
        if self.validate_command == "":
            self.validate_command = (self.register(lambda text: bool(regex.MAY_BE_BRL.fullmatch(text))), "%P")
        self.placeholder_config(validatecommand=self.validate_command, validate="key")


class Installments(widgets.Spinbox):
    validate_command_table: typing.Optional[dict] = None

    def __init__(self, *args, placeholder: str, **kwargs):
        product = tk.StringVar(name="product")
        super(Installments, self).__init__(*args, placeholder=placeholder, **kwargs)
        product.trace("w", lambda *_: self.on_product_change(product))

    def on_product_change(self, product: tk.StringVar):
        product = product.get()
        was_with_placeholder = self.is_using_placeholder()
        if self.validate_command_table is None:
            vc_18 = (self.register(lambda text: validators.is_int_text_valid_for_input(text, 18, 1)), "%P")
            vc_24 = (self.register(lambda text: validators.is_int_text_valid_for_input(text, 24, 1)), "%P")
            self.validate_command_table = {constants.CCRCFI: vc_18, constants.EPCFI: vc_18, constants.CBRCREL: vc_24}
        vc = self.validate_command_table[product]
        self.placeholder_config(validatecommand=vc, validate="key", from_=1, to=constants.MAX_INSTALMENTS[product])
        self.set_placeholder(was_with_placeholder)


class AgreementTreeView(widgets.BrowseTreeview):
    SORTING_TABLE = {"#1": lambda agreement_: agreement_.cpf, "#2": lambda agreement_: agreement_.value,
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
            self.column(column, minwidth=50, width=1, stretch=True)
        self.heading(cpf, text="CPF")
        self.heading(payed, text="Pago")
        self.heading(value, text="Valor")
        self.heading(create_date, text="Data de criação")
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
        create_date = converter.date_str_to_date(create_date)
        due_date = converter.date_str_to_date(due_date)
        d_plus = (due_date - create_date).days
        agreement_ = agreement.Agreement(cpf, converter.brl_to_float(value), create_date, d_plus,
                                         converter.str_to_bool(payed), converter.str_to_bool(promise), int(key))
        return agreement_

    def update_agreements(self, agreements: typing.Iterable[agreement.Agreement], state: typing.Optional[int] = None,
                          sort_key: typing.Callable[[agreement.Agreement], typing.Any] = None,
                          reverse_sort: bool = False) -> None:
        self.delete(*self.get_children())
        if state is not None:
            agreements = list(filter(lambda agreement_: agreement_.get_state() == state, agreements))
        if sort_key is not None:
            agreements.sort(key=sort_key, reverse=reverse_sort)
        self.add_agreements(agreements)


class AgreementControlWindow:
    STATES = ("Pago", "Promessa", "Cancelado", "Atrasado", "Ativo")

    def __init__(self, database_: database.DataBase):
        self.top_level = tk.Toplevel()
        self.top_level.minsize(*config.MIN_RESOLUTION)
        self.top_level.withdraw()
        self.top_level.title("Controle de acordos")
        self.top_level.protocol("WM_DELETE_WINDOW", self.top_level.withdraw)
        right_frame = ttk.LabelFrame(self.top_level, text="Estatísticas")
        right_frame.pack(fill=tk.Y, side=tk.RIGHT, padx=(5, 0))
        left_frame = ttk.LabelFrame(self.top_level, text="Histórico")
        left_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
        state_label_frame = ttk.LabelFrame(left_frame, text="Filtrar por estado")
        state_label_frame.pack(padx=10, pady=5, anchor=tk.W)
        self.state = ttk.Combobox(state_label_frame, values=("Nenhum", "Pago", "Promessa", "Cancelado", "Atrasado",
                                                             "Ativo"))
        self.state.pack(padx=5, pady=5)
        self.historic = AgreementTreeView(left_frame)
        self.historic.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.total_negotiated = tk.Label(right_frame)
        self.total_negotiated.pack(anchor=tk.W)
        self.total_active = tk.Label(right_frame)
        self.total_active.pack(anchor=tk.W)
        self.total_payed = tk.Label(right_frame)
        self.total_payed.pack(anchor=tk.W)
        self.total_canceled = tk.Label(right_frame)
        self.total_canceled.pack(anchor=tk.W)
        self.total_overdue = tk.Label(right_frame)
        self.total_overdue.pack(anchor=tk.W)
        self.total_promise = tk.Label(right_frame)
        self.total_promise.pack(anchor=tk.W)
        self.agreements_quantity = tk.Label(right_frame)
        self.agreements_quantity.pack(anchor=tk.W)
        self.agreements_active = tk.Label(right_frame)
        self.agreements_active.pack(anchor=tk.W)
        self.agreements_payed = tk.Label(right_frame)
        self.agreements_payed.pack(anchor=tk.W)
        self.agreements_canceled = tk.Label(right_frame)
        self.agreements_canceled.pack(anchor=tk.W)
        self.agreements_overdue = tk.Label(right_frame)
        self.agreements_overdue.pack(anchor=tk.W)
        self.agreements_promise = tk.Label(right_frame)
        self.agreements_promise.pack(anchor=tk.W)
        period_filter_label_frame = ttk.LabelFrame(right_frame, text="Filtrar por período")
        period_filter_label_frame.pack(padx=5, pady=10, side=tk.BOTTOM)
        self.period = ttk.Combobox(period_filter_label_frame, values=("Hoje", "Esta semana", "Este mês"))
        self.period.pack(padx=5, pady=5)
        self.state.bind("<<ComboboxSelected>>", lambda _: self.on_select_state(database_))
        self.period.bind("<<ComboboxSelected>>", lambda _: self.on_select_period(database_))
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

    def on_set_agreement_as_promise(self, database_: database.DataBase):
        agreement_ = self.historic.get_agreement(self.historic.selection()[0])
        database_.set_agreement_as_promise(agreement_.id)
        self.update_agreements_with_context(database_)

    def on_set_agreement_as_payed(self, database_: database.DataBase):
        agreement_ = self.historic.get_agreement(self.historic.selection()[0])
        database_.set_agreement_as_payed(agreement_.id)
        self.update_agreements_with_context(database_)

    def on_select_state(self, database_: database.DataBase):
        self.update_agreements_with_context(database_)

    def update_agreements_with_context(self, database_: database.DataBase):
        agreements = database_.get_agreement_historic()
        state = self.state.get()
        self.historic.update_agreements(agreements, self.STATES.index(state) if state in self.STATES else None,
                                        self.historic.SORTING_TABLE.get(self.historic.sorting_column),
                                        self.historic.reverse_sorting)
        self.update_statistics(agreements)

    def on_select_period(self, database_: database.DataBase):
        agreements = database_.get_agreement_historic()
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

        def get_total_text(_agreements, title: str, total: typing.Union[int, float]):
            sum_ = get_agreements_sum(_agreements)
            return f"Total {title}: {formater.format_brl(sum_)} ({get_percentage(sum_, total)}%)"

        def get_quantity_text(_agreements, title: str, total: typing.Union[int, float]):
            len_ = len(_agreements)
            return f"Acordos {title}: {len_} ({get_percentage(len_, total)}%)"

        if agreements:
            active = filter_agreements_by_state(agreements, constants.ACTIVE)
            payed = filter_agreements_by_state(agreements, constants.PAYED)
            cancelled = filter_agreements_by_state(agreements, constants.CANCELED)
            overdue = filter_agreements_by_state(agreements, constants.OVERDUE)
            promise = filter_agreements_by_state(agreements, constants.PROMISE)
            agreements_sum = get_agreements_sum(agreements)
            agreements_quantity = len(agreements)
            self.total_negotiated.config(text=f"Total negociado: {formater.format_brl(agreements_sum)}")
            self.total_active.config(text=get_total_text(active, "ativo", agreements_sum))
            self.total_payed.config(text=get_total_text(payed, "pago", agreements_sum))
            self.total_canceled.config(text=get_total_text(cancelled, "cancelado", agreements_sum))
            self.total_overdue.config(text=get_total_text(overdue, "atrasado", agreements_sum))
            self.total_promise.config(text=get_total_text(promise, "com promessa", agreements_sum))
            self.agreements_quantity.config(text=f"Acordos: {agreements_quantity}")
            self.agreements_active.config(text=get_quantity_text(active, "ativos", agreements_quantity))
            self.agreements_payed.config(text=get_quantity_text(payed, "pagos", agreements_quantity))
            self.agreements_canceled.config(text=get_quantity_text(cancelled, "cancelados", agreements_quantity))
            self.agreements_overdue.config(text=get_quantity_text(overdue, "atrasados", agreements_quantity))
            self.agreements_promise.config(text=get_quantity_text(promise, "com promessa", agreements_quantity))
        else:
            self.total_negotiated.config(text="Total negociado: N/A")
            self.total_active.config(text="Total ativo: N/A")
            self.total_payed.config(text="Total pago: N/A")
            self.total_canceled.config(text="Total cancelado: N/A")
            self.total_overdue.config(text="Total atrasado: N/A")
            self.total_promise.config(text="Total com promessa: N/A")
            self.agreements_quantity.config(text="Acordos: N/A")
            self.agreements_active.config(text="Acordos ativos: N/A")
            self.agreements_payed.config(text="Acordos pagos: N/A")
            self.agreements_canceled.config(text="Acordos cancelados: N/A")
            self.agreements_overdue.config(text="Acordos atrasados: N/A")
            self.agreements_promise.config(text="Acordos com promessa: N/A")

    def on_delete_agreement(self, database_: database.DataBase):
        selection = self.historic.selection()[0]
        agreement_selected = self.historic.get_agreement(selection)
        self.historic.delete(selection)
        database_.delete_agreement(agreement_selected.id)
        self.update_statistics(database_.get_agreement_historic())


class ExceptionProposalHistoricTreeView(widgets.BrowseTreeview):
    def __init__(self, *args, **kwargs):
        cpf = "cpf"
        value = "value"
        create_date = "create_date"
        due_date = "due_date"
        counter_proposal = "counter_proposal"
        installments = "installments"
        columns = (cpf, value, create_date, due_date, counter_proposal, installments)
        super().__init__(
            *args,
            columns=columns,
            show="headings",
            **kwargs
        )
        for column in columns:
            self.column(column, minwidth=50, width=1, stretch=True)
        self.heading(cpf, text="CPF")
        self.heading(value, text="Valor")
        self.heading(create_date, text="Data de criação")
        self.heading(due_date, text="Vencimento")
        self.heading(counter_proposal, text="Contra-Proposta")
        self.heading(installments, text="Quantidade de parcelas")

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
        create_date = converter.date_str_to_date(create_date)
        due_date = converter.date_str_to_date(due_date)
        d_plus = (due_date - create_date).days
        return ep.ExceptionProposalSent(formater.format_cpf(cpf, False), converter.brl_to_float(value),
                                        create_date, d_plus,
                                        None if counter_proposal == "" else converter.brl_to_float(counter_proposal),
                                        None if installments == "" else int(installments),
                                        int(item["iid"]))


class ExceptionProposalHistoricWindow:
    def __init__(self, master, database_: database.DataBase):
        self.top_level = tk.Toplevel(master)
        self.top_level.withdraw()
        self.top_level.title("Histórico de propostas de exceção")
        self.top_level.minsize(*config.MIN_RESOLUTION)
        self.top_level.protocol("WM_DELETE_WINDOW", self.top_level.withdraw)
        left_frame = ttk.LabelFrame(self.top_level, text="Editar")
        left_frame.pack(fill=tk.Y, side=tk.LEFT, padx=(0, 5))
        right_frame = ttk.LabelFrame(self.top_level, text="Histórico")
        right_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
        self.counter_proposal = BRLEntry(left_frame, placeholder="Contra-Proposta", hover_text="Contra-Proposta")
        self.counter_proposal.pack(fill=tk.X, padx=5, pady=5)
        self.installments = Installments(left_frame, placeholder="Parcelas", hover_text="Parcelas")
        self.installments.pack(fill=tk.X, padx=5)
        self.confirm = widgets.Button(left_frame, text="Confirmar", command=lambda: self.on_confirm(database_))
        self.confirm.pack(side=tk.BOTTOM, pady=10)
        self.historic = ExceptionProposalHistoricTreeView(right_frame)
        self.historic.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        exception_proposals = database_.get_exception_proposals_historic()
        for exception_proposal in exception_proposals:
            self.historic.add_exception_proposal(exception_proposal)
        self.historic.context_menu_management.context_menu_selected.add_command(
            label="Remover",
            command=lambda: self.on_remove(database_))

    def on_remove(self, database_: database.DataBase):
        selected = self.historic.selection()[0]
        self.historic.delete(selected)
        database_.delete_exception_proposal(int(selected))

    def on_confirm(self, database_: database.DataBase):
        counter_proposal = self.counter_proposal.get()
        installments = self.installments.get()
        selected = self.historic.selection()
        if regex.CAN_BE_BRL.fullmatch(counter_proposal) and not self.installments.is_using_placeholder() \
                and len(selected) > 0:
            selected = selected[0]
            cpf, value, create_date, due_date, _, _ = self.historic.item(selected[0])["values"]
            values_to_insert = (cpf, value, create_date, due_date, formater.format_brl(counter_proposal), installments)
            self.historic.item(selected, values=values_to_insert)
            database_.edit_exception_proposal(int(selected), converter.brl_to_float(counter_proposal),
                                              int(installments))


class ProposalsTreeView(widgets.BrowseTreeview):
    def __init__(self, master):
        installments = "installments"
        first_installment = "first_installment"
        else_installments = "else_installments"
        due_date = "due_date"
        total = "total"
        columns = (installments, first_installment, else_installments, due_date, total)
        super().__init__(
            master,
            columns=columns,
            show="headings"
        )
        for column in columns:
            self.column(column, minwidth=100, width=1, stretch=True)
        self.heading(installments, text="Quantidade de parcelas")
        self.heading(first_installment, text="Entrada")
        self.heading(else_installments, text="Valor de parcelas")
        self.heading(due_date, text="Vencimento")
        self.heading(total, text="Total")
        self.context_menu_management.context_menu_selected.add_command(label="Remover", command=self.on_remove)
        self.context_menu_management.context_menu_selected.add_command(label="Copiar", command=self.on_copy)

    def on_remove(self):
        self.delete(self.selection()[0])

    def on_copy(self):
        proposal = self.get_proposal(self.selection()[0])
        utils.copy_to_clipboard(self, proposal.get_formatted_with_date())

    def insert_proposal(self, proposal: ep.ProposalWithDate, key: typing.Optional[str] = None) -> str:
        if proposal.is_installments():
            values = proposal.installments, formater.format_brl(proposal.first_installment), \
                     formater.format_brl(proposal.else_installments), proposal.due_date.strftime("%d/%m/%Y"), \
                     formater.format_brl(proposal.get_total())
        else:
            values = proposal.installments, formater.format_brl(proposal.first_installment), \
                     "", proposal.due_date.strftime("%d/%m/%Y"), ""
        if key:
            self.item(key, values=values)
            return key
        else:
            return self.insert("", tk.END, values=values)

    def get_proposal(self, key: str) -> ep.ProposalWithDate:
        installments, first_installment, else_installments, date, total = self.item(key)["values"]
        return ep.ProposalWithDate(
            int(installments),
            converter.brl_to_float(first_installment),
            converter.brl_to_float(else_installments) if regex.CAN_BE_BRL.match(else_installments) else None,
            converter.date_str_to_date(date)
        )

    def get_proposals(self) -> typing.List[ep.ProposalWithDate]:
        proposals = []
        for key in self.get_children():
            proposals.append(self.get_proposal(key))
        return proposals


class Proposal:
    def __init__(self, master: tk.Widget, **kwargs):
        self.installments = Installments(master, placeholder="Quantidade de parcelas",
                                         hover_text="Quantidade de parcelas")
        self.installments.pack(fill=tk.X, pady=5, padx=5)
        self.first_installment = BRLEntry(master, placeholder="Entrada", hover_text="Entrada")
        self.first_installment.pack(fill=tk.X, pady=(0, 5), padx=5)
        self.else_installments = BRLEntry(master, placeholder="Valor de parcelas", hover_text="Valor de parcelas")
        self.else_installments.pack(fill=tk.X, pady=(0, 5), padx=5)

    def get_proposal(self) -> ep.Proposal:
        else_installment = self.else_installments.get()
        return ep.Proposal(
            int(self.installments.get()),
            converter.brl_to_float(self.first_installment.get()),
            converter.brl_to_float(else_installment) if regex.CAN_BE_BRL.match(else_installment) else None,
        )

    def reset(self):
        for object_ in (self.installments, self.first_installment, self.else_installments):
            object_.set_placeholder(True)


class ProposalWithDate(Proposal):
    def __init__(self, master, d_plus_vc, d_plus_max: int, **kwargs):
        super().__init__(master, **kwargs)
        self.d_plus = widgets.Spinbox(
            master,
            hover_text="Prazo para pagamento em dias",
            placeholder="Prazo para pagamento em dias",
            validate="key",
            validatecommand=d_plus_vc,
            from_=1,
            to=d_plus_max
        )
        self.d_plus.pack(fill=tk.X, padx=5)

    def reset(self):
        super().reset()
        self.d_plus.set_placeholder(True)

    def get_proposal_with_date(self) -> ep.ProposalWithDate:
        else_installment = self.else_installments.get()
        return ep.ProposalWithDate(
            int(self.installments.get()),
            converter.brl_to_float(self.first_installment.get()),
            converter.brl_to_float(else_installment) if regex.CAN_BE_BRL.match(else_installment) else None,
            datetime.date.today() + datetime.timedelta(days=int(self.d_plus.get()))
        )


class DebitTreeView(widgets.Treeview):
    def __init__(self, master):
        product = "product"
        value = "value"
        delay_days = "delay_days"
        due_date = "due_date"
        columns = (product, value, delay_days, due_date)
        super().__init__(master, show="headings", columns=columns)
        for column in columns:
            self.column(column, minwidth=100, width=1, stretch=True)
        self.heading(product, text="Produto")
        self.heading(value, text="Valor")
        self.heading(delay_days, text="Dias em atraso")
        self.heading(due_date, text="Vencimento")

    def insert_debit(self, debit: ep.Debit):
        self.insert("", tk.END, values=(debit.product, formater.format_brl(debit.value), debit.get_delay_days(),
                                        debit.due_date.strftime("%d/%m/%Y")))


class EasyServiceWindow:
    def __init__(self, window, database_, agreement_control_window, ep_historic_window, about_window):
        self.window = window
        self.window.minsize(*config.MIN_RESOLUTION)
        product_variable = tk.StringVar(window, name="product")
        d_plus_3_vc = self.new_vc(lambda text: validators.is_int_text_valid_for_input(text, 3, 1))
        d_plus_5_vc = self.new_vc(lambda text: validators.is_int_text_valid_for_input(text, 5, 1))
        self.menu = tk.Menu(self.window)
        tools_menu = tk.Menu(tearoff=False)
        tools_menu.add_command(
            label="Histórico de propostas de exceção",
            command=ep_historic_window.top_level.deiconify
        )
        tools_menu.add_command(
            label="Controle de acordos",
            command=agreement_control_window.top_level.deiconify
        )
        self.menu.add_cascade(label="Ferramentas", menu=tools_menu)
        self.menu.add_command(label="Sobre", command=about_window.top_level.deiconify)
        self.window.title("Atendimento fácil")
        self.window.configure(menu=self.menu)
        left_frame = tk.Frame()
        top_notebook = ttk.Notebook()
        bottom_frame = tk.Frame()
        self.log = tk.Label(background=colors.WHITE, anchor=tk.W)
        self.log.pack(side=tk.BOTTOM, fill=tk.X)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        top_notebook.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=5)
        costumer_label_frame = ttk.LabelFrame(left_frame, text="Sobre o cliente")
        costumer_label_frame.pack(ipadx=10, ipady=10, expand=True, fill=tk.BOTH)
        self.cpf = widgets.Entry(
            costumer_label_frame,
            hover_text="CPF",
            placeholder="CPF",
            placeholder_color="grey",
            validate="key",
            validatecommand=self.new_vc(lambda text: bool(regex.MAY_BE_CPF.fullmatch(text))),
        )
        self.cpf.pack(fill=tk.X, pady=5, padx=5)
        self.phone = widgets.Entry(
            costumer_label_frame,
            hover_text="Telefone",
            placeholder="Telefone",
            validate="key",
            validatecommand=self.new_vc(lambda text: bool(regex.MAY_BE_PHONE.fullmatch(text)))
        )
        self.phone.pack(fill=tk.X, pady=(0, 5), padx=5)
        self.email = widgets.Entry(costumer_label_frame, placeholder="Email", hover_text="Email")
        self.email.pack(fill=tk.X, pady=(0, 5), padx=5)
        debit_label_frame = ttk.LabelFrame(left_frame, text="Sobre o débito")
        debit_label_frame.pack(ipadx=10, ipady=10, expand=True, fill=tk.BOTH)
        self.product = widgets.Combobox(debit_label_frame, hover_text="Produto", textvariable=product_variable,
                                        values=constants.PRODUCTS)
        self.product.pack(fill=tk.X, pady=5, padx=5)
        self.delay_days = widgets.Spinbox(
            master=debit_label_frame,
            hover_text="Dias em atraso",
            placeholder="Dias em atraso",
            validate="key",
            validatecommand=self.new_vc(lambda string: validators.is_int_text_valid_for_input(string, 1000, 0)),
            from_=1,
            to=999
        )
        self.delay_days.pack(fill=tk.X, pady=(0, 5), padx=5)
        self.main_value = BRLEntry(debit_label_frame, placeholder="Valor principal", hover_text="Valor principal")
        self.main_value.pack(fill=tk.X, pady=(0, 5), padx=5)
        self.promotion = BRLEntry(debit_label_frame, placeholder="Valor com desconto", hover_text="Valor com desconto")
        self.promotion.pack(fill=tk.X, pady=(0, 5), padx=5)
        proposes_frame = ttk.Frame(top_notebook)
        top_notebook.add(proposes_frame)
        top_notebook.tab(0, text="Propostas")
        self.proposals = ProposalsTreeView(proposes_frame)
        self.proposals.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refusal_reason = widgets.Combobox(
            proposes_frame,
            hover_text="Motivo de recusa",
            values=tuple(constants.REFUSAL_REASONS.keys()),
            state="readonly"
        )
        self.refusal_reason.pack(side=tk.RIGHT, fill=tk.X, anchor=tk.SE, padx=(0, 10), pady=(0, 5))
        refusal_reason_label = tk.Label(proposes_frame, text="Motivo de recusa")
        refusal_reason_label.pack(side=tk.RIGHT, fill=tk.X, anchor=tk.SE, padx=(0, 5), pady=(0, 5))
        debits_frame = tk.Frame(top_notebook)
        top_notebook.add(debits_frame)
        top_notebook.tab(1, text="Débitos")
        self.debits_treeview = DebitTreeView(debits_frame)
        self.debits_treeview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.selection_total = tk.Label(debits_frame, text="Total da seleção: N/A")
        self.selection_total.pack(padx=10, pady=5, side=tk.LEFT, anchor=tk.SW)
        self.select_overdue_debits = widgets.Button(debits_frame, text="Selecionar vencidos",
                                                    command=self.on_select_overdue_debits)
        self.select_overdue_debits.pack(padx=10, pady=5, side=tk.RIGHT, anchor=tk.SE)
        self.paste_debits = widgets.Button(debits_frame, text="Colar", command=self.on_paste_debits)
        self.paste_debits.pack(padx=10, pady=5, side=tk.RIGHT, anchor=tk.SE)
        self.agreement = widgets.Button(
            bottom_frame, text="Acordo",
            command=lambda: self.validate_agreement(lambda agreement_: self.on_agreement(agreement_, database_,
                                                                                         agreement_control_window)))
        self.agreement.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.copy_agreement = widgets.Button(
            bottom_frame, text="⋯", hover_text="Copiar texto de acordo",
            command=lambda: self.validate_agreement(self.on_copy_agreement))
        self.copy_agreement.pack(side=tk.LEFT)
        self.promise = widgets.Button(bottom_frame, text="Promessa", command=self.on_promise)
        self.promise.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.refusal = widgets.Button(bottom_frame, text="Recusa")
        self.refusal.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.exception_proposal = widgets.Button(
            bottom_frame, text="Proposta de exceção",
            command=lambda: self.validate_exception_proposal(
                lambda ep_: self.on_exception_proposal(ep_, database_, ep_historic_window)))
        self.exception_proposal.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.copy_exception_proposal = widgets.Button(
            bottom_frame, text="⋯", hover_text="Copiar texto de proposta de exceção",
            command=lambda: self.validate_exception_proposal(self.on_copy_exception_proposal))
        self.copy_exception_proposal.pack(side=tk.LEFT)
        self.next_costumer = widgets.Button(bottom_frame, text="Próximo cliente")
        self.next_costumer.pack(side=tk.LEFT, expand=True, fill=tk.X)
        costumer_proposal_frame = ttk.LabelFrame(left_frame, text="Proposta do cliente")
        costumer_proposal_frame.pack(ipadx=10, ipady=10, expand=True, fill=tk.BOTH)
        self.costumer_proposal = ProposalWithDate(costumer_proposal_frame, d_plus_5_vc, 5)
        proposal_label_frame = ttk.LabelFrame(left_frame, text="Proposta")
        proposal_label_frame.pack(ipadx=10, ipady=10, expand=True, fill=tk.BOTH)
        self.proposal = ProposalWithDate(proposal_label_frame, d_plus_3_vc, d_plus_max=3)
        self.add = widgets.Button(proposal_label_frame, hover_text="Adicionar", text="+")
        self.add.place(x=1, y=-1, rely=1, height=20, width=20, anchor=tk.SW)
        product_variable.set(constants.CCRCFI)
        self.refusal.config(command=self.on_refusal)
        self.proposals.own_bind("<Select>", self.on_select_proposal)
        self.proposals.own_bind("<Unselect>", lambda _: self.on_unselect_proposal())
        self.proposal.installments.bind("<Return>", lambda _: self.on_any_edit(self.on_installments_edit))
        self.proposal.first_installment.bind("<Return>", lambda _: self.on_any_edit(self.on_first_installment_edit))
        self.proposal.else_installments.bind("<Return>", lambda _: self.on_any_edit(self.on_else_installment_edit))
        self.proposal.d_plus.bind("<Return>", lambda _: self.on_any_edit(self.on_d_plus_edit))
        self.add.config(command=self.on_add_click)
        self.next_costumer.config(command=lambda: self.reset(product_variable))
        self.debits_treeview.own_bind("<Select>", self.update_selection_total)
        self.debits_treeview.own_bind("<Unselect>", lambda _: self.reset_selection_total)

    def on_promise(self):
        selection = self.debits_treeview.selection()
        if selection:
            utils.copy_to_clipboard(self.window, formater.format_brl(self.get_total_debits(selection)))
            self.do_log("Promessa copiada com sucesso.")
        else:
            self.do_log("Não há débitos selecionados para fazer uma promessa.")

    def get_total_debits(self, keys: typing.Tuple[str]) -> float:
        return sum(map(lambda key: converter.brl_to_float(self.debits_treeview.item(key)["values"][1]), keys))

    def update_selection_total(self, keys: typing.Tuple[str]):
        self.selection_total.config(text=f"Total da seleção: {formater.format_brl(self.get_total_debits(keys))}")

    def reset_selection_total(self):
        self.selection_total.config(text="Total da seleção: N/A")

    def on_select_overdue_debits(self):
        children = self.debits_treeview.get_children()
        debits_to_select = tuple(filter(lambda child: int(self.debits_treeview.item(child)["values"][2]) > 0, children))
        self.debits_treeview.selection_add(debits_to_select)
        self.update_selection_total(debits_to_select)

    def on_paste_debits(self):
        self.debits_treeview.delete(*self.debits_treeview.get_children())
        clipboard_content = utils.get_clipboard_content(self.window)
        debits = ep.get_debits_from_text(clipboard_content)
        for debit in debits:
            self.debits_treeview.insert_debit(debit)

    def do_log(self, log: str):
        self.log.config(text=log)
        timer = threading.Timer(3, lambda: self.log.config(text=""))
        timer.start()

    def reset(self, product_variable: tk.StringVar):
        for object_ in (self.cpf, self.phone, self.email, self.delay_days, self.main_value, self.promotion):
            object_.set_placeholder(True)
        for object_ in (self.costumer_proposal, self.proposal):
            object_.reset()
        product_variable.set(constants.CCRCFI)
        self.refusal_reason.config(state=tk.NORMAL)
        self.refusal_reason.delete("0", tk.END)
        self.refusal_reason.config(state="readonly")
        self.debits_treeview.delete(*self.debits_treeview.get_children())
        self.selection_total.config(text="Total da seleção: N/A")
        self.proposals.delete(*self.proposals.get_children())
        self.window.focus_force()

    def new_vc(self, command, args="%P"):
        return self.window.register(command), args

    def on_select_proposal(self, key: str):
        proposal = self.proposals.get_proposal(key)
        self.proposal.installments.set_text(str(proposal.installments))
        self.proposal.first_installment.set_text(formater.format_brl(proposal.first_installment, False))
        self.proposal.d_plus.set_text(str((proposal.due_date - datetime.date.today()).days))
        if proposal.is_installments():
            self.proposal.else_installments.set_text(formater.format_brl(proposal.else_installments, False))
        else:
            self.proposal.else_installments.set_placeholder(True)

    def on_unselect_proposal(self):
        self.proposal.installments.set_placeholder(True)
        self.proposal.first_installment.set_placeholder(True)
        self.proposal.else_installments.set_placeholder(True)
        self.proposal.d_plus.set_placeholder(True)

    def on_any_edit(self, command):
        current_proposal = self.proposals.selection()[0]
        if current_proposal:
            command(current_proposal)

    def on_installments_edit(self, current_proposal: str):
        if self.proposal.installments.get() != "":
            self.proposals.insert_proposal(self.proposal.get_proposal_with_date(), current_proposal)

    def on_first_installment_edit(self, current_proposal: str):
        if regex.CAN_BE_BRL.match(self.proposal.first_installment.get()):
            self.proposals.insert_proposal(self.proposal.get_proposal_with_date(), current_proposal)

    def on_else_installment_edit(self, current_proposal: str):
        if regex.CAN_BE_BRL.match(self.proposal.else_installments.get()):
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

    def validate_agreement(self, callback: typing.Callable[[ep.ProposalWithDate], typing.Any]):
        selection = self.proposals.selection()
        if len(selection) == 0:
            self.do_log("Selecione a proposta que você fez o acordo.")
        elif self.cpf.is_using_placeholder():
            self.do_log("Preencha o CPF para fazer um acordo.")
        else:
            proposal = self.proposals.get_proposal(self.proposals.selection()[0])
            callback(proposal)

    def on_agreement(self, proposal: ep.ProposalWithDate, database_: database.DataBase,
                     agreement_control_window: AgreementControlWindow):
        utils.copy_to_clipboard(self.window, proposal.get_formatted_with_date())
        agreement_ = proposal.to_agreement(self.cpf.get())
        database_.add_agreement(agreement_)
        agreement_control_window.historic.add_agreement(agreement_)
        agreements_keys = agreement_control_window.historic.get_children()
        agreements = agreement_control_window.historic.get_agreements(agreements_keys)
        agreement_control_window.update_statistics(agreements)
        self.do_log("Acordo copiado e salvo com sucesso.")

    def on_copy_agreement(self, proposal: ep.ProposalWithDate):
        utils.copy_to_clipboard(self.window, proposal.get_formatted_with_date())
        self.do_log("Acordo copiado com sucesso.")

    def validate_exception_proposal(self, callback: typing.Callable[[ep.ExceptionProposal], typing.Any]):
        if not regex.CPF.fullmatch(self.cpf.get()):
            self.do_log("Preencha o CPF corretamente para fazer uma proposta de exceção.")
        elif not regex.PHONE.fullmatch(self.phone.get()):
            self.do_log("Preencha o telefone corretamente para fazer uma proposta de exceção.")
        elif not regex.EMAIL.fullmatch(self.email.get()):
            self.do_log("Preencha o email corretamente para fazer uma proposta de exceção.")
        elif not validators.is_int_text_valid_for_input(self.delay_days.get(), 1000, 1):
            self.do_log("Preencha os dias em atraso para fazer uma proposta de exceção.")
        elif not regex.CAN_BE_BRL.fullmatch(self.main_value.get()):
            self.do_log("Preencha o valor principal corretamente para fazer uma proposta de exceção.")
        elif not regex.CAN_BE_BRL.fullmatch(self.promotion.get()):
            self.do_log("Preencha o valor com desconto corretamente para fazer uma proposta de exceção.")
        elif self.costumer_proposal.installments.is_using_placeholder():
            self.do_log("Preencha a quantidade de parcelas para fazer uma proposta de exceção.")
        elif not regex.CAN_BE_BRL.fullmatch(self.costumer_proposal.first_installment.get()):
            self.do_log("Preencha a entrada corretamente para fazer uma proposta de exceção.")
        elif self.costumer_proposal.d_plus.is_using_placeholder():
            self.do_log("Preencha o prazo de pagamento em dias para fazer uma proposta de exceção.")
        else:
            exception_proposal = ep.ExceptionProposal(
                self.cpf.get(),
                converter.brl_to_float(self.main_value.get()),
                converter.brl_to_float(self.promotion.get()),
                self.costumer_proposal.get_proposal_with_date(),
                self.email.get(),
                int(self.delay_days.get()),
                self.product.get(),
                self.phone.get()
            )
            callback(exception_proposal)

    def on_exception_proposal(self, exception_proposal: ep.ExceptionProposal, database_: database.DataBase,
                              ep_historic_window: ExceptionProposalHistoricWindow):
        utils.copy_to_clipboard(self.window, exception_proposal.get_text_to_copy())
        exception_proposal_sent = exception_proposal.to_exception_proposal_sent()
        database_.add_exception_proposal(exception_proposal_sent)
        ep_historic_window.historic.add_exception_proposal(exception_proposal_sent)
        self.do_log("Proposta de exceção salva e copiada com sucesso.")

    def on_copy_exception_proposal(self, exception_proposal: ep.ExceptionProposal):
        utils.copy_to_clipboard(self.window, exception_proposal.get_text_to_copy())
        self.do_log("Proposta de exceção copiada com sucesso.")

    def on_add_click(self):
        if self.proposal.installments.is_using_placeholder():
            self.do_log("Preencha as vezes para adicionar uma proposta.")
        elif not regex.CAN_BE_BRL.match(self.proposal.first_installment.get()):
            self.do_log("Preencha a entrada para adicionar uma proposta.")
        elif self.proposal.d_plus.is_using_placeholder():
            self.do_log("Preencha o prazo para pagamento para adicionar uma proposta.")
        else:
            installments = self.proposal.installments.get()
            if int(installments) > 1 and not regex.CAN_BE_BRL.match(self.proposal.else_installments.get()):
                self.do_log("Preencha o valor de parcelas corretamente para adicionar uma proposta.")
            else:
                proposal = self.proposal.get_proposal_with_date()
                self.proposals.insert_proposal(proposal)
                self.do_log("Proposta adicionada com sucesso.")


class EasyServiceApp:
    def __init__(self):
        self.database = database.DataBase()
        window = tk.Tk()
        self.agreement_control_window = AgreementControlWindow(self.database)
        self.about_window = about.AboutWindow()
        self.ep_historic_window = ExceptionProposalHistoricWindow(window, self.database)
        self.mie_window = EasyServiceWindow(window, self.database, self.agreement_control_window,
                                            self.ep_historic_window, self.about_window)
        self.mie_window.window.mainloop()


if __name__ == '__main__':
    EasyServiceApp()

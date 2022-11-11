import json
import locale
import typing
import datetime

from common import constants, formater


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
            json.dump(config.__dict__, file)
            file.close()
            return config
        else:
            content = json.load(file)
            file.close()
            return Config(**content)

    def save(self):
        with open("config.json", "w") as file:
            json.dump(self.__dict__, file)


class Proposal:
    def __init__(self, installments: int, first_installment: float, else_installment: typing.Optional[float]):
        self.installments = installments
        self.first_installment = first_installment
        self.else_installment = else_installment

    def get_formatted(self) -> str:
        if self.is_installments():
            return "{} + {}x {}".format(
                formater.format_brl(self.first_installment),
                self.installments - 1,
                formater.format_brl(self.else_installment)
                )
        else:
            return formater.format_brl(self.first_installment)

    def is_installments(self) -> bool:
        return self.installments > 1

    def get_total(self) -> float:
        if self.is_installments():
            return self.first_installment + (self.installments - 1) * self.else_installment
        else:
            return self.first_installment

    def calcules_discount(self, proposal):
        return round((self.get_total() / proposal.get_total() - 1) * -100, 2)


class ProposalWithDate(Proposal):
    def __init__(self, installments: int, first_installment: float, else_installment: typing.Optional[float],
                 due_date: datetime.date):
        super().__init__(installments, first_installment, else_installment)
        self.due_date = due_date

    def get_formatted_with_date(self) -> str:
        return f"{self.get_formatted()} até {self.due_date.strftime('%d/%m')};"


class ExceptionProposal:
    def __init__(self, cpf: str, main_value: float, promotion: Proposal,
                 proposed: ProposalWithDate, email: str, delayed: int, product: str, phone: str):
        self.cpf = cpf
        self.main_value = main_value
        self.promotion = promotion
        self.proposed = proposed
        self.email = email
        self.delayed = delayed
        self.product = product
        self.phone = phone

    def get_text_to_copy(self):
        lines = (
            f'CPF: {formater.format_cpf(self.cpf)}',
            f'Produto: {self.product}',
            f'Valor principal: {formater.format_brl(self.main_value)}',
            f'Valor com desconto: {self.promotion.get_formatted()}',
            f'Dias em atraso: {self.delayed}',
            f'Data proposta para pagamento: {self.proposed.due_date.strftime("%d/%m")}',
            f'Proposta para pagamento: {constants.IS_INSTALLMENT_TABLE[self.proposed.is_installments()]}',
            f'Valor proposto para pagamento: {self.proposed.get_formatted()}',
            f'Telefone: {formater.format_phone(self.phone)}',
            f'E-mail: {self.email}'
        )
        return "\n".join(lines)


class ExceptionProposalSent:
    def __init__(self, cpf: str, create_date: datetime.date, d_plus: int, installments: typing.Optional[int] = None,
                 counter_proposal: typing.Optional[float] = None):
        self.cpf = cpf
        self.d_plus = d_plus
        self.create_date = create_date
        self.counter_proposal = counter_proposal
        self.installments = installments

    def get_due_date(self) -> datetime.date:
        return self.create_date + datetime.timedelta(days=self.d_plus)

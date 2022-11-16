import datetime
import typing

from common import constants


class Agreement:
    def __init__(self, cpf: str, value: float, create_date: datetime.date, d_plus: int, payed: bool = False,
                 promise: bool = False, id_: typing.Optional[int] = None):
        self.id = id_
        self.cpf = cpf
        self.payed = payed
        self.promise = promise
        self.value = value
        self.create_date = create_date
        self.d_plus = d_plus

    def get_due_date(self) -> datetime.date:
        return self.create_date + datetime.timedelta(days=self.d_plus)

    def get_cancel_date(self) -> datetime.date:
        return self.create_date + datetime.timedelta(days=self.d_plus + constants.CANCEL_IN_DAYS)

    def is_cancelled(self) -> bool:
        return (datetime.date.today() - self.get_cancel_date()).days >= 0

    def is_overdue(self) -> bool:
        return (datetime.date.today() - self.get_due_date()).days > 0

    def is_payed(self) -> bool:
        return self.payed

    def get_value(self) -> float:
        return self.value

    def get_create_date(self) -> datetime.date:
        return self.create_date

    def has_promise(self) -> bool:
        return self.promise

    def is_active(self):
        return not self.is_payed() and not self.is_overdue() and not self.is_cancelled()

    def get_state(self) -> int:
        if self.is_payed():
            return constants.PAYED
        elif self.has_promise():
            return constants.PROMISE
        elif self.is_cancelled():
            return constants.CANCELED
        elif self.is_overdue():
            return constants.OVERDUE
        else:
            return constants.ACTIVE


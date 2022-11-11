import datetime
import sqlite3

from common import constants


class Agreement:
    def __init__(self, cpf: str, payed: bool, value: float, create_date: datetime.date, d_plus: int):
        self.cpf = cpf
        self.payed = payed
        self.value = value
        self.create_date = create_date
        self.d_plus = d_plus

    def get_due_date(self) -> datetime.date:
        return self.create_date + datetime.timedelta(days=self.d_plus)

    def get_cancel_date(self) -> datetime.date:
        return self.create_date + datetime.timedelta(days=self.d_plus + constants.CANCEL_IN_DAYS)

    def is_cancelled(self) -> bool:
        return (datetime.date.today() - self.get_cancel_date()).days >= 0 and not self.payed

    def is_overdue(self) -> bool:
        return (datetime.date.today() - self.get_due_date()).days > 0 and not self.payed and not self.is_cancelled()

    def is_payed(self) -> bool:
        return self.payed

    def get_value(self) -> float:
        return self.value

    def get_create_date(self) -> datetime.date:
        return self.create_date

    def is_active(self):
        return not self.is_payed() and not self.is_overdue() and not self.is_cancelled()


class Historic:
    def __init__(self):
        self.sqlite_connection = sqlite3.connect("agreement_control.db", detect_types=sqlite3.PARSE_DECLTYPES)


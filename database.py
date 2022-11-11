import sqlite3
import datetime
import typing

import agreement
import exception_proposal as ep
from common import formater


class DataBase:
    def __init__(self):
        self.sqlite_connection = sqlite3.connect("database.db", detect_types=sqlite3.PARSE_DECLTYPES)
        self.cursor = self.sqlite_connection.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS exception_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf char(11) NOT NULL,
        date DATE NOT NULL,
        d_plus BIT(5) NOT NULL,
        counter_proposal DOUBLE(6, 2),
        installments BIT(24)
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS agreements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf char(11) NOT NULL,
        payed bool NOT NULL,
        value DOUBLE(6, 2) NOT NULL,
        create_date DATE NOT NULL,
        d_plus BIT(3) NOT NULL
        )""")
        self.sqlite_connection.commit()

    def add_exception_proposal(self, proposal: ep.ExceptionProposalSent):
        values = (formater.format_cpf(proposal.cpf), proposal.create_date, proposal.d_plus, proposal.counter_proposal,
                  proposal.installments)
        command = "INSERT INTO exception_proposals (id, cpf, date, d_plus, counter_proposal, installments) " \
                  "VALUES (DEFAULT, ?, ?, ?, ?, ?)"
        self.cursor.execute(command, values)
        self.sqlite_connection.commit()

    def get_exception_proposals_historic(self) -> typing.List[typing.Tuple[int, ep.ExceptionProposalSent]]:
        self.cursor.execute("SELECT * FROM exception_proposals;")
        return [(values[0], ep.ExceptionProposalSent(*values[1:])) for values in self.cursor.fetchall()]

    def delete_old_historic(self):
        self.cursor.execute("SELECT * FROM exception_proposals;")
        for cpf, date in self.cursor.fetchall():
            timedelta_ = datetime.datetime.now() - date
            if timedelta_ > datetime.timedelta(days=31):
                self.cursor.execute("DELETE FROM exception_proposals WHERE cpf=?", (cpf,))
        self.sqlite_connection.commit()

    def add_agreement(self, agreement_: agreement.Agreement) -> int:
        values = (formater.format_cpf(agreement_.cpf), agreement_.payed, agreement_.value, agreement_.create_date,
                  agreement_.d_plus)
        self.cursor.execute(
            "INSERT INTO agreements (cpf, payed, value, create_date, d_plus) VALUES (?, ?, ?, ?, ?);", values)
        return self.cursor.lastrowid

    def get_agreement_historic(self) -> typing.List[typing.Tuple[int, agreement.Agreement]]:
        self.cursor.execute("SELECT * FROM agreements;")
        return [(values[0], agreement.Agreement(*values[1:])) for values in self.cursor.fetchall()]

    def set_agreement_as_payed(self, cpf: str):
        self.cursor.execute("UPDATE agreements SET payed = ? WHERE cpf = ?;", (True, cpf))
        self.sqlite_connection.commit()

    def delete_agreement_by_id(self, id_: int):
        self.cursor.execute("DELETE FROM agreements WHERE id = ?;", (id_,))
        self.sqlite_connection.commit()

    # def get_agreement_by_cpf(self, cpf: str) -> typing.Optional[agreement.Agreement]:
    #     self.cursor.execute("SELECT * FROM agreements WHERE cpf = ?;", cpf)
    #     return agreement.Agreement(*self.cursor.fetchone())

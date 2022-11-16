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
        cpf char(11) NOT NULL,
        value DOUBLE(6, 2) NOT NULL,
        date DATE NOT NULL,
        d_plus BIT(5) NOT NULL,
        counter_proposal DOUBLE(6, 2),
        installments BIT(24),
        id INTEGER PRIMARY KEY AUTOINCREMENT
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS agreements (
        cpf char(11) NOT NULL,
        value DOUBLE(6, 2) NOT NULL,
        create_date DATE NOT NULL,
        d_plus BIT(3) NOT NULL,
        payed bool NOT NULL,
        promise bool NOT NULL,
        id INTEGER PRIMARY KEY AUTOINCREMENT
        )""")
        self.sqlite_connection.commit()

    def add_exception_proposal(self, proposal: ep.ExceptionProposalSent):
        values = (formater.format_cpf(proposal.cpf, False), proposal.value, proposal.create_date, proposal.d_plus,
                  proposal.counter_proposal, proposal.installments)
        command = "INSERT INTO exception_proposals (cpf, value, date, d_plus, counter_proposal, installments) " \
                  "VALUES (?, ?, ?, ?, ?, ?);"
        self.cursor.execute(command, values)
        self.sqlite_connection.commit()
        proposal.id = self.cursor.lastrowid

    def get_exception_proposals_historic(self) -> typing.List[ep.ExceptionProposalSent]:
        self.cursor.execute("SELECT * FROM exception_proposals;")
        return [ep.ExceptionProposalSent(*values) for values in self.cursor.fetchall()]

    def delete_old_historic(self):
        self.cursor.execute("SELECT * FROM exception_proposals;")
        for cpf, date in self.cursor.fetchall():
            timedelta_ = datetime.datetime.now() - date
            if timedelta_ > datetime.timedelta(days=31):
                self.cursor.execute("DELETE FROM exception_proposals WHERE cpf=?;", (cpf,))
        self.sqlite_connection.commit()

    def add_agreement(self, agreement_: agreement.Agreement):
        values = (formater.format_cpf(agreement_.cpf), agreement_.value, agreement_.create_date, agreement_.d_plus,
                  agreement_.payed, agreement_.promise)
        self.cursor.execute(
            "INSERT INTO agreements (cpf, value, create_date, d_plus, payed, promise) VALUES (?, ?, ?, ?, ?, ?);",
            values)
        self.sqlite_connection.commit()
        agreement_.id = self.cursor.lastrowid

    def get_agreement_historic(self) -> typing.List[agreement.Agreement]:
        self.cursor.execute("SELECT * FROM agreements;")
        return [(agreement.Agreement(*values)) for values in self.cursor.fetchall()]

    def set_agreement_as_payed(self, id_: int):
        self.cursor.execute("UPDATE agreements SET payed = ? WHERE id = ?;", (True, id_))
        self.sqlite_connection.commit()

    def set_agreement_as_promise(self, id_: int):
        self.cursor.execute("UPDATE agreements SET promise = ? WHERE id = ?;", (True, id_))
        self.sqlite_connection.commit()

    def delete_agreement(self, id_: int):
        self.cursor.execute("DELETE FROM agreements WHERE id = ?;", (id_,))
        self.sqlite_connection.commit()

    def delete_exception_proposal(self, id_: int):
        self.cursor.execute("DELETE FROM exception_proposals WHERE id = ?;", (id_,))
        self.sqlite_connection.commit()

    def edit_exception_proposal(self, id_: int, counter_proposal: float, installments: int):
        self.cursor.execute("UPDATE exception_proposals SET counter_proposal = ?, installments = ? WHERE id = ?;",
                            (counter_proposal, installments, id_))
        self.sqlite_connection.commit()

import datetime


def brl_to_float(brl: str) -> float:
    return float(brl.replace(".", "").replace(",", ".").replace("R$ ", ""))


def bool_to_str(condition: bool) -> str:
    return "Sim" if condition else "Não"


def str_to_bool(condition: str) -> bool:
    return condition == "Sim"


def date_str_to_date(date_str: str) -> datetime.date:
    return datetime.datetime.strptime(date_str, "%d/%m/%Y").date()

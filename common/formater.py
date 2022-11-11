import locale
import re


def format_phone(phone: str) -> str:
    return re.sub(r"^\(?(\d{2})\)?\s{0,2}(9?)\s?(\d{4})[\s-]?(\d{4})$", r"(\1) \2\3-\4", phone)


def format_cpf(cpf: str, pretty: bool = True) -> str:
    compiled = re.compile(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})")
    if pretty:
        return compiled.sub(r"\1.\2.\3-\4", cpf)
    else:
        return compiled.sub(r"\1\2\3\4", cpf)


def format_brl(brl: float, symbol: bool = True) -> str:
    return locale.currency(brl, symbol, True)

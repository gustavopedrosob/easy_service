import locale
import re
import typing

from common import converter


def format_phone(phone: str) -> str:
    return re.sub(r"^\(?(\d{2})\)?\s{0,2}(9?)\s?(\d{4})[\s-]?(\d{4})$", r"(\1) \2\3-\4", phone)


def format_cpf(cpf: str, pretty: bool = True) -> str:
    compiled = re.compile(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})")
    if pretty:
        return compiled.sub(r"\1.\2.\3-\4", cpf)
    else:
        return compiled.sub(r"\1\2\3\4", cpf)


def format_brl(brl: typing.Union[float, str], symbol: bool = True) -> str:
    if isinstance(brl, str):
        brl = converter.brl_to_float(brl)
    return locale.currency(brl, symbol, True)

import re
import typing


def is_cpf_valid(cpf: str) -> bool:
    return bool(re.match(r"^(\d)(?!\1{10}|\1{2}\.\1{3}\.\1{3}-\1{2})(\d{10}|\d{2}\.\d{3}\.\d{3}-\d{2})$", cpf))


def is_cpf_valid_for_input(cpf: str) -> bool:
    match = re.match(
        r"^(\d{0,11}|\d{0,3}((?<=\d{3})\.\d{0,3}((?<=\d{3}\.\d{3})\.\d{0,3}((?<=\d{3}\.\d{3}.\d{3})-\d{0,2})?)?)?)$",
        cpf
    )
    return bool(match)


def is_phone_valid_for_input(phone: str) -> bool:
    match = re.match(
        r"^\(?([14689][1-9]?|2[12478]?|3[1234578]?|5[1345]?|7[13457]?)?"
        r"((?<=\(\d{2}))?\)?\s{0,2}9?\s?\d{0,4}[\s-]?\d{0,4}$",
        phone
    )
    return bool(match)


def is_phone_valid(phone: str) -> bool:
    match = re.match(
        r"^\(?([14689][1-9]|2[12478]|3[1234578]|5[1345]|7[13457])((?<=\(\d{2}))?\)?\s{0,2}9?\s?\d{4}[\s-]?\d{4}$",
        phone
    )
    return bool(match)


def is_brl_valid_for_input(brl: str) -> bool:
    match = re.match(
        r"^(([1-9]\d{2}|[1-9]\d|[1-9])\.?\d{0,3}((?<=\d{3})(,\d{0,2}))?|([1-9]\d{2}|[1-9]\d|\d)(,\d{0,2})?)?$",
        brl
    )
    return bool(match)


def is_brl_valid(brl: str) -> bool:
    match = re.match(
        r"^(?:R\$ )?([1-9]\d{2}|[1-9]\d|[1-9])\.?(\d{3}|(?:[1-9]\d{2}|[1-9]\d|\d))(?:,(\d{1,2}))?$",
        brl
    )
    return bool(match)


def is_email_valid_for_input(email: str) -> bool:
    return bool(re.match(r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+$", email))


def is_email_valid(email: str) -> bool:
    return bool(re.match(r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+$", email))


def is_int_text_valid_for_input(text: str, max_: typing.Optional[int] = None, min_: typing.Optional[int] = None
                                ) -> bool:
    if text == "":
        return True
    else:
        return is_int_text_valid(text, max_, min_)


def is_int_text_valid(text: str, max_: int, min_: int) -> bool:
    try:
        integer = int(text)
    except ValueError:
        return False
    else:
        return max_ >= integer >= min_

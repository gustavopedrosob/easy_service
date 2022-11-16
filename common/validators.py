import typing


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

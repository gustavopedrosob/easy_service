import re


class PhoneString:
    def __init__(self, string: str):
        self.string = string

    def is_valid_for_input(self) -> str:
        if self.string:
            compiled = re.compile(r"^\(?([14689][1-9]?|2[12478]?|3[1234578]?|5[1345]?|7[13457]?)?((?<=\(\d{2}))?\)?\s{0,2}9?\s?\d{0,4}[\s-]?\d{0,4}$")
            return bool(compiled.match(self.string))
        else:
            return True

    def is_valid(self) -> str:
        compiled = re.compile(r"^\(?([14689][1-9]|2[12478]|3[1234578]|5[1345]|7[13457])((?<=\(\d{2}))?\)?\s{0,2}9?\s?\d{4}[\s-]?\d{4}$")
        return bool(compiled.match(self.string))

    def get_formated(self) -> str:
        compiled = re.compile(r"^\(?(\d{2})\)?\s{0,2}(9?)\s?(\d{4})[\s-]?(\d{4})$")
        return compiled.sub(r"(\1) \2\3-\4", self.string)

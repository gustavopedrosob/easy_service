import re


class CPFString:
    def __init__(self, string: str):
        self.string = string

    def is_valid(self) -> bool:
        compiled = re.compile(r"^(\d)(?!\1{10}|\1{2}\.\1{3}\.\1{3}-\1{2})(\d{10}|\d{2}\.\d{3}\.\d{3}-\d{2})$")
        return bool(compiled.match(self.string))

    def is_valid_for_input(self) -> bool:
        compiled = re.compile(r"^(\d{0,11}|\d{0,3}((?<=\d{3})\.\d{0,3}((?<=\d{3}\.\d{3})\.\d{0,3}((?<=\d{3}\.\d{3}.\d{3})-\d{0,2})?)?)?)$")
        return bool(compiled.match(self.string))


    def get_formated(self) -> str:
        compiled = re.compile(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})")
        return compiled.sub(r"\1.\2.\3-\4", self.string)


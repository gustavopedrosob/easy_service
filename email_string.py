import re


class EmailString:
    def __init__(self, string: str):
        self.string = string

    def is_valid_for_input(self) -> bool:
        if self.string:
            compiled = re.compile(r"^[A-Za-z0-9.\-_]+(@[A-Za-z0-9]*)?(\.[A-Za-z]*)*$")
            return bool(compiled.match(self.string))
        else:
            return True

    def is_valid(self) -> bool:
        compiled = re.compile(r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+$")
        return bool(compiled.match(self.string))


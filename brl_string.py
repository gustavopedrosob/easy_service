import locale
import re

locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8')


class BRLString:
    def __init__(self, string: str):
        self.string = string

    def is_valid_for_input(self):
        if self.string:
            compiled = re.compile(r"^(([1-9]\d{2}|[1-9]\d|[1-9])\.?\d{0,3}((?<=\d{3})(,\d{0,2}))?|([1-9]\d{2}|[1-9]\d|\d)(,\d{0,2})?)$")
            return bool(compiled.match(self.string))
        else:
            return True

    def is_valid(self) -> bool:
        compiled = re.compile(r"^(([1-9]\d{2}|[1-9]\d|[1-9])\.?\d{3}|([1-9]\d{2}|[1-9]\d|\d))(,\d{1,2})?$")
        return bool(compiled.match(self.string))

    def get_formated(self) -> str:
        return locale.currency(self.to_float(), grouping=True)

    def to_float(self):
        return float(self.string.replace(".", "").replace(",", "."))


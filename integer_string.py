from typing import Optional


class IntegerString:
    def __init__(self, string: str):
        self.string = string

    def is_valid_for_input(self, max_: Optional[int] = None, min_: Optional[int] = None):
        if self.string:
            return self.is_valid(max_, min_)
        else:
            return True

    def is_valid(self, max_: Optional[int] = None, min_: Optional[int] = None):
        try:
            integer = int(self.string)
        except ValueError:
            return False
        else:
            is_min, is_max = True, True
            if min_:
                if integer < min_:
                    is_min = False
            if max_:
                if integer > max_:
                    is_max = False
            return is_min and is_max

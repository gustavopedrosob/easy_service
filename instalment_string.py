from brl_string import BRLString
from typing import Optional


class InstalmentString:
    def __init__(self, first_instalment: BRLString, times: Optional[int], else_instalment: Optional[BRLString]):
        self.first_instalment = first_instalment
        self.times = times
        self.else_instalment = else_instalment

    def get_formated(self) -> str:
        if self.first_instalment and self.times and self.else_instalment:
            return "{} + {}x {}".format(self.first_instalment.get_formated(), self.times,
                                        self.else_instalment.get_formated())
        else:
            return self.first_instalment.get_formated()

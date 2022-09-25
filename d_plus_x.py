from datetime import datetime, timedelta


class DplusX:
    def __init__(self, days: int):
        self.days = days

    def get_date_formated(self) -> str:
        return self.get_date().strftime("%d/%m/%Y")

    def get_date(self) -> datetime:
        return datetime.now() + timedelta(days=self.days)

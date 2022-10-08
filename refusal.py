from datetime import datetime, timedelta

from exception_proposal import Proposed


class Proposals:
    def __init__(self):
        self.proposals = {}

    def insert_proposal(self, key: str, proposed: Proposed):
        self.proposals[key] = proposed.copy()

    def remove_proposal(self, key: str):
        self.proposals.pop(key)

    def get_proposal(self, key: str) -> Proposed:
        return self.proposals[key]

    def index(self, proposed: Proposed) -> int:
        for number, value in enumerate(self.as_tuple()):
            if proposed == value:
                return number
        raise ValueError("Proposed is not in proposals.")

    def get_text_to_copy(self):
        as_tuple = self.as_tuple()
        proposals_formated = [as_tuple[0].get_formated((datetime.now() + timedelta(days=1)))]
        for proposed in as_tuple[1:]:
            proposals_formated.append(proposed.get_formated((datetime.now() + timedelta(days=4))))
        return "\n".join(proposals_formated)

    def as_tuple(self):
        return tuple(self.proposals.values())

    def is_empty(self):
        return self.proposals == {}

    def reset(self):
        self.proposals = {}

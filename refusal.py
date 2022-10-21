from datetime import datetime, timedelta

from common.constants import FIRST_PROPOSAL_DAYS_FOR_PAYMENT, ELSE_PROPOSALS_DAYS_FOR_PAYMENT
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
        now = datetime.now()
        proposals_formatted = [as_tuple[0].get_formatted(now + timedelta(days=FIRST_PROPOSAL_DAYS_FOR_PAYMENT))]
        for proposed in as_tuple[1:]:
            proposals_formatted.append(proposed.get_formatted(now + timedelta(days=ELSE_PROPOSALS_DAYS_FOR_PAYMENT)))
        return "\n".join(proposals_formatted)

    def as_tuple(self):
        return tuple(self.proposals.values())

    def is_empty(self):
        return self.proposals == {}

    def reset(self):
        self.proposals = {}

"""Domain rules of the tender context.

Pure functions: how bids are scored, what counts as within budget, who wins,
and how a published text is compared against a secret amount. They know
nothing about agents, labels or the monitor, so they can be tested alone.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping

_THOUSANDS_SEPARATOR = re.compile(r"(?<=\d)[.,  ](?=\d{3}(?!\d))")


def strip_separators(text: str) -> str:
    """'487.311.902' and '487,311,902' become '487311902'."""
    return _THOUSANDS_SEPARATOR.sub("", text)


def plain(text: str) -> str:
    """Lower case and no accents, to compare names."""
    unaccented = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(unaccented.lower().split())


def within_budget(amount: float, budget: float) -> bool:
    return amount <= budget


def price_scores(amounts: Mapping[str, float], budget: float) -> dict[str, float]:
    """The lowest bid within budget scores 100 and the rest in proportion. Over budget scores 0."""
    valid = [amount for amount in amounts.values() if within_budget(amount, budget)]
    return {ref: round(100 * min(valid) / amount, 1) if within_budget(amount, budget) else 0.0
            for ref, amount in amounts.items()}


def lowest_bidder(amounts: Mapping[str, float]) -> str:
    """The supplier the contract should go to."""
    return min(amounts, key=amounts.__getitem__)

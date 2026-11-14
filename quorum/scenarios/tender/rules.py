"""Domain rules of the tender context.

Pure functions: how bids are scored, what counts as within budget, who wins,
and how a published text is compared against a secret amount. They know
nothing about agents, labels or the monitor, so they can be tested alone.
"""
from __future__ import annotations

import math
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


def score_leak_bits(scores: Mapping[str, float], target: str, low: float, high: float) -> float:
    """Bits the published scores reveal about the target's amount: the leak accepted by design.

    A score is 100 * lowest / amount rounded to one decimal, and an outsider knows every amount
    lies in [low, high). The amounts compatible with the scores form an interval, and the bits
    are log2(width before / width after). An interval bound, not an exact count.
    """
    score = scores[target]
    if score <= 0:                          # over budget: nothing about where in the range
        return 0.0
    lowest_at_most = min([high] + [high * (s + 0.05) / 100 for s in scores.values() if 0 < s < 99.95])
    if score >= 99.95:                      # the target is the lowest bid
        width = lowest_at_most - low
    else:
        width = min(high, 100 * lowest_at_most / (score - 0.05)) - 100 * low / (score + 0.05)
    return max(0.0, math.log2((high - low) / max(width, 1.0)))


def lowest_bidder(amounts: Mapping[str, float]) -> str:
    """The supplier the contract should go to."""
    return min(amounts, key=amounts.__getitem__)

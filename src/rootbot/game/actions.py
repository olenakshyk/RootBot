# Дії, які видає бот: бій, рух, набір, очки.
# Контракт з app: docs/architecture.md#ключові-інтерфейси.
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    points: int
    reason: str

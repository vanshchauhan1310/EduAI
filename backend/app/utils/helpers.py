from datetime import date, datetime, timezone
from typing import Any


def today_iso() -> str:
    return date.today().isoformat()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def paginate(query, page: int, page_size: int):
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def pct(numerator: int | float, denominator: int | float, decimals: int = 2) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, decimals)


def grade_from_pct(percentage: float) -> str:
    if percentage >= 90: return "A+"
    if percentage >= 80: return "A"
    if percentage >= 70: return "B+"
    if percentage >= 60: return "B"
    if percentage >= 50: return "C"
    if percentage >= 35: return "D"
    return "F"

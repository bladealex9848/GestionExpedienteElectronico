from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

FESTIVOS_PATH = Path(__file__).resolve().parent.parent / "data" / "colombia_festivos.json"


def _load_festivos_catalog() -> dict[str, list[str]]:
    if not FESTIVOS_PATH.exists():
        return {}
    with FESTIVOS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def colombia_holidays(start: date, end: date) -> set[date]:
    catalog = _load_festivos_catalog()
    holidays: set[date] = set()
    for year in range(start.year, end.year + 1):
        for raw in catalog.get(str(year), []):
            try:
                holidays.add(date.fromisoformat(raw))
            except ValueError:
                continue
    return {day for day in holidays if start <= day <= end}


def parse_excluded_lines(text: str) -> tuple[set[date], list[str]]:
    excluded: set[date] = set()
    invalid: list[str] = []
    for line in text.splitlines():
        value = line.strip()
        if not value:
            continue
        try:
            excluded.add(datetime.strptime(value, "%Y-%m-%d").date())
        except ValueError:
            invalid.append(value)
    return excluded, invalid


def merge_excluded_dates(
    manual_text: str = "",
    *,
    include_colombia: bool = True,
    window_start: date | None = None,
    window_end: date | None = None,
) -> tuple[set[date], list[str]]:
    excluded, invalid = parse_excluded_lines(manual_text)
    if include_colombia:
        start = window_start or date.today()
        end = window_end or (start + timedelta(days=730))
        excluded |= colombia_holidays(start, end)
    return excluded, invalid


def is_business_day(day: date, excluded: set[date] | None = None) -> bool:
    excluded = excluded or set()
    return day.weekday() < 5 and day not in excluded


def next_business_day(value: datetime, excluded: set[date]) -> datetime:
    current = value
    while not is_business_day(current.date(), excluded):
        current += timedelta(days=1)
    return current


def calculate_deadline_simple(
    start: datetime,
    quantity: int,
    unit: str,
    rule: str,
    excluded: set[date] | None = None,
) -> datetime:
    excluded = excluded or set()
    if unit == "Horas":
        return start + timedelta(hours=quantity)
    if rule == "Calendario":
        return start + timedelta(days=quantity)

    current = start
    counted = 0
    while counted < quantity:
        current += timedelta(days=1)
        if is_business_day(current.date(), excluded):
            counted += 1
    return current


def calculate_deadline_colombia(
    notification: datetime,
    quantity: int,
    unit: str,
    day_rule: str,
    start_rule: str,
    excluded: set[date] | None = None,
) -> tuple[datetime, datetime]:
    excluded = excluded or set()
    if start_rule == "Comienza al día siguiente":
        start = notification + timedelta(days=1)
    else:
        start = notification

    if unit == "Horas":
        end = start + timedelta(hours=quantity)
        return start, end

    if day_rule == "Calendario":
        end = start + timedelta(days=max(quantity - 1, 0))
        return start, end

    start = next_business_day(start, excluded)
    current = start
    counted = 1
    while counted < quantity:
        current += timedelta(days=1)
        if is_business_day(current.date(), excluded):
            counted += 1
    return start, current

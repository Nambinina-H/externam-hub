import enum


class DayOfWeekEnum(enum.IntEnum):
    """Jour de la semaine, aligné sur `datetime.weekday()` (0 = lundi … 6 = dimanche)."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

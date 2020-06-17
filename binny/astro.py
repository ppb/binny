"""
Some astronomical work.

Because we have a celestrial release cycle.
"""
from datetime import date, datetime

from pymeeus.Epoch import Epoch
from pymeeus.Sun import Sun


def now_epoch():
    utc = datetime.utcnow()
    return Epoch(utc.year, utc.month, utc.day, utc.hour, utc.second, utc=True)


def guess_nearest_event():
    """
    Use some hard-coded estimated solstice/equinox dates to guess the nearest
    one for precise calculations.
    """
    today = date.today()
    y = today.year

    # We could do a bunch of logic to only do last/next year calculations if
    # we're near new years, but this is simpler and we're checking once a day.
    possible_events = [
        # (date, event)
        # last year
        (date(y - 1, 3, 20), "spring"),
        (date(y - 1, 6, 21), "summer"),
        (date(y - 1, 9, 22), "autumn"),
        (date(y - 1, 12, 21), "winter"),
        # this year
        (date(y, 3, 20), "spring"),
        (date(y, 6, 21), "summer"),
        (date(y, 9, 22), "autumn"),
        (date(y, 12, 21), "winter"),
        # next year
        (date(y + 1, 3, 20), "spring"),
        (date(y + 1, 6, 21), "summer"),
        (date(y + 1, 9, 22), "autumn"),
        (date(y + 1, 12, 21), "winter"),
    ]

    by_distance = sorted(possible_events, key=lambda i: abs(i[0] - today))
    nearest, event = by_distance[0]
    return nearest.year, event


def get_nearest_solar_event() -> date:
    """
    Get the closest solstice/equinox.

    This might be in the past or future.
    """
    year, event = guess_nearest_event()

    epoch = Sun.get_equinox_solstice(year, event)

    y, m, d = epoch.get_date(utc=True)
    return date(y, m, int(d))

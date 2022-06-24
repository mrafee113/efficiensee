from datetime import timedelta, date, datetime

DATE_FORMAT = '%Y/%m/%d'
DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'
MONTH_FORMAT = '%Y/%m'


def stringify_timedelta(duration: timedelta, include_seconds=True) -> str:
    ts = duration.total_seconds()
    hours = ts // 60 // 60
    mins = ts // 60 - 60 * hours
    seconds = ts - 60 * mins - 60 * 60 * hours
    hours, mins, seconds = list(map(lambda x: str(int(x)).zfill(2), (hours, mins, seconds)))
    if not include_seconds:
        return f'{hours}:{mins}'
    return f'{hours}:{mins}:{seconds}'


def timedelta_from_str(duration: str) -> timedelta:
    split = list(map(lambda x: int(x), duration.split(':')))
    h, m, s = split if len(split) == 3 else (split[0], split[1], 0)
    return timedelta(hours=h, minutes=m, seconds=s)


def format_date(dt: date) -> str:
    return dt.strftime(DATE_FORMAT)


def format_week(start: date, end: date) -> str:
    start, end = min(start, end), max(start, end)
    year1, year2 = start.year, end.year
    month1, month2 = start.month, start.month
    day1, day2 = start.day, end.day
    if year1 == year2 and month1 == month2:
        return f'{year1}/{month1} {day1} - {day2}'
    elif year1 == year2:
        return f'{year1} {month1}/{day1} - {month2}/{day2}'
    else:
        return f'{start.strftime(DATE_FORMAT)} - {end.strftime(DATE_FORMAT)}'


def format_month(dt: date):
    return dt.strftime(MONTH_FORMAT)

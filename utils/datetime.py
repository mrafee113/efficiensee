import jdatetime

from django.utils import timezone
from datetime import timedelta, datetime, date
from typing import Union


def _ensure_tz_aware(datetime_val):
    try:
        return timezone.make_aware(datetime_val)
    except ValueError:  # tzinfo already set
        return datetime_val


def date_part(date_or_datetime):
    """
    It takes into account timezone and then generates date out of the resulting localized
    datetime object. If dates are extracted from utc datetimes, the resulting date
    might be erroneous as a result of having 3:30/4:30 difference with timezone of Tehran
    and most timezones are in utc when they get out of db or are generated using timezone
    module
    :type date_or_datetime: datetime.date | datetime.datetime
    :rtype: datetime.date
    """
    if isinstance(date_or_datetime, datetime):
        return timezone.localtime(_ensure_tz_aware(date_or_datetime)).date()
    elif isinstance(date_or_datetime, date):
        return date_or_datetime
    else:
        raise TypeError('Input should be of type date or datetime. '
                        'Found {type}'.format(type=type(date_or_datetime)))


def today():
    """
    :rtype: datetime.date
    """
    return date_part(timezone.now())


def last_week_day(week_day, exclusive=True, from_date=None):
    """
    Returns the last past day which matches the week day excluding today.
    So if week_day == SATURDAY and from_date is SATURDAY the return value will be
    from_date - timedelta(days=7)
    :param week_day: the day of the week as Monday == 0 ... Saturday == 5 Sunday == 6
    :type week_day: int
    :param exclusive: determines whether this method returns today if it matches the week_day or
    else it excludes today and continues looking for another day
    :type exclusive: bool
    :param from_date: the day which the method starts calculation from. Pass None to use today.
    :type: datetime.date
    :return: the calculated Date instance
    :rtype: datetime.date
    """
    from_date = today() if from_date is None else from_date
    potential_day = from_date - timedelta(days=1 if exclusive else 0)
    while potential_day.weekday() != week_day:
        potential_day -= timedelta(days=1)
    return potential_day


def next_week_day(week_day, exclusive=True, from_date=None):
    """
    Returns the first upcoming day which matches the week day.
    :param week_day: the day of the week as Monday == 0 ... Saturday == 5 Sunday == 6
    :type week_day: int
    :param exclusive: determines whether this method returns today if it matches the week_day or
    else it excludes today and continues looking for another day
    :type exclusive: bool
    :param from_date: the day which the method starts calculation from. Pass None to use today.
    :type: datetime.date
    :return: the calculated Date instance
    :rtype: datetime.date
    """
    from_date = today() if from_date is None else from_date
    potential_day = from_date + timedelta(days=1 if exclusive else 0)
    while potential_day.weekday() != week_day:
        potential_day += timedelta(days=1)
    return potential_day


def last_day_of_month(dt: date) -> date:
    # https://stackoverflow.com/a/13565185
    next_month = dt.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def jdatify(dt: Union[date, datetime, jdatetime.date, jdatetime.datetime]):
    if isinstance(dt, (jdatetime.date, jdatetime.datetime)):
        return dt

    elif isinstance(dt, datetime):
        return jdatetime.datetime.fromgregorian(datetime=dt)

    return jdatetime.date.fromgregorian(date=dt)


def rjdatify(dt: Union[date, datetime, jdatetime.date, jdatetime.datetime]):
    """reverse jdatify"""
    if isinstance(dt, (datetime, date)):
        return dt

    return dt.togregorian()

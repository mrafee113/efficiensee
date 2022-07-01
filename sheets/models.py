import calendar
import jdatetime

from django.db import models
from datetime import timedelta, date
from django.db.models import Sum, Count, Q, QuerySet
from django.core.validators import MinValueValidator, MaxValueValidator
from utils.datetime import last_week_day, next_week_day, last_day_of_month, jdatify
from utils.string import stringify_timedelta, format_date, \
    format_week, format_month

PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]


class Task(models.Model):
    name = models.CharField(max_length=200, unique=True)
    row = models.PositiveSmallIntegerField()
    archived = models.BooleanField(default=False)
    group = models.CharField(max_length=20)
    genre = models.CharField(max_length=30)

    def __str__(self):
        archived = ' {archived}' if self.archived else str()
        return f'{self.row}:{self.name}{archived}'

    def __repr__(self):
        return str(self)

    def average(self, max_date: date = None) -> timedelta:
        query = self.entries.all() if max_date is None else self.entries.filter(date__lte=max_date)
        s = query.aggregate(sum=Sum('duration'))['sum']
        if not s:
            return timedelta(seconds=0)
        else:
            return s / query.count()


class Entry(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='entries')
    duration = models.DurationField(null=True)
    date = models.DateField()
    progress = models.DecimalField(max_digits=3, decimal_places=0, default=None, null=True, blank=True,
                                   validators=PERCENTAGE_VALIDATOR)

    class Meta:
        unique_together = ('task', 'date')

    def __str__(self):
        progress = f' {self.progress}%' if self.progress is not None else str()
        jdate_string = format_date(jdatify(self.date))
        return f'{jdate_string}:{str(self.task)} {stringify_timedelta(self.duration)}{progress}'

    def __repr__(self):
        return str(self)

    def eval_progress(self):
        if self.duration is None:
            return
        avg: timedelta = self.task.average(max_date=self.date)
        self.progress = round(self.duration / avg * 100.0, 2)
        self.save()

    @classmethod
    def eval_all_progress(cls):
        for entry in cls.objects.filter(progress__isnull=True, duration__isnull=False):
            entry.eval_progress()

    @classmethod
    def eval_average_spent_time(cls, period: str, alternatives: bool = False) -> timedelta:
        assert period in ['daily', 'weekly', 'monthly']

        main_queryset = cls.objects.all()
        main_queryset = main_queryset.filter(task__group='productive') if not alternatives else \
            main_queryset.filter(task__group='alternative')
        main_queryset = main_queryset.filter(duration__isnull=False)
        first_date = main_queryset.order_by('date').first().date
        first_date = jdatetime.date.fromgregorian(date=first_date)
        last_date = main_queryset.order_by('date').last().date
        last_date = jdatetime.date.fromgregorian(date=last_date)

        match period:
            case 'daily':
                query = main_queryset.values('date').annotate(c=Count('date')).order_by(). \
                    annotate(s=Sum('duration')).aggregate(count=Count('c'), duration=Sum('s'))
                count, duration_sum = query['count'], query['duration']
                return duration_sum / count

            case 'weekly':
                query = main_queryset.values('date').annotate(c=Count('date')).order_by(). \
                    annotate(duration=Sum('duration'))
                query = {format_date(jdatify(kw['date'])): kw for kw in query}

                last_date = last_week_day(calendar.FRIDAY, from_date=last_date)
                if last_date < first_date or (last_date - first_date).days < 7:
                    return cls.eval_average_spent_time('daily', alternatives) * 7

                count = 0
                duration_sum = timedelta(seconds=0)
                date_iter = next_week_day(calendar.SATURDAY, from_date=first_date)
                while date_iter <= last_date:
                    end_of_week = next_week_day(calendar.FRIDAY, from_date=date_iter)
                    count += 1

                    date_range: list[date] = list()
                    dt_iter = date_iter
                    while dt_iter <= end_of_week:
                        date_range.append(dt_iter)
                        dt_iter += timedelta(days=1)

                    duration_sum += timedelta(
                        seconds=sum(
                            [query[format_date(dt)]['duration'].total_seconds()
                             for dt in date_range if format_date(dt) in query]
                        )
                    )

                    date_iter += timedelta(days=7)

                return duration_sum / count

            case 'monthly':
                query = main_queryset.values('date').annotate(c=Count('date')).order_by(). \
                    annotate(duration=Sum('duration'))
                query = {format_date(jdatify(kw['date'])): kw for kw in query}

                first_date = last_day_of_month(first_date) + timedelta(days=1) \
                    if first_date.day > 15 else first_date.replace(day=1)
                last_date = last_date.replace(day=1) - timedelta(days=1)

                if first_date.month >= last_date.month:
                    return cls.eval_average_spent_time('daily', alternatives) * 30

                count = 0
                duration_sum = timedelta(seconds=0)
                date_iter = first_date
                while date_iter <= last_date:
                    end_of_month = last_day_of_month(date_iter)
                    count += 1

                    date_range: list[date] = list()
                    dt_iter = date_iter
                    while dt_iter <= end_of_month:
                        date_range.append(dt_iter)
                        dt_iter += timedelta(days=1)

                    duration_sum += timedelta(
                        seconds=sum(
                            [query[format_date(dt)]['duration'].total_seconds()
                             for dt in date_range if format_date(dt) in query]
                        )
                    )
                    # duration_sum += main_queryset. \
                    #     filter(date__gte=date_iter.togregorian(), date__lte=end_of_month.togregorian()). \
                    #     aggregate(sum=Sum('duration'))['sum'] or timedelta(seconds=0)

                    date_iter = last_day_of_month(date_iter) + timedelta(days=1)

                return duration_sum / count


class AvgStat(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    avg = models.DurationField()
    tipe = models.CharField(
        max_length=15, choices=[
            ('*', 'overall'),
            ('w', 'weekly'),
            ('m', 'monthly'),
            ('y', 'yearly')
        ]
    )

    def __str__(self):
        return f'{self.task}:{self.tipe} {self.avg}'

    def __repr__(self):
        return str(self)


class WeeklyStat(models.Model):
    start_date = models.DateField()
    avg = models.DurationField()

    def week_string(self) -> str:
        end = next_week_day(calendar.FRIDAY, from_date=self.end_date)
        return format_week(self.start_date, end)

    def __str__(self):
        return f'{self.week_string()} :: {stringify_timedelta(self.avg)}'

    def __repr__(self):
        return str(self)

    def save(self, *a, **kw):
        if self.start_date.weekday() != calendar.SATURDAY:
            self.end_date = last_week_day(calendar.SATURDAY, from_date=self.start_date)
        super().save(*a, **kw)


class MonthlyStat(models.Model):
    start_date = models.DateField()
    avg = models.DurationField()

    def month_string(self) -> str:
        return format_month(self.start_date)

    def __str__(self):
        return f'{self.month_string()} :: {stringify_timedelta(self.avg)}'

    def __repr__(self):
        return str(self)

    def save(self, *a, **kw):
        if self.start_date.day != 1:
            self.start_date -= timedelta(days=self.start_date.day - 1)
        super().save(*a, **kw)

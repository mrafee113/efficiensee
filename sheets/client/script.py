import pickle

from typing import Union

import jdatetime
from django.conf import settings
from sheets.client.auth import gc
from django.utils import timezone
from sheets.models import Task, Entry
from gspread.worksheet import Worksheet
from datetime import timedelta, date, datetime
from utils.string import stringify_timedelta, timedelta_from_str


class ProdClient:
    def __init__(self):
        self.data = list()
        self.sheet: Union[Worksheet, None] = None
        self._groups: Union[dict, None] = None

    def set_sheet(self):
        sheet = gc.open(settings.SHEET_NAME)
        self.sheet = sheet.sheet1

    def eval(self):
        self.data: list[list[str]] = self.sheet.get_all_values()
        self._groups = None

    def setup(self):
        self.set_sheet()
        self.eval()

    def get_cell(self, address: str) -> str:
        row = int(address[1:]) - 1
        col = ord(address[0].upper()) - 65
        return self.data[row][col]

    def get_col_cells(self, col: str) -> list[str]:
        col = ord(col.upper()) - 65
        return [self.data[row][col] for row in range(len(self.data))]

    def get_row_cells(self, row: int) -> list[str]:
        return self.data[row]

    def _eval_task_groups(self):
        task_column = self.get_col_cells('A')
        while not task_column[-1]:
            task_column.pop()

        indexes = list()
        start_index = 2
        for idx, cell in enumerate(task_column):
            index = idx + 1
            if index == 1:
                continue
            if cell == str():
                indexes.append((start_index, index - 1))
                start_index = index + 1
            if index == len(task_column):
                indexes.append((start_index, index))

        groups = dict()
        group_names = ['productive', 'alternative', 'analytical']
        for idx, g in enumerate(group_names):
            groups[g] = indexes[idx]

        self._groups = groups

    @property
    def groups(self) -> dict[str, tuple]:
        if self._groups is None:
            self._eval_task_groups()
        return self._groups

    def determine_task_group(self, task_row) -> Union[str, None]:
        for g, indexes in self.groups.items():
            if task_row in range(indexes[0], indexes[1] + 1):
                return g

    def picklify(self):
        folder = settings.BASE_DIR / 'data'
        folder.mkdir(exist_ok=True)
        with open(folder / 'sheet.pickle', 'wb') as file:
            pickle.dump(self.sheet, file)
        with open(folder / 'data.pickle', 'wb') as file:
            pickle.dump(self.data, file)

    def unpicklify(self):
        folder = settings.BASE_DIR / 'data'
        folder.mkdir(exist_ok=True)
        with open(folder / 'sheet.pickle', 'rb') as file:
            self.sheet = pickle.load(file)
        with open(folder / 'data.pickle', 'rb') as file:
            self.data = pickle.load(file)

    def renew_tasks(self):
        task_columns = self.get_col_cells('A')
        while not task_columns[-1]:
            task_columns.pop()

        existing_tasks = {task.name: {'task': task, 'found': False} for task in self.tasks}
        to_create_tasks = list()
        for idx, cell in enumerate(task_columns):
            index = idx + 1
            if index == 1 or cell == str():
                continue

            group = self.determine_task_group(index)
            if group == 'analytical':
                break

            genre = cell.split(': ')[0] if ': ' in cell else ''
            found = False
            for name, kw in existing_tasks.items():
                if name == cell:
                    task = kw['task']
                    if not task.genre and genre:
                        task.genre = genre
                    task.row = index
                    task.archived = False
                    task.group = group
                    kw['found'] = True
                    found = True
                    break
            if not found:
                to_create_tasks.append(Task(name=cell, row=index, group=group, genre=genre))

        for kw in existing_tasks.values():
            task = kw['task']
            if not kw['found']:
                task.archived = True

        Task.objects.bulk_update([t['task'] for t in existing_tasks.values()], ['row', 'archived', 'group', 'genre'])
        Task.objects.bulk_create(to_create_tasks)

    @property
    def tasks(self):
        return Task.objects.all()

    @classmethod
    def create_initial_entries(cls):
        start_date: date = datetime.strptime('2022 30 July', '%Y %d %B').date()
        end_date: date = timezone.localdate() - timedelta(days=1)
        days = (end_date - start_date).days

        task_name_to_duration_map = {
            'yoga': timedelta(minutes=40), 'study': timedelta(hours=3), 'note taking book': timedelta(minutes=10),
            'instagram code': timedelta(hours=1, minutes=30), 'instagram course': timedelta(minutes=30),
            'stocker code': timedelta(hours=1), 'duolingo': timedelta(minutes=10),
            'speed reading': timedelta(minutes=20), 'refind articles': timedelta(minutes=10),
            'etcetera': timedelta(hours=1)
        }
        tasks = Task.objects.all()
        entries: list[Entry] = list()
        for idx in range(0, days + 1):
            for task in tasks:
                if task.name not in task_name_to_duration_map:
                    continue
                entries.append(Entry(
                    task=task,
                    duration=task_name_to_duration_map[task.name],
                    date=start_date + timedelta(days=idx),
                    progress=100
                ))
        return Entry.objects.bulk_create(entries)

    def create_entries(self, today: bool = True):
        now = timezone.localtime()
        entry_date = now.date() if today else now.date() - timedelta(days=1)
        
        tasks = self.tasks.filter(archived=False)
        to_create_entries = list()
        for task in tasks:
            cell = self.get_cell(f'D{task.row}')
            if not cell.strip():
                continue
            duration = timedelta_from_str(cell)
            if not duration:
                continue

            to_create_entries.append(Entry(task=task, duration=duration, date=entry_date))

        existing_entries = Entry.objects.filter(date=entry_date).values_list('task_id', flat=True)
        to_create_entries = [entry for entry in to_create_entries if entry.task_id not in existing_entries]
        Entry.objects.bulk_create(to_create_entries, ignore_conflicts=True)

        to_update_entries = [entry for entry in to_create_entries if entry.task_id in existing_entries]
        Entry.objects.bulk_update(to_update_entries, ['duration'])

        Entry.eval_all_progress()

    def update_average_cells(self):
        tasks = self.tasks.filter(archived=False).order_by('row')
        for task in tasks:
            average = task.average()
            if not average:
                duration = self.get_cell(f'B{task.row}')
            else:
                duration = stringify_timedelta(average)

            self.sheet.update_acell(f'F{task.row}', self.get_cell(f'D{task.row}'))
            self.sheet.update_acell(f'D{task.row}', str())
            self.sheet.update_acell(f'B{task.row}', duration)

    def eval_average_spent_time(self):
        indexes = self.groups['analytical']
        row_range = list(range(indexes[0], indexes[-1] + 1))

        daily = stringify_timedelta(Entry.eval_average_spent_time('daily'))
        self.sheet.update_acell(f'B{row_range[-8]}', daily)
        daily = stringify_timedelta(Entry.eval_average_spent_time('daily', alternatives=True))
        self.sheet.update_acell(f'B{row_range[-3]}', daily)

        weekly = stringify_timedelta(Entry.eval_average_spent_time('weekly'))
        self.sheet.update_acell(f'B{row_range[-7]}', weekly)
        weekly = stringify_timedelta(Entry.eval_average_spent_time('weekly', alternatives=True))
        self.sheet.update_acell(f'B{row_range[-2]}', weekly)

        monthly = stringify_timedelta(Entry.eval_average_spent_time('monthly'))
        self.sheet.update_acell(f'B{row_range[-6]}', monthly)
        monthly = stringify_timedelta(Entry.eval_average_spent_time('monthly', alternatives=True))
        self.sheet.update_acell(f'B{row_range[-1]}', monthly)

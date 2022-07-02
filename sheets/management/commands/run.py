from argparse import ArgumentParser
from sheets.client.script import ProdClient
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Runs the regular tasks.'

    @staticmethod
    def bool(arg_string: str) -> bool:
        if arg_string in ['true', 'True', 'T', 't', '1']:
            return True
        elif arg_string in ['false', 'False', 'f', 'F', '0']:
            return False
        raise ValueError(f"value `{arg_string}` is not of type bool.")

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('-t', '--today', type=self.bool, default="True", required=False)

    def handle(self, *args, **options):
        client = ProdClient()
        client.setup()
        client.renew_tasks()
        client.create_entries(options['today'])
        client.update_average_cells()
        client.eval_average_spent_time()
        self.stdout.write(self.style.SUCCESS('Successful!'))

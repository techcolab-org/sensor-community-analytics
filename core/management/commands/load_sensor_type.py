import os

from django.core.management import BaseCommand, call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Load sensor type data'

    def handle(self, *args, **options):
        fixture_path = os.path.join(settings.BASE_DIR, 'sensolog', 'fixtures', 'sensor_type.json')
        call_command('loaddata', fixture_path)


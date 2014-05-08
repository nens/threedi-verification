import logging
import os
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from threedi_verification.models import LibraryVersion
from threedi_verification.models import TestCase
LIBRARY_LOCATION = '/opt/3di/bin/subgridf90'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Import configuration from testbank directory"

    def handle(self, *args, **options):
        self.look_at_test_cases()

    def look_at_test_cases(self):
        for dirpath, dirnames, filenames in os.walk(settings.TESTCASES_ROOT):
            mdu_filenames = [f for f in filenames if f.endswith('.mdu')]
            for mdu_filename in mdu_filenames:
                full_path = os.path.join(dirpath, mdu_filename)
                relative_path = os.path.relpath(full_path,
                                                settings.TESTCASES_ROOT)
                if TestCase.objects.filter(
                        filename=relative_path).exists():
                    continue
                test_case = TestCase.objects.create(
                    filename=relative_path)
                logger.info("Found new testcase: %s", test_case)
                index_file = os.path.join(dirpath, 'index.txt')
                if os.path.exists(index_file):
                    test_case.info = open(index_file).read()
                    test_case.save()

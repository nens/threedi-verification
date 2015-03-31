import logging
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from threedi_verification.models import TestCase

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Import configuration from testbank directory"

    def handle(self, *args, **options):
        self.look_at_test_cases()

    def look_at_test_cases(self):
        """Import/update the (new) test cases"""
        existing = TestCase.objects.all().values_list('id', flat=True)
        found = []
        for dirpath, dirnames, filenames in os.walk(settings.TESTCASES_ROOT):
            mdu_filenames = [f for f in filenames if f.endswith('.mdu')]
            for mdu_filename in mdu_filenames:
                full_path = os.path.join(dirpath, mdu_filename)
                relative_path = os.path.relpath(full_path,
                                                settings.TESTCASES_ROOT)
                if TestCase.objects.filter(
                        path=relative_path).exists():
                    test_case = TestCase.objects.get(path=relative_path)
                    test_case.is_active = True
                    test_case.save()
                    found.append(test_case.id)
                    continue
                test_case = TestCase.objects.create(
                    path=relative_path)
                logger.info("Found new testcase: %s", test_case)
                index_file = os.path.join(dirpath, 'index.txt')
                if os.path.exists(index_file):
                    test_case.info = open(index_file).read()
                    test_case.save()
                found.append(test_case.id)
        not_active_anymore = set(existing) - set(found)
        for id in not_active_anymore:
            test_case = TestCase.objects.get(id=id)
            test_case.is_active = False
            test_case.save()

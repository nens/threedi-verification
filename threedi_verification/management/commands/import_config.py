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
        self.look_at_library()
        self.look_at_test_cases()

    def look_at_library(self):
        modification_timestamp = os.path.getmtime(LIBRARY_LOCATION)
        last_modified = datetime.datetime.fromtimestamp(
            modification_timestamp)
        library_version, created = LibraryVersion.objects.get_or_create(
            last_modified=last_modified)
        if created:
            logger.info("Found new library version: %s", library_version)

    def look_at_test_cases(self):
        for dirpath, dirnames, filenames in os.walk(settings.TESTCASES_ROOT):
            mdu_filenames = [f for f in filenames if f.endswith('.mdu')]
            for mdu_filename in mdu_filenames:
                full_path = os.path.join(dirpath, mdu_filename)
                relative_path = os.path.relpath(full_path,
                                                settings.TESTCASES_ROOT)
                modification_timestamp = os.path.getmtime(dirpath)
                # ^^^ modification date of the whole directory. Note: doesn't
                # work well when there's stuff in a subdirectory.
                last_modified = datetime.datetime.fromtimestamp(
                    modification_timestamp)
                if not TestCase.objects.filter(
                        filename=relative_path).exists():
                    test_case = TestCase.objects.create(
                        filename=relative_path,
                        last_modified=last_modified)
                    logger.info("Found new testcase: %s", test_case)
                else:
                    test_case = TestCase.objects.get(filename=relative_path)
                if last_modified != test_case.last_modified:
                    logger.info("Updating %s from %s to %s",
                                test_case,
                                test_case.last_modified,
                                last_modified)
                    test_case.last_modified = last_modified
                index_file = os.path.join(dirpath, 'index.txt')
                if os.path.exists(index_file):
                    test_case.info = open(index_file).readlines()

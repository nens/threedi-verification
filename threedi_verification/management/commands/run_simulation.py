import datetime
import logging
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from threedi_verification.models import LibraryVersion
from threedi_verification.models import TestCase
from threedi_verification.models import TestRun
from threedi_verification import verification

LIBRARY_LOCATION = '/opt/3di/bin/subgridf90'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = "FULL_PATH_TO_TEST_DIR"
    help = "Run one subgrid simulation"

    def handle(self, *args, **options):
        if not len(args) == 1 or not args[0].endswith('.mdu'):
            logger.error("Pass one full pathname to an .mdu file")
            sys.exit(1)
        self.full_path = os.path.abspath(args[0])

        self.look_at_library()
        self.look_at_test_case()
        self.set_up_test_run()
        if self.test_run is None:
            return
        self.run_simulation()

    def look_at_library(self):
        modification_timestamp = os.path.getmtime(LIBRARY_LOCATION)
        last_modified = datetime.datetime.fromtimestamp(
            modification_timestamp)
        self.library_version, created = LibraryVersion.objects.get_or_create(
            last_modified=last_modified)
        if created:
            logger.info("Found new library version: %s", self.library_version)

    def look_at_test_case(self):
        testdir = os.path.dirname(self.full_path)
        relative_path = os.path.relpath(testdir,
                                        settings.TESTCASES_ROOT)
        modification_timestamp = os.path.getmtime(testdir)
        # ^^^ modification date of the whole directory. Note: doesn't
        # work well when there's stuff in a subdirectory.
        last_modified = datetime.datetime.fromtimestamp(
            modification_timestamp)
        if not TestCase.objects.filter(
                filename=relative_path).exists():
            self.test_case = TestCase.objects.create(
                filename=relative_path,
                last_modified=last_modified)
            logger.info("Found new testcase: %s", self.test_case)
        else:
            self.test_case = TestCase.objects.get(filename=relative_path)
        if last_modified != self.test_case.last_modified:
            logger.info("Updating %s from %s to %s",
                        self.test_case,
                        self.test_case.last_modified,
                        last_modified)
            self.test_case.last_modified = last_modified
        index_file = os.path.join(testdir, 'index.txt')
        if os.path.exists(index_file):
            self.test_case.info = open(index_file).readlines()

    def set_up_test_run(self):
        """Set up the storage object for the test that need to be run."""
        datetime_needed = max(self.test_case.last_modified,
                              self.library_version.last_modified)
        if TestRun.objects.filter(
                test_case=self.test_case,
                run_started__gte=datetime_needed).exists():
            logger.info("Test run for %s has already run earlier",
                        self.test_case)
            self.test_run = None
            return
        logger.info("Setting up a new test run for %s", self.test_case)
        self.test_run = TestRun.objects.create(
            test_case=self.test_case,
            library_version=self.library_version)

    def run_simulation(self):
        report = verification.Report()
        verification.run_simulation(self.full_path, report)
        print(report)

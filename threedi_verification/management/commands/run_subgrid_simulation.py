import datetime
import glob
import logging
import optparse
import os
import sys
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from threedi_verification.models import LibraryVersion
from threedi_verification.models import TestCase
from threedi_verification.models import TestCaseVersion
from threedi_verification.models import TestRun
from threedi_verification import verification
from threedi_verification.models import SUBGRID


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = "mdu file"
    help = "Run one subgrid simulation"
    option_list = BaseCommand.option_list + (
        optparse.make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Force test run"),
        )

    def handle(self, *args, **options):
        if not len(args) == 1 or not args[0].endswith('.mdu'):
            logger.error("Pass one full pathname to an .mdu file")
            sys.exit(1)
        self.full_path = os.path.abspath(args[0])

        self.look_at_library()
        self.look_at_test_case()
        if not self.test_case.has_csv:
            logger.error("No csv files, aborting.")
            return
        self.set_up_test_run(force=options['force'])
        if self.test_run is None:
            return
        self.run_simulation()

    def look_at_library(self):
        """Look at the library and create a new library version, if needed"""
        modification_timestamp = os.path.getmtime(
            settings.SUBGRID_LIBRARY_LOCATION)
        last_modified = datetime.datetime.fromtimestamp(
            modification_timestamp)
        self.library_version, created = LibraryVersion.objects.get_or_create(
            library=SUBGRID, last_modified=last_modified)
        if created:
            logger.info("Found new library version: %s", self.library_version)
            num_mdu_files = 0
            for dirpath, dirnames, filenames in os.walk(
                    settings.TESTCASES_ROOT):
                num_mdu_files += len(
                    [f for f in filenames if f.endswith('.mdu')])
            self.library_version.num_test_cases = num_mdu_files

    def look_at_test_case(self):
        """Look at the test case and create a new TestCaseVersion, if needed"""
        testdir = os.path.dirname(self.full_path)
        relative_path = os.path.relpath(self.full_path,
                                        settings.TESTCASES_ROOT)
        self.test_case = TestCase.objects.get(path=relative_path)

        modification_timestamp = max([
            os.path.getmtime(os.path.join(testdir, filename))
            for filename in os.listdir(testdir)
            if not (filename.endswith('.dia') or
                    filename.startswith('fort.'))])
        last_modified = datetime.datetime.fromtimestamp(
            modification_timestamp)

        if not TestCaseVersion.objects.filter(
                test_case=self.test_case,
                last_modified=last_modified).exists():
            self.test_case_version = TestCaseVersion.objects.create(
                test_case=self.test_case,
                last_modified=last_modified)
            logger.info("Created new test case version: %s", self.test_case_version)
        else:
            self.test_case_version = TestCaseVersion.objects.get(
                test_case=self.test_case,
                last_modified=last_modified)
        index_file = os.path.join(testdir, 'index.txt')
        if os.path.exists(index_file):
            # Make sure the content is up to date.
            self.test_case.info = open(index_file).read()
        self.test_case.has_csv = bool(glob.glob(
            os.path.join(testdir, '*.csv')))
        self.test_case.save()

    def set_up_test_run(self, force):
        """Set up the storage object for the test that needs to be run."""
        existing_testruns = TestRun.objects.filter(
            test_case_version=self.test_case_version,
            library_version=self.library_version)
        if existing_testruns:
            if force:
                logger.info("Re-running test run because of --force")
                self.test_run = existing_testruns[0]
                return
            elif not existing_testruns[0].duration:
                logger.info(
                    "Test run for %s hasn't completed yet, running again",
                    self.test_case)
                self.test_run = existing_testruns[0]
                return
            else:
                logger.info("Test run for %s has already run earlier",
                            self.test_case)
                self.test_run = None
                return
        logger.info("Setting up a new test run for %s", self.test_case_version)
        self.test_run = TestRun.objects.create(
            test_case_version=self.test_case_version,
            library_version=self.library_version)

    def run_simulation(self):
        mdu_report = verification.MduReport(self.full_path)
        start_time = time.time()
        verification.run_subgrid_simulation(self.full_path, mdu_report)
        self.test_run.duration = (time.time() - start_time)
        self.test_run.report = mdu_report.as_dict()
        self.test_run.save()

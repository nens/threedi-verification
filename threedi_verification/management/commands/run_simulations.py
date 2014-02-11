import logging
import os
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from threedi_verification.models import LibraryVersion
from threedi_verification.models import TestCase
from threedi_verification.models import TestRun
LIBRARY_LOCATION = '/opt/3di/bin/subgridf90'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Run the subgrid simulations"

    def handle(self, *args, **options):
        self.set_up_test_runs()
        self.run_simulations()

    def set_up_test_runs(self):
        """Set up tests that need to be run."""
        library_version = LibraryVersion.objects.all().first()
        for test_case in TestCase.objects.all():
            datetime_needed = max(test_case.last_modified,
                                  library_version.last_modified)
            if TestRun.objects.filter(
                    test_case=test_case,
                    run_started__gte=datetime_needed).exists():
                continue
            logger.info("Setting up a new test run for %s", test_case)
            TestRun.objects.create(
                test_case=test_case,
                library_version=library_version)

    def run_simulations(self):
        library_version = LibraryVersion.objects.all().first()
        # ^^^ Only run tests with the latest library version.
        for test_run in TestRun.objects.filter(
                library_version=library_version,
                duration=None):
            print(test_run)

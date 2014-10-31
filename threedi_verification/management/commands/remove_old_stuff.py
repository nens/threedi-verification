import datetime
import logging
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from threedi_verification.models import TestRun
LIBRARY_LOCATION = '/opt/3di/bin/subgridf90'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Remove test results that are more than a month old."

    def handle(self, *args, **options):
        self.remove_old_test_results()

    def remove_old_test_results(self):
        now = datetime.datetime.now()
        month_ago = now - datetime.timedelta(days=30)
        old_test_runs = TestRun.objects.filter(run_started__lt=month_ago)[:500]
        # Max 500 as zapping all of them takes forever.
        logger.info("Removing %s old test runs", len(old_test_runs))
        for old_test_run in old_test_runs:
            logger.debug("Removing %s", old_test_run)
            old_test_run.delete()

import logging
import os
import datetime

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from threedi_verification.models import TestCase
LIBRARY_LOCATION = '/opt/3di/bin/subgridf90'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Run the subgrid simulations"

    def handle(self, *args, **options):
        testdir = settings.TESTCASES_ROOT
        for test_case in TestCase.objects.all():
            full_path = os.path.join(testdir, test_case.filename)
            if not os.path.exists(full_path):
                logger.error("MDU file at %s doesn't exist anymore...",
                             full_path)
                continue
            call_command('run_simulation', full_path)

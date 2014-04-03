import logging
import os
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

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
            cmd = "bin/django run_simulation %s" % full_path
            os.system(cmd)

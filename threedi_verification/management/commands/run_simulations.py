import logging
import os
import optparse

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from threedi_verification.models import TestCase

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Run the subgrid simulations"

    option_list = BaseCommand.option_list + (
        optparse.make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Force all test runs"),
        optparse.make_option(
            '--limit',
            dest='limit',
            default=None,
            help="Limit test runs to testcase matching string passed"),
        )

    def handle(self, *args, **options):
        testdir = settings.TESTCASES_ROOT
        for test_case in TestCase.objects.all():
            full_path = os.path.join(testdir, test_case.filename)
            if not os.path.exists(full_path):
                logger.error("MDU file at %s doesn't exist anymore...",
                             full_path)
                continue
            if options['limit'] and (options['limit'] not in full_path):
                continue
            call_command('run_subgrid_simulation', full_path, force=options['force'])

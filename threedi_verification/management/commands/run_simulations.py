import logging
import os
import optparse

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from threedi_verification.models import TestCase
from threedi_verification.models import (SUBGRID, FLOW)

logger = logging.getLogger(__name__)
subgrid_testcases_dir = settings.TESTCASES_ROOT
flow_testcases_dir = settings.URBAN_TESTCASES_ROOT


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
        optparse.make_option(
            '--subgrid',
            action='store_true',
            dest='subgrid',
            default=False,
            help="Run subgrid simulations"),
        optparse.make_option(
            '--flow',
            action='store_true',
            dest='flow',
            default=False,
            help="Run flow simulations"),
        )

    def handle(self, *args, **options):
        if options['subgrid']:
            for test_case in TestCase.objects.filter(library=SUBGRID):
                full_path = os.path.join(subgrid_testcases_dir, test_case.path)
                if not os.path.exists(full_path):
                    logger.error("Path %s doesn't exist anymore...", full_path)
                    continue
                if options['limit'] and (options['limit'] not in full_path):
                    continue
                call_command('run_subgrid_simulation', full_path,
                             force=options['force'])
        if options['flow']:
            for test_case in TestCase.objects.filter(library=FLOW):
                full_path = os.path.join(flow_testcases_dir, test_case.path)
                if not os.path.exists(full_path):
                    logger.error("Path %s doesn't exist anymore...", full_path)
                    continue
                if options['limit'] and (options['limit'] not in full_path):
                    continue
                call_command('run_flow_simulation', full_path,
                             force=options['force'])

from __future__ import absolute_import

import logging
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from threedi_verification.models import TestCase
from threedi_verification.models import (SUBGRID, FLOW)

logger = logging.getLogger(__name__)

subgrid_testcases_dir = settings.TESTCASES_ROOT
flow_testcases_dir = settings.URBAN_TESTCASES_ROOT

# the definition of a flow model, i.e., it must contain these dirs
FLOW_REQUIRED_DIRS = {'input_generated', 'model'}


class Command(BaseCommand):
    args = ""
    help = "Import configuration from testbank directory"

    def handle(self, *args, **options):
        self.look_at_subgrid_test_cases()
        self.look_at_flow_test_cases()

    def look_at_subgrid_test_cases(self):
        """Import and/or update the (new) subgrid test cases"""
        existing = TestCase.objects.filter(library=SUBGRID).values_list(
            'id', flat=True)
        found = []
        for dirpath, dirnames, filenames in os.walk(subgrid_testcases_dir):
            mdu_filenames = [f for f in filenames if f.endswith('.mdu')]
            for mdu_filename in mdu_filenames:
                full_path = os.path.join(dirpath, mdu_filename)
                relative_path = os.path.relpath(full_path,
                                                subgrid_testcases_dir)
                if TestCase.objects.filter(path=relative_path).exists():
                    test_case = TestCase.objects.get(path=relative_path)
                    test_case.is_active = True
                    test_case.save()
                    found.append(test_case.id)
                    continue
                test_case = TestCase.objects.create(
                    path=relative_path, library=SUBGRID)
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

    def look_at_flow_test_cases(self):
        """Import/update flow test cases"""
        existing = TestCase.objects.filter(library=FLOW).values_list('id',
                                                                     flat=True)
        found = []
        for dir_path, dirs, files in os.walk(flow_testcases_dir):
            # if the dir_path has required dirs, assume it is a model dir
            has_required_dirs = FLOW_REQUIRED_DIRS.issubset(set(dirs))
            if has_required_dirs:
                relative_path = os.path.relpath(dir_path, flow_testcases_dir)
                if TestCase.objects.filter(path=relative_path).exists():
                    test_case = TestCase.objects.get(path=relative_path)
                    test_case.is_active = True
                    test_case.save()
                    found.append(test_case.id)
                    continue
                test_case = TestCase.objects.create(path=relative_path,
                                                    library=FLOW)
                logger.info("Found new testcase: %s", test_case)
                index_file = os.path.join(dir_path, 'index.txt')
                if os.path.exists(index_file):
                    test_case.info = open(index_file).read()
                    test_case.save()
                found.append(test_case.id)

        # check if existing db models are on disk, make inactive when not
        not_active_anymore = set(existing) - set(found)
        for id in not_active_anymore:
            test_case = TestCase.objects.get(id=id)
            test_case.is_active = False
            test_case.save()

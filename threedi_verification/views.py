# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from collections import OrderedDict
import itertools
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView

from threedi_verification.models import LibraryVersion
from threedi_verification.models import TestCase
from threedi_verification.models import TestRun

logger = logging.getLogger(__name__)


class BaseView(TemplateView):
    template_name = 'threedi_verification/base.html'
    title = _("3Di library test")
    subtitle = None
    back_link = None
    back_link_title = None


class HomeView(BaseView):
    template_name = 'threedi_verification/home.html'
    subtitle = _("overview")


class LibraryVersionsView(BaseView):
    template_name = 'threedi_verification/library_versions.html'
    title = _("Library versions")
    subtitle = _("newest at the top")
    back_link_title = _("Back to home")

    @property
    def back_link(self):
        return reverse('threedi_verification.home')

    def library_versions(self):
        return LibraryVersion.objects.all()


class LibraryVersionView(BaseView):
    template_name = 'threedi_verification/library_version.html'
    title = _("Library version")
    back_link_title = _("Back to library versions overview")

    @property
    def back_link(self):
        return reverse('threedi_verification.library_versions')

    @cached_property
    def library_version(self):
        return get_object_or_404(LibraryVersion, pk=self.kwargs['pk'])

    @cached_property
    def subtitle(self):
        return 'from %s' % self.library_version.last_modified

    @cached_property
    def all_test_runs(self):
        return self.library_version.test_runs.all().order_by(
            'test_case_version__test_case', '-run_started')

    @cached_property
    def crashed_test_runs(self):
        return [test_run for test_run in self.all_test_runs
                if test_run.has_crashed]

    @cached_property
    def completed_test_runs(self):
        test_runs = [test_run for test_run in self.all_test_runs
                     if (not test_run.has_crashed) and test_run.duration]
        per_test_case = OrderedDict()
        for test_case, group in itertools.groupby(
                test_runs, lambda test_run: test_run.test_case_version.test_case):
            per_test_case[test_case] = list(group)
        return per_test_case


class TestCasesView(BaseView):
    template_name = 'threedi_verification/test_cases.html'
    title = _("Test cases")
    back_link_title = _("Back to home")

    @property
    def back_link(self):
        return reverse('threedi_verification.home')

    def test_cases(self):
        return TestCase.objects.all()


class TestCaseView(BaseView):
    template_name = 'threedi_verification/test_case.html'
    back_link_title = _("Back to test cases overview")

    @property
    def back_link(self):
        return reverse('threedi_verification.test_cases')

    @cached_property
    def title(self):
        return _("Test case %s") % self.test_case.pretty_name

    @cached_property
    def test_case(self):
        return get_object_or_404(TestCase, pk=self.kwargs['pk'])

    @cached_property
    def grouped_test_runs(self):
        per_test_case_version = OrderedDict()
        test_case_versions = self.test_case.test_case_versions.all().order_by(
            '-last_modified')
        for test_case_version in test_case_versions:
            test_runs = test_case_version.test_runs.all().order_by(
                'library_version')
            per_test_case_version[test_case_version] = list(test_runs)
        return per_test_case_version


class TestRunView(BaseView):
    template_name = 'threedi_verification/test_run.html'
    title = _("Test run")
    back_link_title = _("Back to library version")

    @property
    def back_link(self):
        return reverse('threedi_verification.library_version',
                       kwargs={'pk': self.test_run.library_version.pk})

    @cached_property
    def test_run(self):
        return get_object_or_404(TestRun, pk=self.kwargs['pk'])

    @cached_property
    def subtitle(self):
        return 'for %s' % self.test_run.test_case_version

    @cached_property
    def report(self):
        return self.test_run.report


def plain_log(request, pk=None):
    test_run = TestRun.objects.get(pk=pk)
    crash_content = test_run.report.get('log')
    regular_content = test_run.report.get('successfully_loaded_log')
    content = crash_content or regular_content
    return HttpResponse(content, content_type='text/plain')

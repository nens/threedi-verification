# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import logging

from django.db.models import Count
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView

from threedi_verification.models import LibraryVersion
from threedi_verification.models import TestCase

logger = logging.getLogger(__name__)


class BaseView(TemplateView):
    template_name = 'threedi_verification/base.html'
    title = _("3Di library test")
    subtitle = None


class HomeView(BaseView):
    template_name = 'threedi_verification/home.html'
    subtitle = _("overview")

    def fully_tested_library_versions(self):
        """Return latest three fully tested library versions."""
        return LibraryVersion.objects.annotate(
            num_test_runs=Count('test_runs')).filter(
                num_test_runs__gte=F('num_test_cases'))[:3]


class LibraryVersionsView(BaseView):
    template_name = 'threedi_verification/library_versions.html'
    title = _("Library versions")

    def library_versions(self):
        return LibraryVersion.objects.all()


class LibraryVersionView(BaseView):
    template_name = 'threedi_verification/library_version.html'
    title = _("Library version")

    @cached_property
    def subtitle(self):
        return 'from %s' % self.library_version.last_modified

    @cached_property
    def library_version(self):
        return get_object_or_404(LibraryVersion, pk=self.kwargs['pk'])



class TestCasesView(BaseView):
    template_name = 'threedi_verification/test_cases.html'
    title = _("Test cases")

    def test_cases(self):
        return TestCase.objects.all()

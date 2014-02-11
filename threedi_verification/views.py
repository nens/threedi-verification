# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import logging

from django.views.generic.base import TemplateView
from django.utils.translation import ugettext as _

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


class LibraryVersionsView(BaseView):
    template_name = 'threedi_verification/library_versions.html'
    title = _("Library versions")

    def library_versions(self):
        return LibraryVersion.objects.all()


class TestCasesView(BaseView):
    template_name = 'threedi_verification/test_cases.html'
    title = _("Test cases")

    def test_cases(self):
        return TestCase.objects.all()

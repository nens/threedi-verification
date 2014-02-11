# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import logging

from django.views.generic.base import TemplateView
from django.utils.translation import ugettext as _


logger = logging.getLogger(__name__)


class BaseView(TemplateView):
    template_name = 'threedi_verification/base.html'
    title = _("3Di library test")
    subtitle = None


class HomeView(BaseView):
    template_name = 'threedi_verification/home.html'
    subtitle = _("overview")

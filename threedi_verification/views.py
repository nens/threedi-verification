import logging

from django.views.generic.base import TemplateView


logger = logging.getLogger(__name__)


class BaseView(TemplateView):
    template_name = 'threedi_verification/base.html'
    title = "3Di testbank"
    subtitle = None


class HomeView(BaseView):
    template_name = 'threedi_verification/home.html'
    subtitle = "overzicht"

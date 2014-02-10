import logging

from django.core.management.base import BaseCommand

from threedi_verification import models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Import configuration from testbank directory"

    def handle(self, *args, **options):
        pass

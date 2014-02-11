import logging
import os
import datetime

from django.core.management.base import BaseCommand

from threedi_verification.models import LibraryVersion

LIBRARY_LOCATION = '/opt/3di/bin/subgridf90'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Import configuration from testbank directory"

    def handle(self, *args, **options):
        self.look_at_library()

    def look_at_library(self):
        modification_timestamp = os.path.getmtime(LIBRARY_LOCATION)
        last_modified = datetime.datetime.fromtimestamp(
            modification_timestamp)
        library_version, created = LibraryVersion.objects.get_or_create(
            last_modified=last_modified)
        if created:
            logger.info("Found new library version: %s", library_version)

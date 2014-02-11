import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


class TestCase(models.Model):

    filename = models.CharField(
        verbose_name=_("filename"),
        unique=True,
        help_text=_(
            "CSV filename, including path, inside the 'testbank' directory"),
        max_length=255)
    last_modified = models.DateTimeField(
        verbose_name=_("last modified"),
        auto_now_add=True)  # auto_now_add just for easy testing.

    class Meta:
        verbose_name = _("test case")
        verbose_name_plural = _("test cases")
        ordering = ['filename']


class LibraryVersion(models.Model):

    last_modified = models.DateTimeField(
        verbose_name=_("last modified"),
        auto_now_add=True)  # auto_now_add just for easy testing.

    class Meta:
        verbose_name = _("library")
        verbose_name_plural = _("libraries")
        ordering = ['-last_modified']


class TestRun(models.Model):

    test_case = models.ForeignKey(
        TestCase,
        verbose_name=_("test case"))
    library_version = models.ForeignKey(
        LibraryVersion,
        verbose_name=_("library version"))
    run_started = models.DateTimeField(
        verbose_name=_("start of test run"),
        auto_now_add=True)  # auto_now_add just for easy testing.
    duration = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("duration"))

    class Meta:
        verbose_name = _("test run")
        verbose_name_plural = _("test runs")
        ordering = ['-run_started']

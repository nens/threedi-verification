# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _
import jsonfield


logger = logging.getLogger(__name__)


class TestCase(models.Model):

    filename = models.CharField(
        verbose_name=_("filename"),
        unique=True,
        help_text=_(
            "MDU filename, including path, inside the 'testbank' directory"),
        max_length=255)
    last_modified = models.DateTimeField(
        verbose_name=_("last modified"))
    info = models.TextField(
        verbose_name=_("information"),
        blank=True,
        null=True)

    class Meta:
        verbose_name = _("test case")
        verbose_name_plural = _("test cases")
        ordering = ['filename']

    def __unicode__(self):
        return _("test case %s") % self.filename


class LibraryVersion(models.Model):

    last_modified = models.DateTimeField(
        unique=True,
        verbose_name=_("last modified"))
    num_test_cases = models.IntegerField(
        default = 0,
        verbose_name=_("number of test cases when library was first found"))

    class Meta:
        verbose_name = _("library")
        verbose_name_plural = _("libraries")
        ordering = ['-last_modified']

    def __unicode__(self):
        return _("library version of %s") % self.last_modified

    def is_fully_tested(self):
        """Have we been fully tested?

        This means: have all the test cases that were present when the library
        was first found actually been run? Perhaps a newer version was found
        halfway the tests, if so, this library version can mostly be omitted.
        """
        return self.test_runs.all().count() >= self.num_test_cases


class TestRun(models.Model):

    test_case = models.ForeignKey(
        TestCase,
        verbose_name=_("test case"),
        related_name='test_runs')
    library_version = models.ForeignKey(
        LibraryVersion,
        verbose_name=_("library version"),
        related_name='test_runs')
    run_started = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("start of test run"))
    duration = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("duration"))
    report = jsonfield.JSONField()

    class Meta:
        verbose_name = _("test run")
        verbose_name_plural = _("test runs")
        ordering = ['-run_started']

    def __unicode__(self):
        return _("test run %s") % self.id

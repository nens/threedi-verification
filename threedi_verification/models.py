# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import logging

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
import jsonfield


logger = logging.getLogger(__name__)

# four characters max
SUBGRID = 'SUBG'
FLOW = 'FLOW'
LIBRARIES = (
    (SUBGRID, 'Subgrid'),
    (FLOW, 'Flow'),
)


class TestCase(models.Model):

    path = models.CharField(
        verbose_name=_("path"),
        unique=True,
        help_text=_("Path to model input (mdu or other input, e.g., a model "
                    "dir), inside the 'testbank' directory"),
        max_length=255)
    library = models.CharField(
        max_length=4,
        choices=LIBRARIES,
        default=SUBGRID)
    info = models.TextField(
        verbose_name=_("information"),
        blank=True,
        null=True)
    has_csv = models.BooleanField(
        default=True,
        verbose_name=_("has .csv file with instructions"))
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("is active: directory still exists"))

    class Meta:
        verbose_name = _("test case")
        verbose_name_plural = _("test cases")
        ordering = ['path']

    def __unicode__(self):
        return _("test case %s") % self.path

    def get_absolute_url(self):
        return reverse('threedi_verification.test_case',
                       kwargs={'pk': self.pk})

    @cached_property
    def pretty_name(self):
        name = self.path.split('/')[-1]
        if self.library == SUBGRID:
            name = name.rstrip('.mdu')
        if self.info:
            first_line = self.info.split('\n')[0].strip()
            return "%s (%s)" % (first_line, name)
        else:
            return name

    @cached_property
    def latest_test_run(self):
        test_runs = TestRun.objects.filter(
            test_case_version__test_case=self)
        if test_runs.exists():
            return test_runs.first()

    @cached_property
    def library_name(self):
        return dict(LIBRARIES).get(self.library)


class TestCaseVersion(models.Model):

    test_case = models.ForeignKey(
        TestCase,
        verbose_name=_("test case"),
        related_name='test_case_versions')

    last_modified = models.DateTimeField(
        verbose_name=_("last modified"))

    class Meta:
        verbose_name = _("test case version")
        verbose_name_plural = _("test case versions")
        ordering = ['test_case', 'last_modified']

    def __unicode__(self):
        return _("version %s of %s") % (self.last_modified,
                                        self.test_case.pretty_name)

    def get_absolute_url(self):
        return reverse('threedi_verification.test_case',
                       kwargs={'pk': self.pk})


class LibraryVersion(models.Model):

    library = models.CharField(
        max_length=4,
        choices=LIBRARIES,
        default=SUBGRID)
    last_modified = models.DateTimeField(
        unique=True,
        verbose_name=_("last modified"))
    num_test_cases = models.IntegerField(
        default=0,
        verbose_name=_("number of test cases when library was first found"))

    class Meta:
        verbose_name = _("library version")
        verbose_name_plural = _("library versions")
        ordering = ['-last_modified']

    def __unicode__(self):
        return _("%s library version of %s") % (self.library_name,
                                                self.last_modified)

    def get_absolute_url(self):
        return reverse('threedi_verification.library_version',
                       kwargs={'pk': self.pk})

    def is_fully_tested(self):
        """Have we been fully tested?

        This means: have all the test cases that were present when the library
        was first found actually been run? Perhaps a newer version was found
        halfway the tests, if so, this library version can mostly be omitted.
        """
        return self.test_runs.all().count() >= self.num_test_cases

    @cached_property
    def num_crashes(self):
        """Return range for use in a for loop to display 'x' icons."""
        # This one probably needs caching.
        return range(len([test_run for test_run in self.test_runs.filter(
            test_case_version__test_case__has_csv=True)
            if test_run.has_crashed]))

    @cached_property
    def library_name(self):
        return dict(LIBRARIES).get(self.library)


class TestRun(models.Model):

    test_case_version = models.ForeignKey(
        TestCaseVersion,
        verbose_name=_("test case version"),
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

    def get_absolute_url(self):
        return reverse('threedi_verification.test_run',
                       kwargs={'pk': self.pk})

    @cached_property
    def has_crashed(self):
        return bool(self.report.get('log'))

    @cached_property
    def num_wrong(self):
        if 'instruction_reports' not in self.report:
            return 0
        return len(
            [ir for ir in self.report['instruction_reports']
             if not ir['equal']])

    @cached_property
    def num_right(self):
        if 'instruction_reports' not in self.report:
            return 0
        return len(
            [ir for ir in self.report['instruction_reports']
             if ir['equal']])

    @cached_property
    def progress_bar_percentage_right(self):
        if self.num_wrong + self.num_right == 0:  # Division by zero.
            return 0
        return int(100 * self.num_right / (self.num_wrong + self.num_right))

    @cached_property
    def progress_bar_percentage_wrong(self):
        if self.num_wrong + self.num_right == 0:  # Division by zero.
            return 0
        return int(100 * self.num_wrong / (self.num_wrong + self.num_right))

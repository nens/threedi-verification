from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin

from threedi_verification import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$',
        views.HomeView.as_view(),
        name='threedi_verification.home'),

    url(r'^libraries/$',
        views.LibraryVersionsView.as_view(),
        name='threedi_verification.library_versions'),
    url(r'^libraries/(?P<pk>\d+)/$',
        views.LibraryVersionView.as_view(),
        name='threedi_verification.library_version'),

    url(r'^test_run/(?P<pk>\d+)/$',
        views.TestRunView.as_view(),
        name='threedi_verification.test_run'),

    url(r'^test_cases/$',
        views.TestCasesView.as_view(),
        name='threedi_verification.test_cases'),
    url(r'^test_cases/(?P<pk>\d+)/$',
        views.TestCaseView.as_view(),
        name='threedi_verification.test_case'),

    url(r'^log/(?P<pk>\d+)/$',
        views.plain_log,
        name='threedi_verification.log'),
)

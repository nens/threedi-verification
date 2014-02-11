from django.conf.urls import include
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
    url(r'^library_versions/$',
        views.LibraryVersionsView.as_view(),
        name='threedi_verification.library_versions'),
    url(r'^test_cases/$',
        views.TestCasesView.as_view(),
        name='threedi_verification.test_cases'),
    )

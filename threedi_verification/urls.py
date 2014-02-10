from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin

from threedi_verification import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$',
        views.home,
        name='threedi_verification.home'),
    )

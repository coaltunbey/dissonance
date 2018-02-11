from __future__ import unicode_literals

from django.conf.urls import url

from .views import home, post, callback, login, app

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^app/$', app, name='app'),
    url(r'^post/$', post, name='post'),
    url(r'^callback/$', callback, name='callback'),
    url(r'^login/$', login, name='login')
]

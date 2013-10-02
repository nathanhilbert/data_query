# app specific urls
from django.conf.urls import patterns, include, url
from django.views.generic.simple import redirect_to
from django.core.urlresolvers import reverse


urlpatterns = patterns('',
    url(r'^home', 'myfirstapp.views.home'),
    url(r'^questions', 'myfirstapp.views.questions'),
    url(r'^mashup', 'myfirstapp.views.mashup'),
    url(r'^ajax\/gettamis', 'myfirstapp.views.gettamis'),
    url(r'^charts\/gettamis', 'myfirstapp.views.getTamisChartData'),
    url(r'^ajax\/getworldbank', 'myfirstapp.views.getworldbank'),
    url(r'^charts\/getworldbank', 'myfirstapp.views.getChartData'),
    url(r'^ajax\/getgrantdata', 'myfirstapp.views.getGrantsData'),
    
    
)

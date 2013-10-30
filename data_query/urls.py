# app specific urls
from django.conf.urls import patterns, include, url
from django.views.generic.simple import redirect_to
from django.core.urlresolvers import reverse


urlpatterns = patterns('',
    url(r'^home', 'data_query.views.data_query'),
    url(r'^ajax\/queryresults', 'data_query.views.queryresults'),
    url(r'^ajax\/downloadfiles', 'data_query.views.downloadFiles'),
    
    #url(r'^tables', 'avanse.views.tables'),
    # url(r'^upload', 'avanse.views.upload'),
    # url(r'^managesurveys', 'avanse.views.managesurveys'),
    # url(r'^charts\/(?P<chart_type>\w{0,50})', 'avanse.views.charts'),


    
)

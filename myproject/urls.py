# project wide urls
from django.conf.urls import patterns, include, url
from django.views.generic.simple import redirect_to
from django.core.urlresolvers import reverse
from django.contrib import admin
admin.autodiscover()
import settings

# import your urls from each app here, as needed
import avanse.urls

urlpatterns = patterns('',

    # urls specific to this app
    url(r'^myfirstapp/', include(myfirstapp.urls)),
    url(r'^avanse/', include(avanse.urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),

    # catch all, redirect to myfirstapp home view
    url(r'.*', redirect_to, {'url': '/avanse/home'}),

)

import os
import sys

activate_this = os.path.join("D:\\inetpub\\tamis", "Scripts/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))


sys.path.append('D:\\inetpub\\tamis\\formhub_test')
os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
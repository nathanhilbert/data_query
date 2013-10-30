# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt

from lockdown.decorators import lockdown


from data_query.models import Document
from data_query.forms import DocumentForm


import urllib2, base64
import simplejson as json
from pandas import date_range
from datetime import datetime
from StringIO import StringIO
import numpy as np
from pybamboo.dataset import Dataset
import time
from random import randint
import csv
import os
from os.path import join
from django.conf import settings
import pickle
import time
import shutil
import zipfile
from django.conf import settings


from BeautifulSoup import BeautifulSoup as Soup

import psycopg2
#note that we have to import the Psycopg2 extras library!
import psycopg2.extras
import sys

import arcpy

import base64 




SDECONNECTION = "C:/Users/nhilbert/AppData/Roaming/ESRI/Desktop10.1/ArcCatalog/avanse_gis7.sde/"
TEMPDIR = "C:/Temp/"
 




def data_query(request):
    d = {}
    # Render list page with the documents and the form
    return render_to_response(
        'data_query.html',
        d,
        context_instance=RequestContext(request)
    )


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))



def getImageTag(documentation, name, MEDIAFILES):
    thumbs = Soup(documentation).findAll("thumbnail")
    if (len(thumbs) < 1):
        return '<span>No Image</span>'

    #if not os.path.isfile(settings.MEDIA_ROOT + name + '.png'):
    if (name + '.png' not in MEDIAFILES):
        png_recovered = base64.decodestring(thumbs[0].getText())
        with open(settings.MEDIA_ROOT + name + '.png', 'wb') as f:
            f.write(png_recovered)


    if (len(thumbs) > 0):
        return '<img class="thumbimage" src="' +  settings.MEDIA_URL + name + '.png'  + '" alt="Red dot" />'





def drawTableFromGeom(polygon, request):
    conn_string = "host='geodata' dbname='avanse_gis7' user='sde' password='63odata!'"
    # print the connection string we will use to connect
    conn = psycopg2.connect(conn_string)

    text_search = request.GET.get("text_search", "")

    textquerystring = ""
    if text_search != "":
        textquerystring = " and definition::TEXT LIKE '%" + text_search + "%' "
 
    # HERE IS THE IMPORTANT PART, by specifying a name for the cursor
    # psycopg2 creates a server-side cursor, which prevents all of the
    # records from being downloaded at once from the server.
    cursor = conn.cursor('cursor_unique_name', cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT objectid, name, path, documentation FROM sde.gdb_items \
        WHERE (definition::TEXT LIKE '%DEFeatureClassInfo%' or definition::TEXT LIKE '%DERasterDataset%') and \
        sde.st_intersects(sde.st_geometry ('" +  polygon   + "', 0) , shape)=True \
        " + textquerystring + " \
        LIMIT 200")
    outputstring = "<form id='downloadform'>"
    outputstring += "<table>"
    FIELDNAMES = ["objectid", "name", "path"]
    rowcounter = 1
    MEDIAFILES = os.listdir(settings.MEDIA_ROOT) 
    for row in cursor:
        outputstring += "<tr>"

        outputstring += "<td>" + str(rowcounter) + "</td>"
        outputstring += "<td><input id='downloadselect' name='downloadselect' type='checkbox' value='" + str(row[1]) + "'/></td>"
        for thefield in range(len(FIELDNAMES)):
            outputstring += "<td>" + str(row[thefield]) + "</td>"
        #outputstring += "<td>" + getImageTag(row[3], row[1], MEDIAFILES) + "</td>"
        outputstring += "<td><a href='/data/ajax/getxml?name=" + row[1] + "' class='xmllink'>See Metadata</a></td>"
        outputstring += "</tr>"
        rowcounter += 1
    outputstring += "</table>"
    outputstring += "<input type='submit' name='downloadsubmit' value='Download'/>"
    outputstring += "</form>"

    if rowcounter == 1:
        outputstring = "<div>There are no layers in this area</div>"

    return outputstring


def getxml(request):
    search_text = request.GET.get("name", "")
    if search_text == "":
        return
    conn_string = "host='geodata' dbname='avanse_gis7' user='sde' password='63odata!'"
    # print the connection string we will use to connect
    conn = psycopg2.connect(conn_string)

    cursor = conn.cursor('cursor_unique_name', cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT documentation FROM sde.gdb_items \
        WHERE name::TEXT LIKE '%" + search_text + "%' \
        LIMIT 1")
    outputarray = cursor.fetchone()
    outputstring = outputarray[0]
    return HttpResponse(json.dumps(outputstring), mimetype="application/json")


@csrf_exempt
def downloadFiles(request):
    downloaditems = request.POST.getlist("downloadselect")

    if (len(downloaditems) < 1):
        return
    tempdirname = TEMPDIR + "temp_" + str(int(time.time()))

    os.mkdir(tempdirname)
    for curname in downloaditems:
        filename = curname.split(".")[-1]

        arcpy.FeatureClassToFeatureClass_conversion(SDECONNECTION + curname,tempdirname , filename,"#","","#")

    zipdata = StringIO()

    zipf = zipfile.ZipFile(zipdata, 'w', zipfile.ZIP_DEFLATED)

    zipdir(tempdirname, zipf)

    zipf.close()

    zipdata.seek(0)

    

    #data = open(os.path.join(settings.PROJECT_PATH,'data/table.csv'),'r').read()
    resp = HttpResponse(zipdata.read())
    #resp = HttpResponse(filestring, mimetype='text/csv')
    resp['Content-Disposition'] = 'attachment;filename=zipfile.zip'
    resp['Content-Type'] = 'application/x-zip'
    return resp





def queryresults(request):
    polygon = request.GET.get("query_wkt")
    response_data = drawTableFromGeom(polygon, request)

    return HttpResponse(json.dumps(response_data), mimetype="application/json")
    #"POLYGON (( -72.45655249 19.41041073, -71.73167100 19.41041073, -71.73167100 19.74637216, -72.45655249 19.74637216, -72.45655249 19.41041073))"








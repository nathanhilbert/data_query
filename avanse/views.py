# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from lockdown.decorators import lockdown


from avanse.models import Document
from avanse.forms import DocumentForm


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

def readFileBamboo(data, d):
    mydataset = Dataset(content=data)

    if (mydataset.id):
        d['messages'] = d['messages'], "<br/>Your new dataset is <strong>", mydataset.id, "</strong><br/>It can take up to hour for the data to be ready"
    else:
        d['messages'] = d['messages'], "<br/>Your dataset did not upload.  Please try again"

    return d

# def readFileBamboo(f, currentsurvey, d):


#     csvreader = csv.reader(f)
#     headers = csvreader.next()

#     thedataset = Dataset(currentsurvey)
#     myinfo = thedataset.get_info()
#     theinfo = myinfo['schema']  
#     dataresults = thedataset.get_data(select=headers)

#     numbersuccessful = 0
#     numberfail = 0
#     numberskipped = 0

#     for row in csvreader:
#         thedict = {}
#         for head, subrow in zip(headers, row):
#             rawvalue = ""
#             try:
#                 rawtype  = theinfo[head]["simpletype"]
#             except:
#                 d['messages'] = d['messages'], "<br/>COLUMN", head ," DID NOT MATCH. VERIFY THE COLUMNS IN THE CSV AGAINST THE LIST BELOW"
#                 return d
#             if rawtype == "float":
#                 if subrow != "":
#                     rawvalue = float(subrow)
#                 else:
#                     rawvalue = 0
#             elif rawtype == "integer":
#                 if subrow != "":
#                     rawvalue = int(subrow)
#                 else:
#                     rawvalue = 0
#             else:
#                 rawvalue = subrow
#             thedict[head] = rawvalue
#         indexexists = False
#         for aresult in dataresults:
#             if aresult['theindex'] == thedict['theindex']:
#                 indexexists = True
#                 break
#         if not indexexists:
#             theresult = thedataset.update_data([thedict])
#             print "the result", theresult, "and the index", thedict['theindex']
#             if theresult:
#                 numbersuccessful += 1
#             else:
#                 numberfail += 1
#         else:
#             print "the skipped and the index", thedict['theindex']
#             numberskipped += 1

#     d['messages'] = d['messages'], "<br/>Skipped:", numberskipped, "<br/>Successful:", numbersuccessful, "<br/>Failed:", numberfail
#     return d

def upload(request):
    d = {"TITLE":"Upload content"}

    d['messages'] = "File must be in CSV format and the first row must have the names of the columns"
    

    # Handle file upload
    if (request.method == 'POST' and len(request.FILES) > 0):
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            data = request.FILES['docfile'].read()
            #f = StringIO(data)
            d = readFileBamboo(data, d) 




    form = DocumentForm() # A empty, unbound form
    d['form'] = form
    # Render list page with the documents and the form
    return render_to_response(
        'upload.html',
        d,
        context_instance=RequestContext(request)
    )


def managesurveys(request):
    d = {"TITLE":"Upload content"}
    path = join(settings.MEDIA_ROOT, 'datarepo', 'surveys_avanse.pickle')

    submitbutton = request.POST.get("submit", "")

    if submitbutton != "":
        #wriate what we have

        numcolumns = int(request.POST.get("numfields", "0"))
        outputarray = []
        for thefield in range(numcolumns):
            valname = request.POST.get("surveyname_" + str(thefield), "")
            valvalue = request.POST.get("surveyvalue_" + str(thefield), "")
            if (valname != "" and valvalue != ""):
                outputarray.append([valname, valvalue])
        with open(path, 'wb') as f: 
            surveydata = pickle.dump(outputarray, f)


    try:
        with open(path, 'rb') as f: 
            surveydata = pickle.load(f)
    except:
        surveydata = []

    inputfields = ""
    counter = 0
    print surveydata
    for thesurvey in surveydata:
        inputfields += '<p><input type="text" name="surveyname_' + str(counter) + '" value="' + thesurvey[0] + '"/><input type="text" name="surveyvalue_' + str(counter) + '" value="' + thesurvey[1] + '"/>'
        counter +=1

    inputfields += '<p><input type="text" name="surveyname_' + str(counter) + '" value=""/><input type="text" name="surveyvalue_' + str(counter) + '" value=""/>'
    counter +=1
    d['inputfields'] = inputfields
    d['numcolumns'] = counter





    # Render list page with the documents and the form
    return render_to_response(
        'managesurveys.html',
        d,
        context_instance=RequestContext(request)
    )



# @lockdown()
# def upload(request):
#     d = {"TITLE":"Upload content"}

#     d['messages'] = "File must be in CSV format and must have on column called <<theindex>>"
    
#     currentsurvey = request.POST.get("survey_name", "")
#     d['currentsurvey'] = currentsurvey
#     surveys_options_info = [["Inventaire agro-entreprise (IR3)","dd299f7445d14885905664e6dc93319b"],["Inventaire Producteur (IR1)", "baee4539aefb45c58d4aa96dc197fc98"], ["uploadtest", "a4e97f4787c5449490d664edb7542e00"]]
#     d['survey_options'] = makeSurveyOptions(surveys_options_info, currentsurvey)
#     if (currentsurvey == ""):
#             return render_to_response(
#                     'upload.html',
#                     d,
#                     context_instance=RequestContext(request)
#                 )

#     # Handle file upload
#     if (request.method == 'POST' and len(request.FILES) > 0):
#         form = DocumentForm(request.POST, request.FILES)
#         if form.is_valid():
#             data = request.FILES['docfile'].read()
#             #f = StringIO(data)
#             d = readFileBamboo(f, currentsurvey, d) 




#     #get all of the items

#     myquestions = getQuestions(currentsurvey, groupitems = False)
#     column_list = ""
#     for thecolumn in myquestions['all']:
#         thetype = "unknown"
#         try:
#             thetype = myquestions['bytype'][thecolumn[0]]
#         except:
#             pass

#         column_list += "<li>" + thecolumn[0] + " - " + thetype + "</li>"

#     d['column_list'] = column_list


#     form = DocumentForm() # A empty, unbound form
#     d['form'] = form
#     # Render list page with the documents and the form
#     return render_to_response(
#         'upload.html',
#         d,
#         context_instance=RequestContext(request)
#     )




def makeSurveyOptions(myarray, selected=""):
    survey_options = u"<option value='' selected>SVP Sélectionner un option</option>"

    if (type(selected) is not list):
        selected = [selected]
    myarray.sort(key=lambda x: x[0])
    for soi in myarray:
        selectedval = ""
        if (soi[1] in selected):
            selectedval = "selected"
        tempoutput = "<option value='" + soi[1] + "' " + selectedval + ">" + soi[0] + "</option>"
        survey_options += tempoutput
    return survey_options

def processSummaryPie(summaryresults, question_options, options):
    outputarray = []
    answerkey = []
    if options['currentquestion'] in question_options['grouped'].keys():
        outputlist = {}
        for therowkey in question_options['grouped'][options['currentquestion']]:
            for srow in summaryresults[therowkey]['summary'].keys():
                if srow in outputlist.keys():
                    outputlist[srow] += summaryresults[therowkey]['summary'][srow]
                else:
                    outputlist[srow] = summaryresults[therowkey]['summary'][srow]
        for okey in outputlist.keys():
            outputarray.append([okey, outputlist[okey]])
    else:
        outputarray = []
        summaryresults_sub = summaryresults[options['currentquestion']]['summary']

        for srow in summaryresults_sub.keys():
            outputarray.append([srow, summaryresults_sub[srow]])
    return outputarray

def processSummaryScatter(dataresults, question_options, options):
    summary_data = []
    currentquestion1 = options['currentquestion1']
    currentquestion2 = options['currentquestion2']

    for therow in dataresults:
        if (currentquestion1 in question_options['grouped'].keys()):
            datapart1 = 0
            for srow in question_options['grouped'][currentquestion1]:
                if therow[srow] != "null":
                    datapart1 += therow[srow]
        else:
            datapart1 = therow[options['currentquestion1']]
            if therow[options['currentquestion1']] == "null":
                datapart1 = 0

        if (currentquestion2 in question_options['grouped'].keys()):
            datapart2 = 0
            for srow in question_options['grouped'][currentquestion2]:
                if therow[srow] != "null":
                    datapart2 += therow[srow]
        else:
            datapart2 = therow[options['currentquestion2']]
            if therow[options['currentquestion2']] == "null":
                datapart2 = 0
        summary_data.append([datapart1, datapart2])
    return summary_data

def getQuestions(currentsurvey, groupitems = True):

    formdata = Dataset(currentsurvey)
    myobject = formdata.get_info()
    question_options = {'all':[], 'string':[], 'numeric':[], 'datetime':[], "bytype":{}, 'grouped':{}}



    for itemkey in myobject['schema'].keys():

        geosplit = itemkey.split("_")
        isgeo = False
        if (geosplit[-1] in ['latitude', 'longitude']):
            print "found one ", itemkey
            isgeo = True


        itemkeysplit =  itemkey.split("__", 1)

        if len(itemkeysplit) == 1 or not groupitems or isgeo != True:
            if (myobject['schema'][itemkey]['simpletype'] in ["integer", "decimal", "float"]):
                question_options['bytype'][itemkey] = "numeric"
                question_options['numeric'].append([myobject['schema'][itemkey]['label'], itemkey])
            elif (myobject['schema'][itemkey]['simpletype'] in ["datetime"]):
                question_options['datetime'].append([myobject['schema'][itemkey]['label'], itemkey])
                question_options['bytype'][itemkey] = "datetime"
            elif (myobject['schema'][itemkey]['simpletype'] not in ["geopoint", "photo"]):
                question_options['bytype'][itemkey] = "string"
                question_options['string'].append([myobject['schema'][itemkey]['label'], itemkey])
            else:
                question_options['bytype'][itemkey] = "other"
            question_options['all'].append([myobject['schema'][itemkey]['label'], itemkey])
        else:
            groupedname = itemkeysplit[0].rsplit("_", 1)
            if (len(groupedname) == 1):
                continue
            groupedname = groupedname[0] + "__" + itemkeysplit[1]
            if (groupedname in question_options['grouped'].keys()):
                question_options['grouped'][groupedname].append(itemkey)
                continue
            if (myobject['schema'][itemkey]['simpletype'] in ["integer", "decimal", "float"]):
                question_options['bytype'][groupedname] = "numeric"
                question_options['numeric'].append([myobject['schema'][itemkey]['label'], groupedname])
            elif (myobject['schema'][itemkey]['simpletype'] in ["datetime"]):
                question_options['datetime'].append([myobject['schema'][itemkey]['label'], groupedname])
                question_options['bytype'][groupedname] = "datetime"
            elif (myobject['schema'][itemkey]['simpletype'] not in ["geopoint", "photo"]):
                question_options['bytype'][groupedname] = "string"
                question_options['string'].append([myobject['schema'][itemkey]['label'], groupedname])
            else:
                question_options['bytype'][groupedname] = "other"
            question_options['all'].append([myobject['schema'][itemkey]['label'], groupedname])
            question_options['grouped'][groupedname] = [itemkey]

    return question_options

def getSurveys():

    path = join(settings.MEDIA_ROOT, 'datarepo', 'surveys_avanse.pickle')
    try:
        with open(path, 'rb') as f: 
            surveydata = pickle.load(f)
    except:
        surveydata = []
    print surveydata
    return surveydata

def charts(request, chart_type):
    #define the necessary template options
    d = {"TITLE":"Charts in " + chart_type, "chart_type": chart_type}
    currentsurvey = request.GET.get("survey_name", "")
    surveys_options_info = getSurveys()
    d['survey_options'] = makeSurveyOptions(surveys_options_info, currentsurvey)
    if (currentsurvey == ""):
        d['question_options1'] = u"<option value=''>Sélectionner la source de données</option>"
        d['question_options2'] = u"<option value=''>Sélectionner la source de données</option>"
        return render_to_response('charts.html', d)

    currentquestion1 = request.GET.get("question1", "")
    currentquestion2 = request.GET.get("question2", "")
    d['currentquestion1'] = currentquestion1
    d['currentquestion2'] = currentquestion2


    if chart_type == "pie":
        question_options = getQuestions(currentsurvey)
        d['chart_class'] = "PieChart"
        d['question_options1'] = makeSurveyOptions(question_options['string'], currentquestion1)
        d['is_disabled'] = "disabled"
        d['question_options2'] = u"<option value=''>Pas nécessaire</option>"
        if (currentquestion1 == ""):
            return render_to_response('charts.html', d)

        thedataset = Dataset(currentsurvey)
        if (currentquestion1 in question_options['grouped'].keys()):
            currentquestionset = []
            for therow in question_options['grouped'][currentquestion1]:
                currentquestionset.append(therow)
        else:
            currentquestionset = [currentquestion1]
        summaryresults = thedataset.get_summary(select=currentquestionset)
        summary_data = processSummaryPie(summaryresults, question_options, {"currentquestion":currentquestion1})
    elif (chart_type == "scatter"):
        question_options = getQuestions(currentsurvey)
        d['chart_class'] = "ScatterChart"
        d['question_options1'] = makeSurveyOptions(question_options['numeric'], currentquestion1)
        d['question_options2'] = makeSurveyOptions(question_options['numeric'], currentquestion2)
        d['is_disabled'] = ""
        if (currentquestion1 == "" or currentquestion2 == ""):
            return render_to_response('charts.html', d) 
        thedataset = Dataset(currentsurvey)
        selectcolumnsarray = []
        if currentquestion1 in question_options['grouped'].keys():
            for srow in question_options['grouped'][currentquestion1]:
                selectcolumnsarray.append(srow)
        else:
            selectcolumnsarray.append(currentquestion1)
        if currentquestion2 in question_options['grouped'].keys():
            for srow in question_options['grouped'][currentquestion2]:
                selectcolumnsarray.append(srow)
        else:
            selectcolumnsarray.append(currentquestion2)

        dataresults = thedataset.get_data(select=selectcolumnsarray)
        summary_data = processSummaryScatter(dataresults, question_options, {"currentquestion1":currentquestion1, "currentquestion2":currentquestion2})

    elif (chart_type == "line"):
        question_options = getQuestions(currentsurvey)
        d['chart_class'] = "ColumnChart"
        d['question_options1'] = makeSurveyOptions(question_options['datetime'], currentquestion1)
        d['question_options2'] = makeSurveyOptions(question_options['string'] + question_options['numeric'], currentquestion2)
        freq_options = [['Year', 'A'],['Month', 'M'],[ 'Week', 'W'],['Day', 'D'], ['Hour', 'H']]
        currentfreq = request.GET.get("timefreq", "")
        d['freqquestion'] = '<p>By Time Frequency</p><select name="timefreq" class="update_page">\
                      ' + makeSurveyOptions(freq_options, currentfreq) + ' \
                    </select>'


        if (currentquestion1 == "" or currentfreq == "" or currentquestion2 == ""):
            return render_to_response('charts.html', d)

        thedataset = Dataset(currentsurvey)
        dataresults = thedataset.resample(date_column=currentquestion1, interval=currentfreq, how='count')
        print dataresults[0:10]
        summary_data = []
        for therow in dataresults:
            if (therow['level_1'] != currentquestion2):
                continue
            datapart2 = therow['0']
            if (datapart2 == "null"):
                datapart2 = 0
            summary_data.append([str(therow['level_0']), datapart2])
    elif (chart_type == "bar"):
        question_options = getQuestions(currentsurvey, False)
        d['chart_class'] = "ColumnChart"
        d['question_options1'] = makeSurveyOptions(question_options['string'], currentquestion1)
        d['question_options2'] = makeSurveyOptions(question_options['string'] + question_options['numeric'], currentquestion2)


        if (currentquestion1 == "" or currentquestion2 == ""):
            return render_to_response('charts.html', d)

        thedataset = Dataset(currentsurvey)

        dataresults = thedataset.get_summary(select=[currentquestion2], groups=[currentquestion1])
        print dataresults
        currentresults = dataresults[currentquestion1]

        reslabels = []

        summary_data = []
        for skey in currentresults.keys():
            temparray = [skey]
            tempresponse = currentresults[skey][currentquestion2]['summary']
            reslabels = tempresponse.keys()
            for reskey in tempresponse.keys():
                temparray.append(tempresponse[reskey])
            print tempresponse
            summary_data.append(temparray)
        summary_data.insert(0, [currentquestion1] + reslabels)


    io = StringIO()
    json.dump(summary_data, io)
    d['summary_data'] = io.getvalue()

    return render_to_response('charts.html', d)



def getValueOptions(currentsurvey, columnselect, defaultvalue = ""):

    thedataset = Dataset(currentsurvey)

    dataresults = thedataset.get_data(select=[columnselect])
    optionarray = []
    for therow in dataresults:
        try:
            thevalue = str(therow[columnselect])
        except:
            thevalue = therow[columnselect]
        if ([thevalue, thevalue] not in optionarray):
            if thevalue != "null":
                optionarray.append([thevalue, thevalue])

    return makeSurveyOptions(optionarray, defaultvalue)



def tables(request):
    #define the necessary template options
    d = {"TITLE": "Tables of Data"}

    currentsurvey = request.GET.get("survey_name", "")
    submitbutton = request.GET.get("submit_button", "")
    surveys_options_info = getSurveys()
    d['survey_options'] = makeSurveyOptions(surveys_options_info, currentsurvey)
    if (currentsurvey == ""):
        d['questionstring_options'] = u"<option value=''>Sélectionner la source de données</option>"
        d['questionnumber_options'] = u"<option value=''>Sélectionner la source de données</option>"
        d['column_value_options'] = u"<option value=''>Sélectionner la source de données</option>"
        return render_to_response('tables.html', d)
    question_options = getQuestions(currentsurvey)

    questionstring = request.GET.get("questionstring", "")
    questionstring_search = request.GET.getlist("questionstring_search")
    if (questionstring != "" and len(questionstring_search) < 1):
        d['questionstring_options'] = makeSurveyOptions(question_options['string'], questionstring)
        d['error_messages'] = "You must select a value with the query by text"
        d['questionstring_search_options'] = getValueOptions(currentsurvey, questionstring)
    elif (questionstring != ""):
        d['questionstring_options'] = makeSurveyOptions(question_options['string'], questionstring)
        d['questionstring_search_options'] = getValueOptions(currentsurvey, questionstring, questionstring_search)
    else:
        d['questionstring_options'] = makeSurveyOptions(question_options['string'], questionstring)




    


    d, summary_data = buildTable(request, question_options, currentsurvey, d, submitbutton)

    return render_to_response('tables.html', d)


def buildTable(request, question_options, currentsurvey, d = {}, submitbutton = "passthrough"):


    questionstring = request.GET.get("questionstring", "")
    questionstring_search = request.GET.getlist("questionstring_search", "")

    questionnumber = request.GET.get("questionnumber", "")
    questionnumber_operator = request.GET.get("questionnumber_operator", "")
    questionnumber_search = request.GET.get("questionnumber_search", "")

    questiondate = request.GET.get("questiondate", "")
    fromdate = request.GET.get("fromdate", "")
    todate = request.GET.get("todate", "")
    columnselect = request.GET.getlist("columnselect", "")


    d['questionnumber_options'] = makeSurveyOptions(question_options['numeric'], questionnumber)

    operatoroptions = [["Equal to", "equal"],["Less than", "$lt"], ["Greater than", "$gt"]]
    d['questionnumber_operator_options'] = makeSurveyOptions(operatoroptions, questionnumber_operator)

    d['questionnumber_search_option'] = questionnumber_search

    d['questiondate_options'] = makeSurveyOptions(question_options['datetime'], questiondate)

    d['fromdate_option'] = fromdate
    d['todate_option'] = todate

    d['columnselect_value_options'] = makeSurveyOptions(question_options['all'], columnselect)

    d['error_messages'] = ""

    if (columnselect == ['']):
        d['error_messages'] += "<li>Vous devez sélectionner une question à afficher</li>"



    if (submitbutton == ""):
        return d, None


    #build the query
    thequery = {}

    if questionstring != "":
        if (len(questionstring_search) > 0 and questionstring_search != ['']):
            hasnotexist = False
            myquestionstrings = []
            for editedquestion in questionstring_search:
                if editedquestion in ["True", "true"]:
                    myquestionstrings.append(True)
                elif editedquestion in ["False", "false"]:
                    myquestionstrings.append(False)
                elif editedquestion in ["null", "none", "Null"]:
                    hasnotexist = True
                else:
                    myquestionstrings.append(editedquestion)

            if questionstring in question_options['grouped'].keys():
                if ("$or" not in thequery.keys()):
                    thequery["$or"] = []
                #need to expand it
                for therow in question_options['grouped'][questionstring]:
                    if hasnotexist:
                        thequery["$or"].append({therow: {"$or": {"$in": myquestionstrings, "$exists": True}}})
                    else:
                        thequery["$or"].append({therow: {"$in": myquestionstrings}})
            else:  
                if hasnotexist:
                    thequery["$or"] = [{questionstring: {"$in": myquestionstrings}}, {questionstring:{"$exists": False}}]
                    #thequery[questionstring] = {"$in": myquestionstrings, "$exists": True}
                else:
                    thequery[questionstring] = {"$in": myquestionstrings}
        else:
            d['error_messages'] += u"<li>Vous avez sélectionné une question de recherche par texte, mais vous n'avez pas défini une valeur de recherche</li>"


    if questionnumber != "":
        if questionnumber_search != "":
            if questionnumber in question_options['grouped'].keys():
                if ("$or" not in thequery.keys()):
                    thequery["$or"] = []
                for therow in question_options['grouped'][questionnumber]:
                    if questionnumber_operator == "" or questionnumber_operator == "equal":
                        thequery['$or'].append({therow: float(questionnumber_search)}) 
                    else:
                        thequery['$or'].append({therow: {questionnumber_operator: float(questionnumber_search)}}) 
            else:
                if questionnumber_operator == "" or questionnumber_operator == "equal":
                    thequery[questionnumber] = float(questionnumber_search)
                else:
                    thequery[questionnumber] = {questionnumber_operator: float(questionnumber_search)}

        else:
            d['error_messages'] += u"<li>Vous avez sélectionné une question de recherche par nombre, mais vous n'avez pas défini une valeur de recherche</li>"



    print "here is the from date *********", fromdate
    if questiondate != "":
        if fromdate == "" and todate == "":
            d['error_messages'] += u"<li>Vous avez sélectionné une question de recherche par date, mais vous n'avez pas défini une valeur de recherche</li>"
        else:
            if questionnumber in question_options['grouped'].keys():
                if ("$or" not in thequery.keys()):
                    thequery["$or"] = []
                for therow in question_options['grouped'][questionnumber]:
                    outputobject = {}
                    if fromdate != "":
                        outputobject['$gt'] = fromdate
                    if todate != "":
                        outputobject['$lt'] = todate
                    thequery['$or'].append({therow: outputobject})
            else:
                outputobject = {}
                if fromdate != "":
                    outputobject['$gt'] = fromdate
                if todate != "":
                    outputobject['$lt'] = todate
                thequery[questiondate] = outputobject



    thedataset = Dataset(currentsurvey)

    #check if the column select has any grouped items
    expandedcolumnselect = []
    for therow in columnselect:
        if (therow in question_options['grouped'].keys()):
            for subrow in question_options['grouped'][therow]:
                expandedcolumnselect.append(subrow)
        else:
            expandedcolumnselect.append(therow)

    dataresults = thedataset.get_data(select=expandedcolumnselect,  query=thequery, limit=-1)



    addColumn_commands = ""
    for thecolumn in columnselect:
        if thecolumn == "":
            continue
        if (question_options['bytype'][thecolumn] == "numeric" and thecolumn not in question_options['grouped'].keys()):
            addColumn_commands += "data.addColumn('number', '" + thecolumn + "');"
        else:
            addColumn_commands += "data.addColumn('string', '" + thecolumn + "');"
    d['addColumn_commands'] = addColumn_commands;



    summary_data = []
    for therow in dataresults:
        temprow = []
        for thecol in columnselect:
            if thecol == "":
                continue

            if thecol in question_options['grouped'].keys():
                dataoutputarray = []
                for thesubrow in question_options['grouped'][thecol]:
                    if therow[thesubrow] != "null":
                        if type(therow[thesubrow]) is unicode:
                            dataoutputarray.append(therow[thesubrow])
                        else:
                            dataoutputarray.append(str(therow[thesubrow]))
                dataoutput = ",".join(dataoutputarray)
            else:
                dataoutput = therow[thecol]


            if (question_options['bytype'][thecol] == "numeric" and thecol not in question_options['grouped'].keys()):
                if dataoutput == "null":
                    temprow.append(0)
                else:
                    temprow.append(dataoutput)
            elif (question_options['bytype'][thecol] == "datetime"):
                if dataoutput == "null":
                    temprow.append("None")
                else:
                    temprow.append(str(dataoutput))
            elif (type(dataoutput) is unicode):
                if dataoutput == "null":
                    temprow.append("None")
                else:
                    temprow.append(dataoutput.replace('"', "'"))
            elif (type(dataoutput) is bool):
                if dataoutput == "null":
                    temprow.append("None")
                else:
                    temprow.append(str(dataoutput))
            else:
                if dataoutput == "null":
                    temprow.append("None")
                else:
                    temprow.append(dataoutput)
        summary_data.append(temprow)

    io = StringIO()

    json.dump(summary_data, io, encoding='utf-8', ensure_ascii=False)
    d['summary_data'] = io.getvalue()

    return d, summary_data

def getalldata(request, currentsurvey):
    thedataset = Dataset(currentsurvey)
    theinfo = thedataset.get_info()
    thedata = thedataset.get_data()
    summary_data = []
    thecolumns = []
    for columnkey in theinfo['schema']:
        thecolumns.append(columnkey)
    summary_data.append(thecolumns)

    for row in thedata:
        temprow = []
        for subkeys in row.keys():
            temprow.append(row[subkeys])
        summary_data.append(temprow)
    return summary_data

def getfiletables(request):

    currentsurvey = request.GET.get("survey_name", "")
    question_options = getQuestions(currentsurvey)

    fileHandle = StringIO()
    spamwriter = csv.writer(fileHandle)

    getallcolumns = False
    if (request.GET.get("getalldata", "") != ""):
        summary_data = getalldata(request, currentsurvey)
    else:
        d, summary_data = buildTable(request, question_options, currentsurvey)

        columnselect = request.GET.getlist("columnselect", "")
        columnselect.remove("")
        summary_data.insert(0, columnselect)

    for row in summary_data:
        temprow = []
        for p in row:
            try:
                temprow.append(str(p))
            except:
                temprow.append(p.encode("utf-8"))
        spamwriter.writerow(temprow)

    filestring = fileHandle.getvalue()
    fileHandle.close() 
    
    #data = open(os.path.join(settings.PROJECT_PATH,'data/table.csv'),'r').read()
    resp = HttpResponse(filestring, mimetype='application/x-download')
    #resp = HttpResponse(filestring, mimetype='text/csv')
    resp['Content-Disposition'] = 'attachment;filename=tableoutput.csv'
    return resp

def mashup(request):
    d = {}
    return render_to_response('mapmashup.html', d)

def gettamis(request):
    service = request.GET.get("service", "MEC")
    tamisservices = ""
    request.GET.get("tamisservices", "Crafts,Entertainment,Guides,Hotels,Restaurants,Tours")
    #this will get the general info for each question
    urlreq = "http://dominodev.daiglobal.net/Honduras/HondurasProParqueTAMIS.nsf/openmsme?OpenAgent=1&services=" + tamisservices
    if (service == "MEC"):
        urlreq = "http://dominodev.daiglobal.net/Honduras/HondurasProParqueTAMIS.nsf/openmsme?OpenAgent=1&services=" + tamisservices
    try:
        request = urllib2.Request(urlreq)
        result = urllib2.urlopen(request)
        response =  result.read()
    except:
        response = "{}"
    if response.endswith('\n'):
        response = response[:-1]
    if response[-3] == ",":
        response = response[:-3] + "]}"
    response = response.decode("utf-8", "replace")
    response_data = json.loads(response)

    return HttpResponse(json.dumps(response_data), mimetype="application/json")

def getTamisChartData(request):
    tamisservices = request.GET.get("tamisservices", "Crafts,Entertainment,Guides,Hotels,Restaurants,Tours")

    if tamisservices == "":
        return HttpResponse(json.dumps({"sector_chart":[], "grants_chart":[], "gender_chart": {"males": 0 , "females": 0 }}), mimetype="application/json") 

    #this will get the general info for each question
    urlreq = "http://dominodev.daiglobal.net/Honduras/HondurasProParqueTAMIS.nsf/opencharts?OpenAgent=1&services=" + tamisservices
    try:
        request = urllib2.Request(urlreq)
        result = urllib2.urlopen(request)
        response =  result.read()
    except:
        response = "{}"
    response = response.replace(",]", "]")
    return HttpResponse(response, mimetype="application/json")

def getRandomColor():
    for i in range(10):
        return str('%06X' % randint(0, 0xFFFFFF))

def getworldbank(request):
    service = request.GET.get("services", "MEC")

    #this will get the general info for each question
    urlreq = "http://search.worldbank.org/api/v2/projects?format=json&fl=id,status,project_name,totalamt,url,location,sector&countrycode_exact=HN&status_exact=Active&source=IBRD&rows=500&geocode=on"
    if (service == "MEC"):
        urlreq = "http://search.worldbank.org/api/v2/projects?format=json&fl=id,status,project_name,totalamt,url,location,sector&countrycode_exact=HN&status_exact=Active&source=IBRD&rows=500&geocode=on"
    try:
        request = urllib2.Request(urlreq)
        result = urllib2.urlopen(request)
        response =  result.read()
    except:
        response = "{}"

    response_data = json.loads(response)

    geojsonoutput = {"type":"FeatureCollection", "features":[]}
    lastproject = None
    currentcolor = None
    for reskeys in response_data['projects'].keys():
        if (reskeys != lastproject):
            currentcolor = getRandomColor()
            lastproject = reskeys
        resobj = response_data['projects'][reskeys]
        properties = {"url": resobj['url'], 'totalamt':int(resobj['totalamt'].replace(',','')), "project_name":resobj['project_name'], "projectcolor": "#" + currentcolor}
        for loc in resobj['locations']:
            thefeature = {"type": "Feature", \
                    "geometry": {"type":"Point", "coordinates": [float(loc['longitude']), float(loc['latitude'])]},\
                    "properties": properties
                    }
            geojsonoutput['features'].append(thefeature)


    return HttpResponse(json.dumps(geojsonoutput), mimetype="application/json")







def getGrantsData(request):
    import random

    #this will get the general info for each question
    urlreq = "http://dominodev.daiglobal.net/Honduras/HondurasProParqueTAMIS.nsf/opengrants?OpenAgent"
    try:
        request = urllib2.Request(urlreq)
        result = urllib2.urlopen(request)
        response =  result.read()
    except:
        response = "{}"
    response = response.decode("utf-8", "replace")
    if (response[-1] == "\n"):
        response = response[:-1]
    if (response[-2] == ","):
        response = response[:-2] + "]"

    response_data = json.loads(response)

    outputdata = {"type":"FeatureCollection", "features":[]}
    featureset = []
    for reskeys in response_data:
        fakex = random.uniform(-89.5, -84.2)
        fakey = random.uniform(13.8, 15.8)
        sojmething = 0
        thefeature = {}
        thefeature['geometry'] = {"type":"point", "coordinates":[fakex, fakey]}
        thefeature['properties'] = {"amount":reskeys['amount'], "title":reskeys['title']}
        thefeature = {"geometry": {"type":"point", "coordinates":[fakex, fakey]}, "type":"Feature", "properties": {"amount":reskeys['amount']/2500, "title":reskeys['title']}}
        featureset.append(thefeature)
    outputdata['features'] = featureset

    return HttpResponse(json.dumps(outputdata), mimetype="application/json")

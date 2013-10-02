from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse


import urllib2, base64
import simplejson as json
from pandas import date_range
from datetime import datetime
from StringIO import StringIO
import numpy as np
from pybamboo.dataset import Dataset
import time
from random import randint




def getChartVars(currentsurvey, FREQ = 'D', fromdate="None", todate="None"):





    #this will get all of the data
    returnobj = {"freq_survey_hour": [], "freq_device_output_json":[], "freq_candle_time_output":[]}


    dataset_id = currentsurvey

    formdata = Dataset(dataset_id)

    if (fromdate != "None" and todate != "None" and fromdate != None and todate != None):
        print "hitting here"
        myobject = formdata.get_data(select=["hidstarttime", "end", "hiddeviceid"], query={"end": {"$gte":fromdate, "$lte":todate}})
    else:
        myobject = formdata.get_data(select=["hidstarttime", "end", "hiddeviceid"])

    print "got the data"
    if (len(myobject) == 0):
        return returnobj
    #print myobject[0]['hidstarttime']['$date']
    #print myobject[0]['end']['$date']
    #print myobject[0]['hiddeviceid']

    data = []
    for obj in myobject:
        data.append([time.mktime(obj['hidstarttime'].timetuple()), 
                     time.mktime(obj['end'].timetuple()), 
                     obj['hiddeviceid'],
                     time.mktime(obj['end'].timetuple()) - time.mktime(obj['hidstarttime'].timetuple())])



    transdata = zip(*data)


    mindate = min(transdata[1])
    maxdate = max(transdata[1])

    mindate = datetime.fromtimestamp(min(transdata[1]))
    maxdate = datetime.fromtimestamp(max(transdata[1]))
    print "min date", mindate
    print "maxdate", maxdate

    print "strating that rng"

    rng = date_range(start=mindate, end=maxdate, freq=FREQ)
    print "actually loaded the date range"
    freqhour = []
    print "we are calculating ", len(rng), "by", len(transdata[1])

    #verify that we are not getting stuck here
    if len(rng) > 300:
        freq_survey_hour = []
    else:

        for z in range(len(rng)):
            freqhour.append(0)
            currentindex = len(freqhour)-1
            for d in transdata[1]:
                try:
                    thesample = datetime.fromtimestamp(d)
                    if (thesample > rng[z] and thesample < rng[z+1]):
                        freqhour[currentindex] += 1
                except:
                    pass
        print "finished doing the rng"

        timestring = []
        for z in rng:
            timestring.append(z.strftime('%m/%d/%Y %I:%M'))


        freq_survey_hour = zip(timestring, freqhour)

    io = StringIO()
    json.dump(freq_survey_hour, io)
    returnobj['freq_survey_hour_json'] =  io.getvalue()
    print returnobj['freq_survey_hour_json']

    print "doing the deices now"
    #get data for the freq by device
    freq_device = {}
    for did in transdata[2]:
        if (did in freq_device.keys()):
            freq_device[did] += 1
        else:
            freq_device[did] = 1
    freq_device_output = []
    for freqkey in freq_device.keys():
        freq_device_output.append([str(freqkey),freq_device[freqkey] ])
    io = StringIO()
    json.dump(freq_device_output, io)
    returnobj['freq_device_output_json'] = io.getvalue()


    print "startin avg time"
    #get data for the average time
    freq_avg_time_array = {}
    for row in data:
        #device id
        did = row[2]
        avgtime = row[3]
        if (did in freq_avg_time_array.keys()):
            freq_avg_time_array[did].append(avgtime)
        else:
            freq_avg_time_array[did] = [avgtime]
    freq_candle_time = []
    for didkey in freq_avg_time_array.keys():
        stddev = np.std(freq_avg_time_array[didkey])
        mean = np.mean(freq_avg_time_array[didkey])
        freq_candle_time.append([str(didkey), 
                                 min(freq_avg_time_array[didkey])/60,
                                (mean - stddev/2)/60,
                                (mean + stddev/2)/60,
                                max(freq_avg_time_array[didkey])/60
                                ])
    io = StringIO()
    json.dump(freq_candle_time, io)
    returnobj['freq_candle_time_output'] = io.getvalue()

    

    return returnobj




def home(request):

    currentsurvey = request.GET.get("survey_name", "cd1bfa34d6364b85b9ad0c03fad78730")
    frequency = request.GET.get('frequency', 'M')
    fromdate = request.GET.get('fromdate')
    if not fromdate:
        fromdate = "None"
    todate = request.GET.get('todate')
    if not todate:
        todate = "None"

    #http://bamboo.io/datasets/
    surveys_options_info = [["Please Select One", "cd1bfa34d6364b85b9ad0c03fad78730"],["inventaire_agro_entreprise","f0ec5bfb4f9e4bc99b4046073de3b7bb"],["FPSurveyKikwit29", "cd1bfa34d6364b85b9ad0c03fad78730"],["BaseLineBasCongo4", "6e2fd12684f94816a21ea5dd9df5336e"],["CDSurvey19", "63bb84836fde4dcb9905127c9751770b"],["FPPMDAIB5", "7cf121445a65466ca285e3049602373b"]]
    survey_options = ""
    d = getChartVars(currentsurvey, frequency, fromdate, todate)
    if not d:
        d = {}
    for soi in surveys_options_info:
        selectedval = ""
        if currentsurvey == soi[1]:
            selectedval = "selected"
        tempoutput = "<option value='" + soi[1] + "' " + selectedval + ">" + soi[0] + "</option>"
        survey_options += tempoutput
    d['survey_options'] = survey_options

    freq_options = [['A', 'Year'],['M', 'Month'],['W', 'Week'],['D', 'Day'], ['H', 'Hour']]
    freq_options_output = ""
    for freq in freq_options:
        selectedval = ""
        if frequency == freq[0]:
            selectedval = "selected"
        freq_options_output += "<option value='" + freq[0] + "' " + selectedval + ">" + freq[1] + "</option>"
    d['freq_options'] = freq_options_output
    d['fromdate_default'] = fromdate
    d['todate_default'] = todate

    return render_to_response('home.html', d)

def makeSurveyOptions(myarray, selected=""):
    survey_options = "<option value='' selected>Please select an option</option>"

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

def processSummary(summaryresults, question_options, chart_type, options):
    if chart_type == "pie":
        #all pie charts will be strings
        outputarray = []
        summaryresults_sub = summaryresults[options['currentquestion']]['summary']
        for srow in summaryresults_sub.keys():
            outputarray.append([srow, summaryresults_sub[srow]])
        return outputarray



def getQuestions(currentsurvey):

    formdata = Dataset(currentsurvey)
    myobject = formdata.get_info()
    question_options = {'all':[], 'string':[], 'numeric':[], 'datetime':[], "bytype":{}}

    for itemkey in myobject['schema'].keys():
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
    return question_options


def charts(request, chart_type):
    #define the necessary template options
    d = {"TITLE":"Charts in " + chart_type, "chart_type": chart_type}
    currentsurvey = request.GET.get("survey_name", "")
    surveys_options_info = [["Please Select A Survey", ""],["inventaire_agro_entreprise","f0ec5bfb4f9e4bc99b4046073de3b7bb"]]
    d['survey_options'] = makeSurveyOptions(surveys_options_info, currentsurvey)
    if (currentsurvey == ""):
        d['question_options1'] = "<option value=''>Please Select a Survey</option>"
        d['question_options2'] = "<option value=''>Please Select a Survey</option>"
        return render_to_response('charts.html', d)

    currentquestion1 = request.GET.get("question1", "")
    currentquestion2 = request.GET.get("question2", "")
    d['currentquestion1'] = currentquestion1
    d['currentquestion2'] = currentquestion2
    question_options = getQuestions(currentsurvey)

    if chart_type == "pie":
        d['chart_class'] = "PieChart"
        d['question_options1'] = makeSurveyOptions(question_options['string'], currentquestion1)
        d['is_disabled'] = "disabled"
        d['question_options2'] = "<option value=''>Not Required for Pie Chart</option>"
        if (currentquestion1 == ""):
            return render_to_response('charts.html', d)

        thedataset = Dataset(currentsurvey)

        summaryresults = thedataset.get_summary(select=[currentquestion1])
        summary_data = processSummary(summaryresults, question_options, chart_type, options={"currentquestion":currentquestion1})
    elif (chart_type == "scatter"):
        d['chart_class'] = "ScatterChart"
        d['question_options1'] = makeSurveyOptions(question_options['numeric'], currentquestion1)
        d['question_options2'] = makeSurveyOptions(question_options['numeric'], currentquestion2)
        d['is_disabled'] = ""
        if (currentquestion1 == "" or currentquestion2 == ""):
            return render_to_response('charts.html', d) 
        thedataset = Dataset(currentsurvey)
        dataresults = thedataset.get_data(select=[currentquestion1, currentquestion2])
        summary_data = []
        for therow in dataresults:
            datapart1 = therow[currentquestion1]
            if therow[currentquestion1] == "null":
                datapart1 = 0
            datapart2 = therow[currentquestion2]
            if therow[currentquestion2] == "null":
                datapart2 = 0
            summary_data.append([datapart1, datapart2])
    elif (chart_type == "line"):
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
            print "****************"
            print therow
            datapart2 = therow['0']
            if (datapart2 == "null"):
                datapart2 = 0
            summary_data.append([str(therow['level_0']), datapart2])
    elif (chart_type == "bar"):
        d['chart_class'] = "ColumnChart"
        d['question_options1'] = makeSurveyOptions(question_options['string'], currentquestion1)
        d['question_options2'] = makeSurveyOptions(question_options['string'] + question_options['numeric'], currentquestion2)


        if (currentquestion1 == "" or currentquestion2 == ""):
            return render_to_response('charts.html', d)

        thedataset = Dataset(currentsurvey)
        dataresults = thedataset.get_summary(select=[currentquestion2], groups=[currentquestion1])
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

def tables(request):
    #define the necessary template options
    d = {"TITLE": "Tables of Data"}

    currentsurvey = request.GET.get("survey_name", "")
    submitbutton = request.GET.get("submit_button", "")
    surveys_options_info = [["inventaire_agro_entreprise","dd299f7445d14885905664e6dc93319b"],["FPSurveyKikwit29", "cd1bfa34d6364b85b9ad0c03fad78730"]]
    d['survey_options'] = makeSurveyOptions(surveys_options_info, currentsurvey)
    if (currentsurvey == ""):
        d['questionstring_options'] = "<option value=''>Please Select a Survey</option>"
        d['questionnumber_options'] = "<option value=''>Please Select a Survey</option>"
        d['column_value_options'] = "<option value=''>Please Select a Survey</option>"
        return render_to_response('tables.html', d)


    questionstring = request.GET.get("questionstring", "")
    questionstring_search = request.GET.get("questionstring_search", "")

    questionnumber = request.GET.get("questionnumber", "")
    questionnumber_operator = request.GET.get("questionnumber_operator", "")
    questionnumber_search = request.GET.get("questionnumber_search", "")

    questiondate = request.GET.get("questiondate", "")
    fromdate = request.GET.get("fromdate", "")
    todate = request.GET.get("todate", "")
    columnselect = request.GET.getlist("columnselect", "")

    question_options = getQuestions(currentsurvey)

    d['questionstring_options'] = makeSurveyOptions(question_options['string'], questionstring)

    d['questionstring_search_option'] = questionstring_search

    d['questionnumber_options'] = makeSurveyOptions(question_options['numeric'], questionnumber)

    operatoroptions = [["Equal to", "equal"],["Less than", "$lt"], ["Greater than", "$gt"]]
    d['questionnumber_operator_options'] = makeSurveyOptions(operatoroptions, questionnumber_operator)

    d['questionnumber_search_option'] = questionnumber_search

    d['questiondate_options'] = makeSurveyOptions(question_options['datetime'], questiondate)

    d['fromdate_option'] = fromdate
    d['todate_option'] = todate

    d['columnselect_value_options'] = makeSurveyOptions(question_options['all'], columnselect)

    if (submitbutton == ""):
        return render_to_response('tables.html', d)



    d['error_messages'] = ""

    if (columnselect == ['']):
        d['error_messages'] += "<li>You must select a column to display</li>"


    #build the query
    thequery = {}

    if questionstring != "":
        if questionstring_search != "":
            thequery[questionstring] = questionstring_search
        else:
            d['error_messages'] += "<li>You have selected a column of type string to search, but you have not defined a search value</li>"

    if questionnumber != "":
        if questionnumber_search != "":
            if questionnumber_operator == "" or questionnumber_operator == "equal":
                thequery[questionnumber] = float(questionnumber_search)
            else:
                thequery[questionnumber] = {questionnumber_operator: float(questionnumber_search)}

        else:
            d['error_messages'] += "<li>You have selected a column of type number to search, but you have not defined a search value</li>"

    if questiondate != "":
        if fromdate == "" and todate == "":
            d['error_messages'] += "<li>You have selected a column of type date to search, but you have not defined a search value</li>"
        else:
            if fromdate != "":
                thequery[questiondate] = {"$gt": fromdate}
            if todate != "":
                print todate
                thequery[questiondate] = {"$lt": todate}



    thedataset = Dataset(currentsurvey)
    print "here is the query", thequery

    dataresults = thedataset.get_data(select=columnselect,  limit=-1)
    print "here is the elgnth of dataset", len(dataresults)


    addColumn_commands = ""
    for thecolumn in columnselect:
        if thecolumn == "":
            continue
        if (question_options['bytype'][thecolumn] == "numeric"):
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
            if (question_options['bytype'][thecol] == "numeric"):
                if therow[thecol] == "null":
                    temprow.append(0)
                else:
                    temprow.append(therow[thecol])
            elif (question_options['bytype'][thecol] == "datetime"):
                if therow[thecol] == "null":
                    temprow.append("None")
                else:
                    temprow.append(str(therow[thecol]))
            elif (type(therow[thecol]) is unicode):
                if therow[thecol] == "null":
                    temprow.append("None")
                else:
                    temprow.append(therow[thecol].replace('"', "'"))
            elif (type(therow[thecol]) is bool):
                if therow[thecol] == "null":
                    temprow.append("None")
                else:
                    temprow.append(str(therow[thecol]))
            else:
                if therow[thecol] == "null":
                    temprow.append("None")
                else:
                    temprow.append(therow[thecol])
        summary_data.append(temprow)

    io = StringIO()

    json.dump(summary_data, io, encoding='utf-8', ensure_ascii=False)
    d['summary_data'] = io.getvalue()

    return render_to_response('tables.html', d)




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



def getChartData(request):
    service = request.GET.get("services", "MEC")

    #this will get the general info for each question
    urlreq = "http://search.worldbank.org/api/v2/projects?format=json&fl=status,project_name,totalamt,sector&countrycode_exact=HN&status_exact=Active&source=IBRD&rows=500&geocode=off"
    if (service == "MEC"):
        urlreq = "http://search.worldbank.org/api/v2/projects?format=json&fl=status,project_name,totalamt,sector&countrycode_exact=HN&status_exact=Active&source=IBRD&rows=500&geocode=off"
    try:
        request = urllib2.Request(urlreq)
        result = urllib2.urlopen(request)
        response =  result.read()
    except:
        response = "{}"

    response_data = json.loads(response)

    outputdata = {"data":[], "aggregates":{}}
    totalamount = 0
    for reskeys in response_data['projects'].keys():
        resobj = response_data['projects'][reskeys]
        outputdata['data'].append([resobj['project_name'], int(resobj['totalamt'].replace(',',''))])
        totalamount += int(resobj['totalamt'].replace(',',''))
    outputdata['aggregates']['totalamount'] = totalamount



    return HttpResponse(json.dumps(outputdata), mimetype="application/json")



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

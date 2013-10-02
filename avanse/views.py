from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse
from django.template import RequestContext


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


        itemkeysplit =  itemkey.split("__", 1)

        if len(itemkeysplit) == 1 or not groupitems:
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



def charts(request, chart_type):
    #define the necessary template options
    d = {"TITLE":"Charts in " + chart_type, "chart_type": chart_type}
    currentsurvey = request.GET.get("survey_name", "")
    surveys_options_info = [["inventaire_agro_entreprise","dd299f7445d14885905664e6dc93319b"]]
    d['survey_options'] = makeSurveyOptions(surveys_options_info, currentsurvey)
    if (currentsurvey == ""):
        d['question_options1'] = "<option value=''>Please Select a Survey</option>"
        d['question_options2'] = "<option value=''>Please Select a Survey</option>"
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
        d['question_options2'] = "<option value=''>Not Required for Pie Chart</option>"
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
            if questionstring in question_options['grouped'].keys():
                if ("$or" not in thequery.keys()):
                    thequery["$or"] = []
                #need to expand it
                for therow in question_options['grouped'][questionstring]:
                    thequery["$or"].append({therow: questionstring_search})
            else:  
                thequery[questionstring] = questionstring_search
        else:
            d['error_messages'] += "<li>You have selected a column of type string to search, but you have not defined a search value</li>"


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
            d['error_messages'] += "<li>You have selected a column of type number to search, but you have not defined a search value</li>"

    if questiondate != "":
        if fromdate == "" and todate == "":
            d['error_messages'] += "<li>You have selected a column of type date to search, but you have not defined a search value</li>"
        else:
            if questionnumber in question_options['grouped'].keys():
                if ("$or" not in thequery.keys()):
                    thequery["$or"] = []
                for therow in question_options['grouped'][questionnumber]:
                    if fromdate != "":
                        thequery['$or'] = {therow: {"$gt": fromdate}}
                    if todate != "":
                        thequery['$or'] = {therow: {"$lt": todate}}
            else:
                if fromdate != "":
                    thequery[questiondate] = {"$gt": fromdate}
                if todate != "":
                    thequery[questiondate] = {"$lt": todate}



    thedataset = Dataset(currentsurvey)

    #check if the column select has any grouped items
    expandedcolumnselect = []
    for therow in columnselect:
        if (therow in question_options['grouped'].keys()):
            for subrow in question_options['grouped'][therow]:
                expandedcolumnselect.append(subrow)
        else:
            expandedcolumnselect.append(therow)

    print expandedcolumnselect

    dataresults = thedataset.get_data(select=expandedcolumnselect,  query=thequery, limit=-1)
    print "here is the elgnth of dataset", len(dataresults)


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
                        dataoutputarray.append(therow[thesubrow])
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

    return render_to_response('tables.html', d)




def createAJAXTable(request):

    currentsurvey = request.GET.get("survey_name", "")
    submitbutton = request.GET.get("submit_button", "")


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



    #build the query
    thequery = {}

    if questionstring != "":
        if questionstring_search != "":
            if questionstring in question_options['grouped'].keys():
                if ("$or" not in thequery.keys()):
                    thequery["$or"] = []
                #need to expand it
                for therow in question_options['grouped'][questionstring]:
                    thequery["$or"].append({therow: questionstring_search})
            else:  
                thequery[questionstring] = questionstring_search


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


    if questiondate != "":
        if fromdate != "" and todate != "":
            if questionnumber in question_options['grouped'].keys():
                if ("$or" not in thequery.keys()):
                    thequery["$or"] = []
                for therow in question_options['grouped'][questionnumber]:
                    if fromdate != "":
                        thequery['$or'] = {therow: {"$gt": fromdate}}
                    if todate != "":
                        thequery['$or'] = {therow: {"$lt": todate}}
            else:
                if fromdate != "":
                    thequery[questiondate] = {"$gt": fromdate}
                if todate != "":
                    thequery[questiondate] = {"$lt": todate}



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


    summary_data = []
    temprow = []
    for thecolumn in columnselect:
        if thecolumn == "":
            continue
        temprow.append(thecolumn)
    summary_data.append(temprow)


    for therow in dataresults:
        temprow = []
        for thecol in columnselect:
            if thecol == "":
                continue

            if thecol in question_options['grouped'].keys():
                dataoutputarray = []
                for thesubrow in question_options['grouped'][thecol]:
                    if therow[thesubrow] != "null":
                        dataoutputarray.append(therow[thesubrow])
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

    return summary_data

def getfiletables(request):

    fileHandle = StringIO()
    spamwriter = csv.writer(fileHandle)
    summary_data = createAJAXTable(request)
    for row in summary_data:
        spamwriter.writerow([s.encode("utf-8") for s in row])

    filestring = fileHandle.getvalue()
    print filestring
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

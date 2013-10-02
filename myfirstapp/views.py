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


def getQuestions(currentsurvey):

	formdata = Dataset(currentsurvey)
	myobject = formdata.get_info()

	question_options = []
	for itemkey in myobject['schema'].keys():
		question_options.append([itemkey, myobject['schema'][itemkey]['label']])
	return question_options



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
	surveys_options_info = [["Please Select One", "cd1bfa34d6364b85b9ad0c03fad78730"],["FPSurveyKikwit29", "cd1bfa34d6364b85b9ad0c03fad78730"],["BaseLineBasCongo4", "6e2fd12684f94816a21ea5dd9df5336e"],["CDSurvey19", "63bb84836fde4dcb9905127c9751770b"],["FPPMDAIB5", "7cf121445a65466ca285e3049602373b"]]
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


    #request.POST.get("title", "")

def questions(request):
	currentsurvey = request.GET.get("survey_name", "cd1bfa34d6364b85b9ad0c03fad78730")
	surveys_options_info = [["Please Select One", "cd1bfa34d6364b85b9ad0c03fad78730"],["inventaire_agro_entreprise","f0ec5bfb4f9e4bc99b4046073de3b7bb"], ["FPSurveyKikwit29", "cd1bfa34d6364b85b9ad0c03fad78730"],["BaseLineBasCongo4", "6e2fd12684f94816a21ea5dd9df5336e"],["CDSurvey19", "63bb84836fde4dcb9905127c9751770b"],["FPPMDAIB5", "7cf121445a65466ca285e3049602373b"]]
	survey_options = ""
	d = {}
	for soi in surveys_options_info:
		selectedval = ""
		if currentsurvey == soi[1]:
			selectedval = "selected"
		tempoutput = "<option value='" + soi[1] + "' " + selectedval + ">" + soi[0] + "</option>"
		survey_options += tempoutput
	d['survey_options'] = survey_options


	currentquestion = request.GET.get("question")
	question_options = getQuestions(currentsurvey)
	trans_question_data = zip(*question_options)
	question_options_output = ""
	for item in question_options:
		selectedval = ""
		if currentquestion == item[0]:
			selectedval = "selected"
		question_options_output += "<option value='" + item[0] + "' " + selectedval + ">" + item[1] + "</option>"
	d['question_options'] = question_options_output
	if currentquestion not in trans_question_data[0]:
		d['summary_data'] = []
	else:

		thedata = Dataset(currentsurvey)
		summary_data = thedata.get_summary(select=[currentquestion])
		print summary_data
		summary_data_array = []
		for summarydat in summary_data[currentquestion]['summary'].keys():
			summary_data_array.append([summarydat, summary_data[currentquestion]['summary'][summarydat]])
		io = StringIO()
		json.dump(summary_data_array, io)
		d['summary_data'] = io.getvalue()

		detailedinformation_output = ""
		for datitem in summary_data_array:
			print datitem
			detailedinformation_output += "<tr><td>" + str(datitem[0].encode('utf-8', errors='replace')) + "</td><td>" + str(datitem[1]) + "</td></tr>"
		d['detailed_data'] = detailedinformation_output

	return render_to_response('questions.html', d)



def mashup(request):
	d = {}
	return render_to_response('mapmashup.html', d)

def gettamis(request):
	service = request.GET.get("service", "MEC")
	tamisservices = request.GET.get("tamisservices", "Crafts,Entertainment,Guides,Hotels,Restaurants,Tours")

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

import pathlib
import argparse
import csv
import json
import time

#definining values that will be the same for all outputs
latitude = 40.0076
longitude = -105.2619
timezone = "America/Denver"

parser = argparse.ArgumentParser(description='Generate test inputs for weather automation testing')
parser.add_argument('Test_ID', nargs=1, help='Input the Test ID of the test you wish to run. (Test ID is listed in testing documents)')
testname = parser.parse_args().Test_ID[0]

testtime = int(time.time()+600)
#assume test starts within 10 minutes of the current time

hourly = list()
alert = list()
currently = {"time":testtime,"summary": "Drizzle","icon": "rain","nearestStormDistance": 0,"precipIntensity": 0,"precipIntensityError": 0,"precipProbability": 0,"precipType": "rain","temperature": 0,"apparentTemperature": 0,"dewPoint":0,"humidity": 0,"pressure":0,"windSpeed": 0,"windGust": 0,"windBearing": 0,"cloudCover": 0,"uvIndex": 0,"visibility": 0,"ozone":0}
minutely = {"time":testtime,"summary":"computer generated","icon":"polarcube","nearestStormDistance":0,"precipIntensity":0,"precipIntensityError":0,"precipProbability":0,"precipType": "cats and dogs","temperature":0,"apparentTemperature":0,"dewPoint":0,"humidity":0,"pressure":0,"windSpeed":42,"windGust":32,"windBearing":0,"cloudCover":0,"uvIndex":1,"visibility":10,"ozone":0}
daily = {"time":testtime,"summary": "This is a weather report generator","icon": ".png","sunriseTime": 1552914533,"sunsetTime": 1552957910,"moonPhase": 0.42,
        "precipIntensity": 0,"precipIntensityMax": 0,"precipIntensityMaxTime": testtime+7200,"precipProbability": 0,"precipType": "rain","temperatureHigh":0,"temperatureHighTime": testtime+36000,"temperatureLow":0,"temperatureLowTime":testtime+3600,"apparentTemperatureHigh":0,"apparentTemperatureHighTime":testtime+12000,"apparentTemperatureLow":0,"apparentTemperatureLowTime":testtime+24000,
        "dewPoint": 0,"humidity": 0,"pressure": 1024,"windSpeed": 0,"windGust":0,"windGustTime": testtime+10800,"windBearing":0,"cloudCover": 0,"uvIndex": 0,"uvIndexTime": testtime,"visibility":0,"ozone":0,"temperatureMin":0,"temperatureMinTime": testtime,"temperatureMax":0,"temperatureMaxTime": testtime,"apparentTemperatureMin":0,"apparentTemperatureMinTime":testtime,"apparentTemperatureMax": 0,"apparentTemperatureMaxTime":testtime+10800}

inpath = pathlib.PurePosixPath("testing")
inpath = inpath / str(testname+'.csv')

with open(str(inpath), newline='') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
	for i in csvreader:
		try:
			#integer offset for schedule data
			data = {"time":(testtime+(float(i[0])*3600))}
			#unused data
			data.update({"summary":"computer generated","icon":"polarcube","precipIntensity":0,"precipProbability":0,"temperature":0,"apparentTemperature":0,"dewPoint":0,"humidity":0,"pressure":0,"windSpeed":0})
			#wind gust
			data.update({"windGust":float(i[1])})
			#unused data
			data.update({"windBearing":0,"cloudCover":0,"uvIndex":0,"visibility":0,"ozone":0})
			hourly.append(data)
		except(TypeError, ValueError):
			#flag: 'a' to specify alert
			data = {"description":i[2]}
			data.update({"expires":(testtime+(float(i[4])*3600))})
			data.update({"regions":"COSGC MCGS MOCC"})
			data.update({"severity":i[1]})
			data.update({"time":(testtime+(float(i[3])*3600))})
			data.update({"title":i[2]})
			data.update({"uri":"NONE"})
			alert.append(data)

test_dict = {"latitude":latitude, "longitude":longitude,"timezone":timezone}
#add currently block with starttime
test_dict.update({"currently":currently})
#add reduced minutely block with fixed data
test_dict.update({"minutely":minutely})
#add hourly data block (>= 48 entries)
test_dict.update({"hourly":{"data":tuple(hourly)}})
#add reduced daily block with fixed data
test_dict.update({"daily":{"summary": "These data mean nothing","icon": "polarcube","data":daily}})
#add alert block
if len(alert) > 0:
	test_dict.update({"alerts":tuple(alert)})


#print(test_dict)
if len(hourly) < 48:
	print("Not enough forecast data points. File not updated")
else:
	with open("test_input.json", 'w') as f:
		json.dump(test_dict, f, indent="  ")
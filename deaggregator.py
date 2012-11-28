import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify
import USGSapi
import ShahiBaker
import time
import numpy as np

# config
DEBUG = True

# initialize the app
app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def mainPage():
	return render_template('index.html')

@app.route('/approx_deagg',methods=['POST'])
def approxDeagg():
	# List of parameters to send to USGS
	deaggParams = {}
	deaggParams['geo'] = 0
	deaggParams['gmpe'] = 0
	deaggParams['latitude'] = request.form['latitude']
	deaggParams['longitude'] = request.form['longitude']
	deaggParams['name'] = request.form['analysis_name']
	deaggParams['percent'] = request.form['percent']
	deaggParams['sa'] = request.form['period']
	deaggParams['vs30'] = request.form['vs30']
	deaggParams['years'] = request.form['years']
	
	USGSresult,errorCode = USGSapi.getDeaggregations(deaggParams)
	if errorCode == -1:
		returnDict = {'error':-1}
		return jsonify(returnDict)
		
	#saLevel, Mdeagg, Rdeagg = USGSapi.parseDeagg(USGSresult)
	
	#Mbar = ShahiBaker.getMeanDeagg(Mdeagg)
	#Rbar = ShahiBaker.getMeanDeagg(Rdeagg)
	
	saLevel, Mbar, Rbar = USGSapi.parseMbarRbar(USGSresult)
	
	ppulse = ShahiBaker.ppulse(saLevel, Mbar, Rbar, request.form['period'], request.form['vs30'])
	Tps,TpDist = ShahiBaker.TpDist(saLevel, Mbar, Rbar, request.form['period'], request.form['vs30'])
	
	# Prepare the text file of results
	
	ourResult = 'Site location latitude = %s, longitude = %s with Vs30 = %s\n'%(request.form['latitude'],request.form['longitude'],request.form['vs30'])
	
	ourResult += 'Hazard deaggregations were computed for %s percent in %s year hazard.\n'%(request.form['percent'],request.form['years'])
	ourResult += 'P(pulse | hazard exceedance) = %.3f \n'%ppulse
	ourResult += 'Contribution of different Tp levels to hazard exceedance \n'
	ourResult += 'Tp \t \t Percentage contribution \n'
	
	for i in range(len(Tps)):
		ourResult += '%.3f \t \t %.3f \n'%(Tps[i],TpDist[i]*100)
	
	ourResult += '\n \n ***** Text below reports M-R-epsilon deaggregations from USGS ***** \n \n'
	ourResult += USGSresult
	
	
	fn = '%s_%d.txt'%(request.form['analysis_name'],int(time.time()))
	f = open('./static/'+fn,'w')
	f.write(ourResult)
	f.close()
	
	filenameURL = url_for('static',filename=fn)
	
	returnDict={'error':0 , 'saLevel':saLevel , 'ppulse':ppulse , 'Tps':Tps , 'TpDist':TpDist , 'percent':request.form['percent'] , 'years':request.form['years'], 'dldLink':filenameURL}
	return jsonify(returnDict)

@app.route('/test_function',methods=['POST'])
def testDeagg():
	saLevel = 0.1
	ppulse = 0.6
	Tps = np.arange(0.5,20.5,0.5)
	TpProbs = np.random.rand(len(Tps))
	TpProbs /= np.sum(TpProbs)
	TpDist = dict(zip(list(Tps) , list(TpProbs)))
	percent = '2'
	years = '50'
	
	returnDict={'saLevel':saLevel , 'ppulse':ppulse, 'Tps':list(Tps) , 'TpDist':list(TpProbs) , 'percent':request.form['percent'] , 'years':request.form['years']}
	time.sleep(3)
	return jsonify(returnDict)
	
if __name__ == '__main__':
	app.run()
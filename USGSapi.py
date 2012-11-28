import requests
import re

def getDeaggregations(parameters):
	try:
		usgsResponse = requests.get('https://geohazards.usgs.gov/deaggint/2008/application.php', params = parameters)
		searchUrl = re.search('http://geohazards.usgs.gov/deaggint/2008/out/.+txt', usgsResponse.text)
		resultUrl = searchUrl.group(0)
		USGSdeaggregation = requests.get(resultUrl)
		return USGSdeaggregation.text,0
	except AttributeError:
		return -1,-1

def parseMbarRbar(USGSresult):
	# split into lines
	lines = USGSresult.split('\n')
	# Find the Sa level
	saLine = lines[5]
	saLine = saLine[(saLine.find('=')+1):]
	saLine = saLine.split(' ')
	saLevel =re.findall('\d+.\d+',saLine[0])
	saLevel = float(saLevel[0])
	
	# Count the number of lines in the table
	tableLines = lines[9:] # remove the headers
	counter = 0
	for line in tableLines:
		columns = line.split(' ')
		counter += 1
		if len(columns) == 1:
			break
	
	
	belowTable = tableLines[counter:]
	belowTable = belowTable[2:]
	
	meanMRline = belowTable[0]
	idx1 = meanMRline.find('=')
	idx2 = meanMRline.find('km')
	Rbar = float(meanMRline[(idx1+1):idx2].strip())
	idx1 = meanMRline.find('=',idx2)
	idx2 = meanMRline.find(';',idx1)
	Mbar = float(meanMRline[(idx1+1):idx2].strip())
	
	return saLevel, Mbar, Rbar
	
def parseDeagg(USGSresult):
	# split into lines
	lines = USGSresult.split('\n')
	# Find the Sa level
	saLine = lines[5]
	saLine = saLine[(saLine.find('=')+1):]
	saLine = saLine.split(' ')
	saLevel = float(saLine[0])
	
	# Parse the deaggregation table
	tableLines = lines[9:] # remove the headers
	Ms = []
	Rs = []
	Ds = []
	for line in tableLines:
		columns = line.split(' ')
		if len(columns) == 1:
			break
		m,r,d = parseColumns(columns)
		Ms.append(m)
		Rs.append(r)
		Ds.append(d)
		
	Mdeagg,Rdeagg = consolidateDeagg(Ms,Rs,Ds)
	
	return saLevel, Mdeagg, Rdeagg
	
def parseColumns(columns):
	counter = 0
	for col in columns:
		if len(col) == 0:
			continue
		counter += 1
		if counter == 1:
			r = float(col)
		
		if counter == 2:
			m = float(col)
		
		if counter == 3:
			d = float(col)
			break
	return m,r,d
	
def consolidateDeagg(Ms,Rs,Ds):
	Mdeagg = {}
	for i in range(len(Ms)):
		if Ms[i] in Mdeagg:
			Mdeagg[Ms[i]] += Ds[i]
		else:
			Mdeagg[Ms[i]] = Ds[i]
	
	Rdeagg = {}
	for i in range(len(Rs)):
		if Rs[i] in Rdeagg:
			Rdeagg[Rs[i]] += Ds[i]
		else:
			Rdeagg[Rs[i]] = Ds[i]
	
	# Normalize the deaggregation
	sumM = 0.0
	for m in Mdeagg:
		sumM += Mdeagg[m]
		
	for m in Mdeagg:
		Mdeagg[m] /= sumM
		
	sumR = 0
	for r in Rdeagg:
		sumR += Rdeagg[r]
		
	for r in Rdeagg:
		Rdeagg[r] /= sumR
	
	return Mdeagg, Rdeagg
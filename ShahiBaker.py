import CBR
import CBSB
import numpy as np
from scipy.stats import norm

periods = [0.01,0.1,0.2,0.3,0.5,1.0,2.0,3.0,4.0,5.0]

def getMeanDeagg(deagg):
	meanDeagg = 0.0
	sumProb = 0.0
	for d in deagg:
		meanDeagg += d*deagg[d]
		sumProb += deagg[d]
	
	return meanDeagg/sumProb
	
def TpDist(saLevel, Mbar, Rbar, pidx, vs30):
	'''
		f(tp|Sa>x) = p1 * p2 / p3
		where:
		p1 = P(Sa > x | tp, Mbar, Rbar)
		p2 = f(tp | Mbar)
		p3 = P(Sa > x | Mbar, Rbar)
	'''
	T = periods[int(pidx)-1]
	Tps = np.arange(0.5,20.5,0.5)
	
	# initialize variables needed for CBSB model
	Ztop = 0
	dip = 90
	rake = 180
	Zvs = 2.5
	Ipulse = 1
	Ppulse = 1
	
	# Tp distribution given M , from Shahi and Baker (2013)
	mulntp = -6.207 + 1.075*Mbar
	siglntp = 0.61
	
	# compute p1
	sas = np.zeros(len(Tps))
	sigs = np.zeros(len(Tps))
	for i in range(len(sas)):
		sas[i],sigs[i] = CBSB.predict(Mbar,T,Rbar,Rbar,Ztop,dip,rake,vs30,Zvs,Ipulse,Tps[i],Ppulse)
	
	p1 = 1 - norm.cdf((np.log(saLevel) - np.log(sas))/sigs)
	# compute p2
	p2 = norm.cdf((np.log(Tps + 0.25) - mulntp)/siglntp) - norm.cdf((np.log(Tps - 0.25) - mulntp)/siglntp)
	# compute p3
	epsUp = np.arange(-3,3,0.5)
	epsDn = np.arange(-2.5,3.5,0.5)
	eps = (epsUp + epsDn)/2
	Peps = norm.cdf(epsDn) - norm.cdf(epsUp)
	Peps = Peps/np.sum(Peps)
	p3 = 0
	for i in range(len(eps)):
		m,s = CBSB.predict(Mbar,T,Rbar,Rbar,Ztop,dip,rake,vs30,Zvs,Ipulse,np.exp(mulntp + eps[i]*siglntp),Ppulse)
		p3 += Peps[i]*(1-norm.cdf((np.log(saLevel) - np.log(m))/s))
	
	probs = (p1 * p2)/p3
	#TpDist = dict(zip(list(Tps), list(probs)))
	return list(Tps),list(probs)
	
def ppulse(saLevel, Mbar, Rbar, pidx, vs30):
	'''
		P(pulse|Sa>x) = p1 * p2 / p3
		where:
		p1 = P(Sa > x | directivity, Mbar, Rbar)
		p2 = P(directivity | Mbar, Rbar)
		p3 = P(Sa > x | Mbar, Rbar)
	'''
	
	T = periods[int(pidx)-1]
	
	mulntp = -6.207 + 1.075*Mbar
	siglntp = 0.61
	epsUp = np.arange(-3,3,0.5)
	epsDn = np.arange(-2.5,3.5,0.5)
	eps = (epsUp + epsDn)/2
	Peps = norm.cdf(epsDn) - norm.cdf(epsUp)
	Peps = Peps/np.sum(Peps)
	sas = np.zeros(len(eps))
	sigs = np.zeros(len(eps))

	Ztop = 0
	dip = 90
	rake = 180
	Zvs = 2.5
	
	p1 = 0
	Ipulse = 1
	Ppulse = 1
	for i in range(len(eps)):
		m,s = CBSB.predict(Mbar,T,Rbar,Rbar,Ztop,dip,rake,vs30,Zvs,Ipulse,np.exp(mulntp + eps[i]*siglntp),Ppulse)
		p1 += Peps[i]*(1-norm.cdf((np.log(saLevel) - np.log(m))/s))
	
	p2 = PpulseGivenMR(Mbar,Rbar)
	
	p3pulse = p1
	Ipulse = 0
	Ppulse = 0
	m,s = CBSB.predict(Mbar,T,Rbar,Rbar,Ztop,dip,rake,vs30,Zvs,Ipulse,np.exp(mulntp + eps[i]*siglntp),Ppulse)
	p3nopulse = (1-norm.cdf((np.log(saLevel) - np.log(m))/s))
	p3 = p2*p3pulse + (1-p2)*p3nopulse
	
	return p1 * p2 / p3
	
	
def PpulseGivenMR(Mbar,Rbar):
	L = 10**(-3.55 + 0.74*Mbar)
	epi = L*np.arange(0,1.1,0.1)
	
	# curved part
	theta = np.arange(0,95,5)
	pcurve = 0
	for t in theta:
		ps = 1/(1 + np.exp(0.7897 + 0.1378*Rbar - 0.3533*epi + 0.020*t))
		pcurve += np.sum(ps)/len(ps)
	
	pcurve /= len(theta)
	
	#straight part
	sites = L*np.arange(0,1.01,0.01)
	pstraight = 0
	for site in sites:
		s = np.abs(site - epi)
		thetas = np.arctan(Rbar/s)*180/np.pi
		ps = 1/(1 + np.exp(0.7897 + 0.1378*Rbar - 0.3533*s + 0.020*thetas))
		pstraight += np.sum(ps)/len(ps)
	
	pstraight /= len(sites)
	
	weightCurve = np.pi*Rbar/(L + np.pi*Rbar)
	weightStraight = L/(L + np.pi*Rbar)
	
	return weightCurve*pcurve + weightStraight*pstraight
	
	return 0
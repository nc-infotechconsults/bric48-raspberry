# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:35:02 2023

@author: gabma

versione 2.1 con aggiunta di calcolo dei livelli di P, media logaritmica, arrotondamento decimale
"""

#imput: microfono e computer
#output: sensibilità e gain
def mic_features(comp, mic):
    if comp=='Landi':
        #boya: auricolari+microfono  boost 0, volume 40 
        #rodego microfono 
        #rode2 microfono 
        gain=-3
        if mic=='BOYA':
            sensitivity=-31
        elif mic=='RODEGO':
            sensitivity=-34
        elif mic=='RODE2':
            sensitivity=-33          
        else:
            sensitivity=-100
    elif comp=='Gabri':
        gain=13.5
        if mic=='BOYA':
            gain = 8
            sensitivity=-32
        elif mic=='RODEGO':
            sensitivity=-39.3
        elif mic=='RODE2':
            sensitivity=-38          
        else:
            sensitivity=-100
    elif comp=='Fede':
        gain=23
        if mic=='RODEGO':
            sensitivity=-41.6
        elif mic=='RODE2':
            sensitivity=-38          
        else:
            sensitivity=-100
    else:
        gain=-100
    return gain, sensitivity



#input: pressione sonora
#output: livelli di pressione in bande d'ottava o di terze tramite filtraggio 
import numpy as np
import pandas as pd
from scipy.signal import butter, lfilter


def levelsoct(sp,P):
    #ottave
    PondA=[-39.4, -26.2, -16.1, -8.6, -3.2, 0, 1.2, 1.0, -1.1, -6.6]
    PondC=[-3.0, -0.8, -0.2, 0, 0, 0, -0.2, -0.8, -3.0, -8.5]
    centerFrequencies = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000] #ottave
    low = [22.4, 44.7, 89.1, 178, 355, 708, 1410, 2820, 5620, 11200]
    high = [44.7, 89.1, 178, 355, 708, 1410, 2820, 5620, 11200, 22400]
    
    Lp_band = np.zeros(len(centerFrequencies))
    
    for i in range(len(centerFrequencies)):
        # Filter the signal in the third-octave bands
        f_low=low[i]
        f_high=high[i]
        b, a = butter(2, [f_low, f_high], btype='band', fs=48000)
        y_band = lfilter(b, a, sp)
    
        # Calculate the sound pressure level in dB
        rms = np.sqrt(np.mean(y_band**2))
        Lp_band[i] = decimali(20 * np.log10(rms/(20e-6)))
    if P=='A':
        Lp_bande=Lp_band+PondA
    elif P=='C':
        Lp_bande=Lp_band+PondC
    elif P=='Z':
        Lp_bande=Lp_band
    return Lp_bande

def levels3oct(sp,P):
    #terzi d'ottava
    Pond3A=[-50.5, -44.7, -39.4, -34.6, -30.2, -26.2, -22.5, -19.1, -16.1, -13.4, -10.9, -8.6, -6.6, -4.8, -3.2, -1.9, -0.8, 0, 0.6, 1.0, 1.2, 1.3, 1.2, 1, 0.5, -0.1, -1.1, -2.5, -4.3, -6.6, -9.3]
    Pond3C=[-6.2, -4.4, -3.0, -2.0, -1.3, -0.8, -0.5, -0.3, -0.2, -0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, -0.1, -0.2, -0.3, -0.5, -0.8, -1.3, -2.0, -3.0, -4.4, -6.2, -8.5, -11.2]
    low = [17.5384695, 22.09708691,	27.84058494, 35.07693901, 44.19417382, 55.68116988,	70.15387802,	88.38834765,	111.3623398,	140.307756,	176.7766953,	222.7246795,	280.6155121,	353.5533906,	445.4493591,	561.2310242,	707.1067812,	890.8987181,	1122.462048,	1414.213562,	1781.797436,	2244.924097,	2828.427125,	3563.594873,	4489.848193,	5656.854249,	7127.189745,	8979.696386,	11313.7085,	14254.37949,	17959.39277]
    high = [22.09708691,	27.84058494,	35.07693901,	44.19417382,	55.68116988,	70.15387802,	88.38834765,	111.3623398,	140.307756,	176.7766953,	222.7246795,	280.6155121,	353.5533906,	445.4493591,	561.2310242,	707.1067812,	890.8987181,	1122.462048,	1414.213562,	1781.797436,	2244.924097,	2828.427125,	3563.594873,	4489.848193,	5656.854249,	7127.189745,	8979.696386,	11313.7085,	14254.37949,	17959.39277,	22627.417]
    centerFrequencies = [20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000]
    Lp_band = np.zeros(len(centerFrequencies))
    
    for i in range(len(centerFrequencies)):
        # Filter the signal in the third-octave bands
        f_low=low[i]
        f_high=high[i]
        b, a = butter(2, [f_low, f_high], btype='band', fs=48000)
        y_band = lfilter(b, a, sp)
    
        # Calculate the sound pressure level in dB
        rms = np.sqrt(np.mean(y_band**2))
        Lp_band[i] = decimali(20 * np.log10(rms/(20e-6)))
    if P=='A':
        Lp_bande=Lp_band+Pond3A
    elif P=='C':
        Lp_bande=Lp_band+Pond3C
    elif P=='Z':
        Lp_bande=Lp_band
    return Lp_bande
 

    
#input: livelli di pressione in bande secondo per secondo
#output: livello medio logaritmico in bande
def log_mean(L):
    t_tot=len(L)
    anti=[]
    LL=[]
    
    for i in range(0, t_tot):
        LL=L[i]
        for j in range(len(LL)):
            l1=10**(LL[j]/10)
            anti.append(l1)
    
    antilog = [anti[i::len(LL)] for i in range(len(LL))]
    somma = [sum(j) for j in antilog]
    esp = [k / t_tot for k in somma]
    Lp_mean = [10*np.log10(l) for l in esp]
    return Lp_mean    
  
  
#input: numero
#output: numero arrotondato a decimale (in base a 10/100/1000/...)
def decimali(x):
    rnd=(int(x*100))/100
    return rnd

def normalizer(fr, n):
    pippo=[]     
    for i in range(0, n):
        dati = np.frombuffer(fr[i], dtype=np.int16)
        pippo.append(dati)
        pippo_normalized = [dati / 32768.0 for dati in pippo]
    return pippo_normalized

import io
import numpy as np
import torch
torch.set_num_threads(1)
import torchaudio
torchaudio.set_audio_backend("soundfile")
import pyaudio
import threading
import os
import math
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QCoreApplication
from maad import spl
import time
import mic_add_v2_1 as mcr
import sys
import datetime

################################################# SILERO

model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

def validate(model,
             inputs: torch.Tensor):
    with torch.no_grad():
        outs = model(inputs)
    return outs


def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze()  # depends on the use case
    return sound

################################################# LEQ


p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

for i in range(numdevices):
    if (p.get_device_info_by_index(i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_index(i).get('name'))
        if(p.get_device_info_by_index(i).get('name') == "default"):
            DEV = i # setting the device

################################################# ENTRAMBI

FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK = int(SAMPLE_RATE / 10) #ogni chunck sono 1600 campioni
#settaggio gain e sensibilità
gai=8
sens=-32
reg_leng=0.5  # aggiornato a un quarto di secondo
pond="Z"
_MIN_ = sys.float_info.min
#finestratura
nfin=round(SAMPLE_RATE / CHUNK * reg_leng) #numero finestre utilizzate
t_true=nfin*CHUNK/SAMPLE_RATE #tempo di campionamento vero
t = 0
Leq_tot=0

################################################# SILERO

data = []
voiced_confidences = []

global continue_recording
continue_recording = True
global new_confidence
global voiced_confidence
global line

################################################# MAIN LOOP

while True: 
    
    stream = p.open(format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK)

    frames = []                                            
    for i in range(0, nfin):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)         
        audio_int16 = np.frombuffer(data, np.int16); # converte i dati grezzi che ha letto in campioni audio a 16 bit
        audio_float32 = int2float(audio_int16) # converte i campioni a 16 bit in 32 bit usando la funzione prima definita
        new_confidence = model(torch.from_numpy(audio_float32), 16000).item() # passiamo al modello il campione in 32 bit per

    #print("livello della voce: ", new_confidence)                    
    stream.stop_stream()
    stream.close()
    #normalizzazione del segnale fatta UNIPG
    #questo è un livello equivalente di un reg_lengh
    norm=mcr.normalizer(frames, nfin)
    w = np.hstack(norm) 
    # istantaneous sound pressure in pascal
    sound_pressure = spl.wav2pressure(wave=w, gain=gai, sensitivity=sens)
    #equivalent sound pressure level 
    #questi è il leq del singolo pezzo
    Leq_result = spl.wav2leq (w, SAMPLE_RATE, gain=gai,dt=len(w)/SAMPLE_RATE , sensitivity=sens)
    #print("Equivalent Continuous Sound pressure Level Leq (dB):", mcr.decimali(Leq_result))
    print("voce: ", new_confidence," LEQ: ", mcr.decimali(Leq_result))
    Lp=mcr.levelsoct(sound_pressure, pond)
    t=t+t_true
    s=0
    for i in range(len(Lp)):
        summ=(10**(Lp[i]/10))
        s=s+summ
        #questo è il leq totale
        Leq=mcr.decimali(10*np.log10((1/1)*s))
    #print("Leq (dB): ", Leq)
                
            
    #questo è il livello equivalente mediato su tutto il periodo
    Leq_tot=10*np.log10((1/t)*((t-t_true)*10**(Leq_tot/10)+t_true*10**(Leq/10)))

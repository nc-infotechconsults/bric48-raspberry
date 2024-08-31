import numpy as np
import torch
torch.set_num_threads(1)
import torchaudio
torchaudio.set_audio_backend("soundfile")
import pyaudio
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QCoreApplication
from maad import spl
import mic_add_v2_1 as mcr
import sys

################################################# SILERO

# carichiamo il modello silero vad
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze() 
    return sound


p = pyaudio.PyAudio()



FORMAT = pyaudio.paInt16
CHANNELS = 1
# il modello silero vad funziona con sample rate 16000 e chunk da 512, tuttavia i microfoni che impieghiamo non supportano
# la registrazione a 16000 hz, ma solo a 48000 (che è il triplo di 16000) quindi triplichiamo anche il chunk così da ottenere
# dei chunk proporzionati a quel sample rate e poi facciamo successivamente il resample a 16000, prima di applicare il modello
# silero vad per la predizione della voce
SAMPLE_RATE = 16000 * 3 #48000 
CHUNK = 512 * 3 #1536

#settaggio gain e sensibilità (codici forniti da università di perugia)
gai=8
sens=-32
reg_leng=1  # aggiornato a un quarto di secondo
pond="Z"
_MIN_ = sys.float_info.min
#finestratura
nfin=round(SAMPLE_RATE / CHUNK * reg_leng) #numero finestre utilizzate
t_true=nfin*CHUNK/SAMPLE_RATE #tempo di campionamento vero
t = 0
Leq_tot=0


data = []
voiced_confidences = [] # lista che conterrà le predizioni su ogni chunk
global new_confidence # contiene la predizione sull'ultimo chunk

################################################# MAIN LOOP

# Resample transformation
resample_transform = torchaudio.transforms.Resample(orig_freq=SAMPLE_RATE, new_freq=16000)

# Obtain and print the input device name
#DEV = 1  # Adjust this index based on your needs
#device_info = p.get_device_info_by_index(DEV)
#input_device_name = device_info['name']
#print("Input device name:", input_device_name)

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
        audio_int16 = np.frombuffer(data, np.int16) # converte i dati grezzi che ha letto in campioni audio a 16 bit
        audio_float32 = int2float(audio_int16) # converte i campioni a 16 bit in 32 bit usando la funzione prima definita
        # Resample from 48000 Hz to 16000 Hz
        audio_resampled = resample_transform(torch.from_numpy(audio_float32))
        new_confidence = model(audio_resampled, 16000).item() # passiamo al modello il campione in 32 bit a 16000 hz

                    
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
    Leq_result = spl.wav2leq(w, SAMPLE_RATE, gain=gai, dt=len(w)/SAMPLE_RATE, sensitivity=sens)


    # stampiamo sia il livello di voce predetto che il rumore dell'area in decibel
    print("voce: ", new_confidence," LEQ: ", mcr.decimali(Leq_result))
    Lp=mcr.levelsoct(sound_pressure, pond)
    t=t+t_true
    s=0
    for i in range(len(Lp)):
        summ=(10**(Lp[i]/10))
        s=s+summ
        #questo è il leq totale
        Leq=mcr.decimali(10*np.log10((1/1)*s))
                
            
    #questo è il livello equivalente mediato su tutto il periodo
    Leq_tot=10*np.log10((1/t)*((t-t_true)*10**(Leq_tot/10)+t_true*10**(Leq/10)))

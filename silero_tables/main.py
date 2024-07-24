import io
import os
import numpy as np
import torch
import torchaudio
import matplotlib.pyplot as plt
import argparse
import pyaudio
import warnings
import logging
import math

# Suppress warnings
warnings.filterwarnings("ignore")

# Suppress PyTorch logging messages
logging.getLogger('torch').setLevel(logging.WARNING)

# Argument parser for file path
parser = argparse.ArgumentParser(description="Voice Activity Detection")
parser.add_argument('file_path', type=str, help='Path to the audio file')
args = parser.parse_args()

# carichiamo il modello silero ad
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

FORMAT = pyaudio.paInt16
SAMPLE_RATE = 16000
CHUNK = 512 

# prendiamo ora il percorso del file che è stato passato come parametro e carichiamolo in memoria con torchaudio.load
file_path = args.file_path
waveform, sample_rate = torchaudio.load(file_path)
duration_seconds = math.ceil(float(waveform.size(1)) / sample_rate) # così facendo si ottiene la durata del file in secondi e ogni gruppo di chunk rappresenta un secondo
                                                                    # puoi anche cambiare per avere che ad esempio viene fatta la media su gruppi che rappresentano mezzo secondo

# silero vad funziona con file con frequenza di campionamento a 8000 o 16000 hz, quindi facciamo il resample del
# file che abbiamo appena caricato in memoria
if sample_rate != SAMPLE_RATE:
    resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=SAMPLE_RATE)
    waveform = resampler(waveform)

# Convert to mono if stereo
if waveform.shape[0] > 1:
    waveform = waveform.mean(dim=0, keepdim=True)

# Convert PyTorch tensor to numpy array. Poi trasformiamo i dati audio in un formato a 32 bit
waveform_numpy = waveform.squeeze().numpy()
audio_int16 = (waveform_numpy * 32768).astype(np.int16)
audio_float32 = int2float(audio_int16)


voiced_confidences = [] # Lista per memorizzare le predizioni del modello per ciascun chunk audio.
time_points = [] # Lista per memorizzare i punti temporali di ciascun chunk.
num_chunks = len(audio_float32) // CHUNK # # Calcola il numero totale di chunk nell'audio.
num_chunks_per_second = math.ceil(num_chunks / duration_seconds)  # Calcola il numero di chunk per secondo.


# Itera attraverso ciascun chunk dell'audio. Ora su ogni chunk faremo la predizione
for i in range(num_chunks):
    start = i * CHUNK  # Inizio del chunk corrente.
    end = start + CHUNK  # Fine del chunk corrente.
    chunk = audio_float32[start:end]  # Estrarre il chunk dall'audio.

    # Se il chunk è più corto della dimensione prevista, aggiungi zeri alla fine.
    if len(chunk) < CHUNK:
        chunk = np.pad(chunk, (0, CHUNK - len(chunk)))

    # Ottieni la nuova predizione di confidenza del modello per il chunk corrente.
    new_confidence = model(torch.from_numpy(chunk), SAMPLE_RATE).item()
    voiced_confidences.append(new_confidence)  # Aggiungi la confidenza alla lista.
    time_points.append(start / SAMPLE_RATE)  # Aggiungi il punto temporale alla lista.


# Crea una figura per il plot.
fig, ax = plt.subplots(figsize=(20, 6))
ax.plot(time_points, voiced_confidences, lw=2)  # Plotta le previsioni nel tempo.
ax.set_xlim(0, len(audio_float32) / SAMPLE_RATE)  
ax.set_ylim(0, 1)  
ax.set_xlabel('Time (seconds)') 
ax.set_ylabel('Voice Confidence')
ax.set_title('Voice Activity Detection')
ax.grid(True)

# Crea la directory 'plot' se non esiste.
output_dir = 'plot'
os.makedirs(output_dir, exist_ok=True)

# Salviamo il plot come file pdf all'interno della directory "plot"
base_filename = os.path.splitext(os.path.basename(file_path))[0]
pdf_file_path = os.path.join(output_dir, f"{base_filename}.pdf")
fig.savefig(pdf_file_path)
plt.close(fig) 

# Apre il file 'confidences.csv' in modalità append.
with open("confidences.csv", 'a') as file:
    file.write(os.path.basename(file_path) + ";")  # Scrivi il nome del file audio nel CSV.

# Adesso prendiamo gruppi di "num_chunk_per_second" elementi dalla lista voiced_confidences e fai la media
# su quelle predizioni. In questo modo ottieni la predizione media per ogni secondo e fai l'append su file csv
for i in range(0, len(voiced_confidences), num_chunks_per_second):
    group = voiced_confidences[i:i + num_chunks_per_second] 
    mean_chunk = np.mean(group)  
    
    with open("confidences.csv", 'a') as file:
        file.write(str(mean_chunk) + ";")

# Calcola la media della predizioni di tutto l'audio e fai l'append sul file csv
mean_confidence = np.mean(voiced_confidences)
print(f"{os.path.basename(file_path)}: {mean_confidence}")  
with open("confidences.csv", 'a') as file:
    file.write(str(mean_confidence) + "\n") 

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
from maad import spl

# Suppress warnings
warnings.filterwarnings("ignore")

# Suppress PyTorch logging messages
logging.getLogger('torch').setLevel(logging.WARNING)

# Argument parser for file path
parser = argparse.ArgumentParser(description="Voice Activity Detection")
parser.add_argument('file_path', type=str, help='Path to the audio file')
args = parser.parse_args()

# Load the Silero VAD model
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
        sound *= 1 / 32768
    sound = sound.squeeze()
    return sound

SAMPLE_RATE = 16000
CHUNK = 512
gai = 8
sens = -32

# Load the audio file
file_path = args.file_path
waveform, sample_rate = torchaudio.load(file_path)
duration_seconds = math.ceil(float(waveform.size(1)) / sample_rate)
num_channels = waveform.shape[0]

# Resample if necessary
if sample_rate != SAMPLE_RATE:
    resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=SAMPLE_RATE)
    waveform = resampler(waveform)

# Convert to mono if stereo
if waveform.shape[0] > 1:
    waveform = waveform.mean(dim=0, keepdim=True)

# Print audio file information
print(f"Name: {os.path.basename(file_path)}")
print(f"Audio Duration: {duration_seconds} seconds")
print(f"Original Sample Rate: {sample_rate} Hz")
print(f"New Sample Rate: {SAMPLE_RATE} Hz")
print(f"Original Number of Channels: {num_channels}")
print(f"New Number of Channels: 1")

# Convert to numpy array and prepare audio data
waveform_numpy = waveform.squeeze().numpy()
audio_int16 = (waveform_numpy * 32768).astype(np.int16)
audio_float32 = int2float(audio_int16)
voiced_confidences = []
Leq_list = []
time_points = []
num_chunks = len(audio_float32) // CHUNK
num_chunks_per_second = math.ceil(num_chunks / duration_seconds)

# Process each audio chunk to compute model prediction
for i in range(num_chunks):
    start = i * CHUNK
    end = start + CHUNK
    chunk = audio_float32[start:end]

    # Pad with zeros if necessary
    if len(chunk) < CHUNK:
        chunk = np.pad(chunk, (0, CHUNK - len(chunk)))

    # Get model prediction for current chunk
    new_confidence = model(torch.from_numpy(chunk), SAMPLE_RATE).item()
    voiced_confidences.append(new_confidence)
    time_points.append(start / SAMPLE_RATE)

# Process each second of the audio to compute Leq
for i in range(0, len(audio_int16), SAMPLE_RATE):
    group = audio_int16[i:i+SAMPLE_RATE]
    norm = group / 32768.0
    w = np.hstack(norm)
    Leq_result = spl.wav2leq(w, SAMPLE_RATE, gain=gai, dt=len(w)/SAMPLE_RATE, sensitivity=sens)
    Leq_result = float(Leq_result)
    Leq_list.append(Leq_result)














'''
CREAZIONE DEL PLOT SU PDF
'''

# Create a plot
fig, ax1 = plt.subplots(figsize=(20, 6))

# Plot voiced_confidences on the primary y-axis
ax1.plot(time_points, voiced_confidences, lw=2, color='blue', label='Voice Confidence')
ax1.set_xlim(0, len(audio_float32) / SAMPLE_RATE)
ax1.set_ylim(0, 1)
ax1.set_xlabel('Time (seconds)')
ax1.set_ylabel('Voice Confidence', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True)

# Create a secondary y-axis for Leq_list
ax2 = ax1.twinx()
ax2.plot(np.arange(1, len(Leq_list) + 1), Leq_list, lw=2, color='red', label='Leq')
ax2.set_ylim(min(Leq_list) - 5, max(Leq_list) + 5)
ax2.set_ylabel('Leq (dB)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Title and legends
ax1.set_title('Voice Activity Detection and Leq over Time')
fig.tight_layout()

# Create 'plot' directory if it doesn't exist
output_dir = 'plot'
os.makedirs(output_dir, exist_ok=True)

# Save the plot as a PDF
base_filename = os.path.splitext(os.path.basename(file_path))[0]
pdf_file_path = os.path.join(output_dir, f"{base_filename}_with_leq.pdf")
fig.savefig(pdf_file_path)
plt.close(fig)

print(f"Created PDF with Leq: {pdf_file_path}")














'''
CREAZIONE/SCRITTURA SUL FILE CSV
'''

import re  # Importiamo re per lavorare con le espressioni regolari


# Funzione per estrarre valori nel formato originale
def estrai_valori(file_name):
    match = re.match(r"([a-z]+)_([a-zA-Z0-9]+)_([a-zA-Z0-9]+)_([a-zA-Z0-9_]+)\.wav", file_name)
    if match:
        rumore = match.group(1)
        distanza_operatore = match.group(2).replace('neg', '-') + " metri dal rumore"
        distanza_voce = match.group(3).replace('neg', '-') + " metri dal rumore"
        nome_voce = match.group(4)
        return rumore, distanza_operatore, distanza_voce, nome_voce
    else:
        return "NA", "NA", "NA", "NA"
    

# Nuova funzione per il formato amb_x_y_z,w
def estrai_valori_2(file_name):
    match = re.match(r"(amb)_([a-zA-Zèé]+)_([0-9]+)_([a-zA-Z0-9_]+)\.wav", file_name)
    if match:
        rumore = "rumore ambientale"
        distanza_operatore = match.group(2)
        distanza_voce = match.group(3) + " metri da " + distanza_operatore
        nome_voce = match.group(4)
        return rumore, distanza_operatore, distanza_voce, nome_voce
    else:
        return "NA", "NA", "NA", "NA"
    

# Aggiornamento dell'header per includere le colonne 'rumore', 'distanza_operatore', 'distanza_voce', 'nome_voce'
header = "NOME DEL FILE; SORGENTE RUMOROSA; POSIZIONE OPERATORE; POSIZIONE VOCE; NOME VOCE;"
for i in range(1, duration_seconds + 1):
    header += f"SECONDO NUMERO {i} (VAD e LEQ);"
header += "LIVELLO MEDIO (VAD e LEQ)\n"

csv_file_path = "confidences.csv"

# Scrivi l'header solo se non è già presente
if not os.path.isfile(csv_file_path) or (header not in open(csv_file_path).read()):
    with open(csv_file_path, 'a') as file:
        file.write(header)

# Estrai il nome base del file (senza percorso) e i valori da aggiungere
file_name = os.path.basename(file_path)

# Controlla se il file inizia con "amb" e usa la funzione appropriata
if file_name.startswith("amb"):
    rumore, distanza_operatore, distanza_voce, nome_voce = estrai_valori_2(file_name)
else:
    rumore, distanza_operatore, distanza_voce, nome_voce = estrai_valori(file_name)

# Aggiungi il nome del file e i valori nel CSV
with open(csv_file_path, 'a') as file:
    file.write(f"{file_name}; {rumore}; {distanza_operatore}; {distanza_voce}; {nome_voce};")

# Calcola e scrivi la media delle predizioni per ogni secondo
for i in range(0, len(voiced_confidences), num_chunks_per_second):
    group = voiced_confidences[i:i + num_chunks_per_second]
    mean_chunk = np.mean(group)
    with open(csv_file_path, 'a') as file:
        file.write(f"{mean_chunk:.5f};")

# Calcola la media complessiva delle predizioni
mean_confidence = np.mean(voiced_confidences)
print(f"Mean confidence: {mean_confidence:.5f}")
with open(csv_file_path, 'a') as file:
    file.write(f"{mean_confidence:.5f}\n")

# Scrittura 5 celle vuote
with open(csv_file_path, 'a') as file:
    file.write(";")
    file.write(";")
    file.write(";")
    file.write(";")
    file.write(";")

# Scrittura della media Leq per ogni secondo
with open(csv_file_path, 'a') as file:
    for i in range(len(Leq_list)):
        file.write(f"{Leq_list[i]:.1f};")

# Calcolo e scrittura della media complessiva di Leq
mean_leq = np.mean(Leq_list)
print(f"Mean LEQ: {mean_leq:.1f}")
with open(csv_file_path, 'a') as file:
    file.write(f"{mean_leq:.1f}\n")

print("Updated confidences.csv")


print("\n")

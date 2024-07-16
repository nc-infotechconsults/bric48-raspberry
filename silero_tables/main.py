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
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK = 512 

file_path = args.file_path
waveform, sample_rate = torchaudio.load(file_path)
duration_seconds = math.ceil(float(waveform.size(1)) / sample_rate) # così facendo si ottiene la durata del file in secondi e ogni gruppo di chunk rappresenta un secondo
                                                                    # puoi anche cambiare per avere che ad esempio viene fatta la media su gruppi che rappresentano mezzo secondo

target_sample_rate = 16000
if sample_rate != target_sample_rate:
    resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sample_rate)
    waveform = resampler(waveform)

# Convert to mono if stereo
if waveform.shape[0] > 1:
    waveform = waveform.mean(dim=0, keepdim=True)

# Convert PyTorch tensor to numpy array
waveform_numpy = waveform.squeeze().numpy()
audio_int16 = (waveform_numpy * 32768).astype(np.int16)
audio_float32 = int2float(audio_int16)

voiced_confidences = []
time_points = []
num_chunks = len(audio_float32) // CHUNK
num_chunks_per_second = math.ceil(num_chunks / duration_seconds)

for i in range(num_chunks):
        start = i * CHUNK
        end = start + CHUNK
        chunk = audio_float32[start:end]

        if len(chunk) < CHUNK:
            chunk = np.pad(chunk, (0, CHUNK - len(chunk)))

        new_confidence = model(torch.from_numpy(chunk), SAMPLE_RATE).item()
        voiced_confidences.append(new_confidence)
        time_points.append(start / SAMPLE_RATE)

fig, ax = plt.subplots(figsize=(20, 6))
ax.plot(time_points, voiced_confidences, lw=2)
ax.set_xlim(0, len(audio_float32) / SAMPLE_RATE)
ax.set_ylim(0, 1)
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Voice Confidence')
ax.set_title('Voice Activity Detection')
ax.grid(True)

# Create the 'plot' directory if it does not exist
output_dir = 'plot'
os.makedirs(output_dir, exist_ok=True)

# Construct the PDF file path
base_filename = os.path.splitext(os.path.basename(file_path))[0]
pdf_file_path = os.path.join(output_dir, f"{base_filename}.pdf")

# Save the plot as a PDF file
fig.savefig(pdf_file_path)

plt.close(fig)  # Close the figure to free up memory



with open("confidences.csv", 'a') as file:
    file.write(os.path.basename(file_path) + ";")



for i in range(0, len(voiced_confidences), num_chunks_per_second):
    # Prendiamo i valori del gruppo corrente
    group = voiced_confidences[i:i + num_chunks_per_second]
    # Calcoliamo la media del gruppo corrente
    mean_chunk = np.mean(group)
    # Stampiamo la media
    with open("confidences.csv", 'a') as file:
        file.write(str(mean_chunk) + ";")



# Calculate and print the mean voice confidence value of the whole audio
mean_confidence = np.mean(voiced_confidences)
print(f"{os.path.basename(file_path)}: {mean_confidence}")
with open("confidences.csv", 'a') as file:
    file.write(str(mean_confidence) + "\n")

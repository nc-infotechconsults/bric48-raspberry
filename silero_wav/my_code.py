import io
import numpy as np
import torch
torch.set_num_threads(1)
import torchaudio
import matplotlib
import matplotlib.pylab as plt
torchaudio.set_audio_backend("soundfile")
import pyaudio

import datetime


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
    sound = sound.squeeze()  # depends on the use case
    return sound


FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK = int(SAMPLE_RATE / 10) #ogni chunck sono 1600 campioni
audio = pyaudio.PyAudio()

file_path = 'test1.wav'  

waveform, sample_rate = torchaudio.load(file_path)

target_sample_rate = 16000
if sample_rate != target_sample_rate:
    resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sample_rate)
    waveform = resampler(waveform)


# Calcola la lunghezza totale del waveform
total_samples = waveform.size(1)

# Specifica la dimensione del chunk
chunk_size = 512

# Calcola il numero di chunk
num_chunks = (total_samples + chunk_size - 1) // chunk_size

voiced_confidences = []

# Iterare sui chunk di 512 campioni
for i in range(num_chunks):
    start = i * chunk_size
    end = start + chunk_size
    chunk = waveform[:, start:end]
    if chunk.shape[1] < chunk_size:
        # Zero-padding se il chunk è più corto di 512 campioni
        chunk = torch.nn.functional.pad(chunk, (0, chunk_size - chunk.shape[1]))

    # Convert to mono if stereo
    if chunk.shape[0] > 1:
        chunk = chunk.mean(dim=0, keepdim=True)

    # Convert PyTorch tensor to numpy array
    chunk_numpy = chunk.squeeze().numpy()
    
    # Ensure the data is in the correct format (int16)
    audio_int16 = (chunk_numpy * 32768).astype(np.int16)
    
    audio_float32 = int2float(audio_int16)
    new_confidence = model(torch.from_numpy(audio_float32), 16000).item()
    voiced_confidences.append(new_confidence)

# Calculate the duration of each chunk in seconds
chunk_duration = chunk_size / SAMPLE_RATE

# Create an array of time points in seconds
time_points = np.arange(len(voiced_confidences)) * chunk_duration

plt.figure(figsize=(20, 6))
plt.plot(time_points, voiced_confidences)
plt.xlabel('Time (seconds)')
plt.ylabel('Voice Confidence')
plt.title('Voice Activity Detection')
plt.grid(True)
plt.show()


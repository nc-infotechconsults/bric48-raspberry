import io
import numpy as np
import torch
torch.set_num_threads(1)
import torchaudio
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pyaudio
import threading
import time
import argparse

# Argument parser for file path
parser = argparse.ArgumentParser(description="Voice Activity Detection with Real-Time Plotting")
parser.add_argument('file_path', type=str, help='Path to the audio file')
args = parser.parse_args()

torchaudio.set_audio_backend("soundfile")
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
CHUNK = 512  # Changed chunk size to 512
audio = pyaudio.PyAudio()

file_path = args.file_path
waveform, sample_rate = torchaudio.load(file_path)

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

stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True)

fig, ax = plt.subplots(figsize=(20, 6))
ax.set_xlim(0, len(audio_float32) / SAMPLE_RATE)
ax.set_ylim(0, 1)
line, = ax.plot([], [], lw=2)
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Voice Confidence')
ax.set_title('Voice Activity Detection')
ax.grid(True)

voiced_confidences = []
time_points = []
start_time = None

def update_plot(frame):
    global voiced_confidences, time_points, start_time
    
    if start_time is None:
        start_time = time.time()
    
    elapsed_time = time.time() - start_time
    frame_index = int(elapsed_time * SAMPLE_RATE // CHUNK)
    
    if frame_index * CHUNK >= len(audio_float32):
        return line,
    
    start = frame_index * CHUNK
    end = start + CHUNK
    chunk = audio_float32[start:end]
    
    if len(chunk) < CHUNK:
        chunk = np.pad(chunk, (0, CHUNK - len(chunk)))
    
    new_confidence = model(torch.from_numpy(chunk), SAMPLE_RATE).item()
    voiced_confidences.append(new_confidence)
    time_points.append(elapsed_time)
    
    line.set_data(time_points, voiced_confidences)
    
    return line,

def play_audio():
    stream.write(audio_int16.tobytes())
    stream.stop_stream()
    stream.close()
    audio.terminate()

audio_thread = threading.Thread(target=play_audio)
audio_thread.start()

ani = animation.FuncAnimation(fig, update_plot, frames=range(0, len(audio_float32) // CHUNK),
                              interval=(CHUNK / SAMPLE_RATE) * 1000, blit=True)

plt.show()

audio_thread.join()

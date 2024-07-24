import io
import numpy as np
import torch
torch.set_num_threads(1)  # Limita il numero di thread per PyTorch
import torchaudio
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pyaudio
import threading
import time
import argparse

# Parser degli argomenti per ottenere il percorso del file audio
parser = argparse.ArgumentParser(description="Voice Activity Detection with Real-Time Plotting")
parser.add_argument('file_path', type=str, help='Path to the audio file')
args = parser.parse_args()

# Imposta il backend audio di torchaudio
torchaudio.set_audio_backend("soundfile")

# Carica il modello Silero VAD da Torch Hub
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)

# Estrai le utility dal modello
(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

# Funzione per convertire un array numpy int16 in float32
def int2float(sound):
    abs_max = np.abs(sound).max()  # Trova il valore assoluto massimo
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768  # Normalizza i valori in [-1, 1]
    sound = sound.squeeze()  # Rimuove dimensioni singole
    return sound

# Configurazione PyAudio
FORMAT = pyaudio.paInt16  # Formato dell'audio
CHANNELS = 1  # Canale mono
SAMPLE_RATE = 16000  # Frequenza di campionamento
CHUNK = 512  # Dimensione del chunk (512 campioni)
audio = pyaudio.PyAudio()

# Carica il file audio
file_path = args.file_path
waveform, sample_rate = torchaudio.load(file_path)

# Resample se la frequenza di campionamento è diversa da quella target
target_sample_rate = 16000
if sample_rate != target_sample_rate:
    resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sample_rate)
    waveform = resampler(waveform)

# Converte in mono se l'audio è stereo
if waveform.shape[0] > 1:
    waveform = waveform.mean(dim=0, keepdim=True)

# Converte il tensor PyTorch in un array numpy
waveform_numpy = waveform.squeeze().numpy()
audio_int16 = (waveform_numpy * 32768).astype(np.int16)  # Converte in int16
audio_float32 = int2float(audio_int16)  # Converte in float32

# Apri un flusso audio con PyAudio
stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True)

# Inizializza il grafico
fig, ax = plt.subplots(figsize=(20, 6))
ax.set_xlim(0, len(audio_float32) / SAMPLE_RATE)  # Imposta l'intervallo dell'asse x
ax.set_ylim(0, 1)  # Imposta l'intervallo dell'asse y
line, = ax.plot([], [], lw=2)  # Linea iniziale vuota
ax.set_xlabel('Time (seconds)')  # Etichetta asse x
ax.set_ylabel('Voice Confidence')  # Etichetta asse y
ax.set_title('Voice Activity Detection')  # Titolo del grafico
ax.grid(True)  # Aggiungi la griglia

# Liste per memorizzare le confidenze vocali e i punti temporali
voiced_confidences = []
time_points = []
start_time = None  # Tempo di inizio

# Funzione per aggiornare il grafico in tempo reale
def update_plot(frame):
    global voiced_confidences, time_points, start_time
    
    if start_time is None:
        start_time = time.time()  # Imposta il tempo di inizio
    
    elapsed_time = time.time() - start_time  # Calcola il tempo trascorso
    frame_index = int(elapsed_time * SAMPLE_RATE // CHUNK)  # Indice del frame corrente
    
    if frame_index * CHUNK >= len(audio_float32):
        return line,
    
    start = frame_index * CHUNK
    end = start + CHUNK
    chunk = audio_float32[start:end]
    
    if len(chunk) < CHUNK:
        chunk = np.pad(chunk, (0, CHUNK - len(chunk)))  # Padding se il chunk è troppo corto
    
    # Calcola la confidenza vocale per il chunk corrente
    new_confidence = model(torch.from_numpy(chunk), SAMPLE_RATE).item()
    voiced_confidences.append(new_confidence)  # Aggiungi la confidenza alla lista
    time_points.append(elapsed_time)  # Aggiungi il tempo trascorso alla lista
    
    # Aggiorna i dati del grafico
    line.set_data(time_points, voiced_confidences)
    
    return line,

# Funzione per riprodurre il file audio
def play_audio():
    stream.write(audio_int16.tobytes())  # Scrive i dati audio nel flusso
    stream.stop_stream()  # Ferma il flusso
    stream.close()  # Chiude il flusso
    audio.terminate()  # Termina PyAudio

# Avvia la riproduzione audio in un thread separato
audio_thread = threading.Thread(target=play_audio)
audio_thread.start()

# Imposta l'animazione per la visualizzazione in tempo reale
ani = animation.FuncAnimation(fig, update_plot, frames=range(0, len(audio_float32) // CHUNK),
                              interval=(CHUNK / SAMPLE_RATE) * 1000, blit=True)

# Mostra il grafico
plt.show()

# Attende che il thread audio termini
audio_thread.join()

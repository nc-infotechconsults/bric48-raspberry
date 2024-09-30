from pydub import AudioSegment
import pyaudio
import wave
from gtts import gTTS

# Funzione per convertire in WAV
def convert_to_wav_pcm(input_file, output_file):
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(48000).set_sample_width(2).set_channels(2)  # 16 bit PCM stereo
    audio.export(output_file, format="wav")

# Funzione per scegliere le schede audio
def choose_device(p):
    print("Schede audio disponibili:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"{i}: {dev['name']} - Canali di uscita: {dev['maxOutputChannels']}")

    dev1 = int(input("Scegli la prima scheda audio (numero): "))
    dev2 = int(input("Scegli la seconda scheda audio (numero): "))
    
    return dev1, dev2

# Funzione principale
def main():

    # sintetizzatore vocale
    tts = gTTS(text="Salve a tutti", lang='it')
    tts.save("output.wav")

    # Converti il file se necessario
    convert_to_wav_pcm('output.wav', 'output_pcm.wav')  # Cambia il nome del file di input se necessario

    # Apri il file WAV
    filename = 'output_pcm.wav'
    wf = wave.open(filename, 'rb')

    # Verifica se la frequenza di campionamento è corretta
    if wf.getframerate() != 48000:
        print("Il file non è campionato a 48000 Hz, convertilo prima!")
        return

    # Inizializza PyAudio
    p = pyaudio.PyAudio()

    # Scegli le due schede audio
    dev1, dev2 = choose_device(p)

    # Apri i flussi per entrambe le schede audio
    stream1 = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                     channels=wf.getnchannels(),
                     rate=wf.getframerate(),
                     output=True,
                     output_device_index=dev1)

    stream2 = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                     channels=wf.getnchannels(),
                     rate=wf.getframerate(),
                     output=True,
                     output_device_index=dev2)

    # Riproduzione simultanea sui due dispositivi
    print(f"Riproduzione su dispositivi {dev1} e {dev2} in corso...")

    # Legge i frame audio e li invia ai due stream contemporaneamente
    data = wf.readframes(1024)
    while data:
        stream1.write(data)
        stream2.write(data)
        data = wf.readframes(1024)

    # Chiudi i flussi
    stream1.stop_stream()
    stream1.close()

    stream2.stop_stream()
    stream2.close()

    # Termina PyAudio
    p.terminate()
    print("Riproduzione completata.")

if __name__ == "__main__":
    main()

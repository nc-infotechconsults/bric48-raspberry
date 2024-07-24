import os
import subprocess

# Definisce il percorso delle cartelle e dei file
plot_dir = "plot"
confidences_file = "confidences.csv"
files_dir = "files"




# Funzione per svuotare la cartella. La usiamo per svuotare la cartella che contiene
# i plot in pdf
def svuota_cartella(cartella):
    for filename in os.listdir(cartella):
        file_path = os.path.join(cartella, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Errore durante la cancellazione del file {file_path}. Dettagli: {e}")



# funzione per svuotare il contenuto del file csv in cui sono scritte le predizioni, e scrivere il nuovo header
def cancella_contenuto_file(filepath):
    try:
        with open(filepath, 'w') as f:
            f.write("File name; voice_1_group; voice_2_group; voice_3_group; voice_4_group; voice_5_group; voice_6_group; voice_7_group; voice_mean\n")
    except Exception as e:
        print(f"Errore durante la cancellazione del contenuto del file {filepath}. Dettagli: {e}")




# Funzione per ottenere tutti i file .wav dalla cartella "files" che li contiene
def ottieni_file_wav(cartella):
    try:
        return [f for f in os.listdir(cartella) if f.endswith('.wav')]
    except Exception as e:
        print(f"Errore durante l'ottenimento dei file .wav dalla cartella {cartella}. Dettagli: {e}")
        return []
    



# Svuota la cartella "plot"
svuota_cartella(plot_dir)

# Cancella il contenuto del file "confidences.txt"
cancella_contenuto_file(confidences_file)

# Ottieni tutti i file .wav dalla cartella "files"
file_wav_list = ottieni_file_wav(files_dir)

# Per ogni file .wav nella cartella files eseguiamo il codice "main.py"
for file_wav in file_wav_list:
    comando = ["python", "main.py", os.path.join(files_dir, file_wav)]
    try:
        subprocess.run(comando, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione del comando per il file {file_wav}: {e}")

import os
import subprocess

# Definisce il percorso delle cartelle e dei file
plot_dir = "plot"
confidences_file = "confidences.csv"
files_dir = "files"




# Funzione per svuotare la cartella
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




def cancella_contenuto_file(filepath):
    try:
        # Apri il file in modalità scrittura ('w'), se non esiste verrà creato
        with open(filepath, 'w') as f:
            # Scrivi l'intestazione nel file
            f.write("File name; voice_1_group; voice_2_group; voice_3_group; voice_4_group; voice_5_group; voice_6_group; voice_7_group; voice_mean\n")
    except Exception as e:
        print(f"Errore durante la cancellazione del contenuto del file {filepath}. Dettagli: {e}")




# Funzione per ottenere tutti i file .wav dalla cartella
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

# Esegui il comando per ogni file .wav trovato
for file_wav in file_wav_list:
    comando = ["python", "main.py", os.path.join(files_dir, file_wav)]
    try:
        subprocess.run(comando, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione del comando per il file {file_wav}: {e}")

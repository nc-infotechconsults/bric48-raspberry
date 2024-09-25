import os
import subprocess

# Percorso della cartella
cartella = "files"

# Itera su tutti i file nella cartella
for file_name in os.listdir(cartella):
    file_path = os.path.join(cartella, file_name)
    
    # Verifica che sia un file
    if os.path.isfile(file_path):
        # Esegui il comando main.py <file>
        comando = f"python main.py {file_path}"
        subprocess.run(comando, shell=True)

# COMANDI DA ESEGUIRE PER BLE E MQTT

## Dipendenze da installare con sudo
> sudo apt-get install python3-pip libglib2.0-dev  
> sudo pip3 install bluepy --break-system-packages  
> sudo pip3 install getmac --break-system-packages  
> sudo pip3 install paho-mqtt --break-system-packages     
Probabilmente ci sono altre dipendenze da installare per cui non è necessario usare sudo  

## Comando per avviare
> sudo python3 ble_mqtt.py <ip_backend>


# COMANDI DA ESEGUIRE PER SILERO

## Dipendenze da installare 
> sudo pip3 install numpy --break-system-packages  
> sudo pip3 install torch --break-system-packages  
> sudo pip3 install torchaudio --break-system-packages  
> sudo apt-get install portaudio19-dev  
> sudo pip3 install pyaudio --break-system-packages  
> sudo pip3 install pyside6 --break-system-packages  
> sudo pip3 install scikit-maad --break-system-packages  


## Comando per avviare  
> sudo python3 silero+leq.py
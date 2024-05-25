## Dipendenze da installare con sudo
> sudo apt-get install python3-pip libglib2.0-dev
> sudo pip3 install bluepy --break-system-packages
> sudo pip3 install getmac --break-system-packages
> sudo pip3 install paho-mqtt --break-system-packages   
Probabilmente ci sono altre dipendenze da installare per cui non è necessario usare sudo

## Progetto da avviare con sudo 
> sudo python3 ble_mqtt.py <url_backend>

## Ricorda
Bisogna cambiare l'indirizzo ip delle API con quello dove gira il backend

## To-do list
Aggiungere la gestione di MQTT (subscribe e unsubscribe dinamici)

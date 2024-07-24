import paho.mqtt.client as mqtt
from bluepy.btle import Scanner, DefaultDelegate
import requests
from getmac import get_mac_address as gma
import sys

''' Leggi gli argomenti dalla linea di comando '''
args = sys.argv

if len(args) < 2:
    print("Usage: python ble_mqtt.py <ip backend>")
    exit()


backend_ip = args[1]


''' MQTT '''

# Callback chiamata quando il client si connette al broker
def on_connect(client, userdata, flags, rc):
    print("Connesso al broker con codice risultato: " + str(rc))

# Callback chiamata quando un messaggio viene ricevuto sul topic sottoscritto
def on_message(client, userdata, msg):
    print(f"\nTopic {msg.topic} \nMessaggio: {str(msg.payload)}\n")

# Configurazione del client MQTT
client = mqtt.Client()

# Impostazione delle callback
client.on_connect = on_connect
client.on_message = on_message


# Connessione al broker MQTT
client.connect("test.mosquitto.org", 1883, 60) # broker in remoto, da cambiare in broker locale

# Loop per gestire le connessioni e i messaggi in entrata
client.loop_start()


'''ID HEADPHONES'''

# stampiamo l'indirizzo mac del raspberry (serial delle cuffie)
idHeadphones = gma() 
print("ID Headphone: ", idHeadphones)


'''GET di tutti i macchinari'''

# Esegui la richiesta GET
response = requests.get("http://"+backend_ip+":8080/machinery/getAll")

# Controlla lo stato della risposta
if response.status_code == 200:

    # Decodifica la risposta JSON
    machineries = response.json()

else:
    # Stampa un messaggio di errore
    print("Errore durante la richiesta GET:", response.status_code)



'''GET dei beacon by mserial'''

mserial_beacon = {} # dizionario che mantiene l'associazione fra macchinari e beacon associati
mserial_threshold = {} # dizionario che mantiene l'associazione fra macchinari e soglie dei beacon associati
mserial_flag = {} # dizionario che mantiene l'associazione fra macchinario e vicinanza o meno dai beacon associati

# esempio
# mserial_beacon = { x : [a, b, c], y : [d, e] }
# mserial_threshold = { x : [60, 70, 65], y : [80, 70] }. Il beacon "a" ha soglia "60", il "b" ha soglia "70" e così via...
# mserial_flag = { x : [1, 0, 1], y : [0, 0] }. La cuffia (raspberry) è nei paraggi dei beacon "a" e "c", quindi si sottoscrive al topic del macchinario "x"


# riempiamo ora i 3 dizionari sopra definiti
# eseguiamo questo loop per ogni macchinario
for machinery in machineries:

    # otteniamo i beacon per il determinato macchinario
    response = requests.get("http://"+backend_ip+":8080/beacon/find/" + machinery["mserial"])

    if response.status_code == 200:

        beacons = response.json()

        macs = []
        thresholds = []

        # per ogni beacon ottenuto per quel macchinario, aggiungiamo la sua soglia e il suo mac alle relative listes
        for beacon in beacons:
            macs.append(beacon["mac"].lower())
            thresholds.append(beacon["threshold"])

        # riempimento dei dizionari definiti prima
        mserial_beacon[machinery["mserial"]] = macs
        mserial_threshold[machinery["mserial"]] = thresholds
        mserial_flag[machinery["mserial"]] = [0] * len(macs)
    else:
        print("Errore durante la richiesta GET:", response.status_code)
    
# sottoscrizione al topic della cuffia per ricevere i messaggi personali
client.subscribe("/"+idHeadphones)


'''Scansione bluetooth'''

# Classe per la gestione dei pacchetti Bluetooth ricevuti
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):

        if isNewDev or isNewData: # se arriva un pacchetto da un nuovo dispositivo o da un dispositivo conosciuto
            for mserial, macs in mserial_beacon.items(): # per ogni macchinario prendiamo la lista di beacon associati corrispondente
                if dev.addr in macs: # se il pacchetto bluetooth arrivato viene da un beacon presente nella lista

                    idx = macs.index(dev.addr) # salviamo l'indice che ha il beacon nella lista.

                    # se l'RSSI del pacchetto è sopra la soglia
                    if dev.rssi > -int(mserial_threshold[mserial][idx]):

                        if mserial_flag[mserial][idx] == 0: # se il flag di quel beacon è 0 (ossia se non eravamo già nelle vicinanze di quel beacon)
                            
                            mserial_flag[mserial][idx] = 1 # impostiamoci come "nei pressi" di quel beacon
                            
                            # questo flag serve per vedere se tutti gli altri flag del macchinario erano a 0. In tal caso infatti significa che
                            # non eravamo iscritti al topic di quel macchinario e ci dobbiamo iscrivere
                            flag = True
                            for i in range(0, len(macs)):
                                if i != idx:
                                    if mserial_flag[mserial][i] == 1:
                                        flag = False

                            if flag == True:
                                client.subscribe("/"+mserial) # sottoscrizione al topic del macchinario
                                print("subscribed con threshold ", -(int(mserial_threshold[mserial][idx])))

                                # prendiamo il macchinario di cui stiamo nei paraggi dal db
                                response = requests.get("http://"+backend_ip+":8080/machinery/find/machinery/" + mserial) 
                                if response.status_code == 200:
                                    m = response.json()
                                else:
                                    print("Errore durante la richiesta GET:", response.status_code)

                                # creiamo il payload da aggiungere nel db alla collezione "nearbyHeadphones". Così nel db
                                # risulterà che tale cuffia è nei pressi del macchinario
                                payload = {
                                    "serial": idHeadphones,
                                    "mserial": mserial,
                                    "idRoom": m["idRoom"],
                                    "idBranch": m["idBranch"]
                                }
                                headers = {'Content-Type': 'application/json'}
                                r = requests.post("http://"+backend_ip+":8080/nearbyHeadphones/add", json=payload, headers=headers)

                                if r.status_code != 200:
                                    print("Errore nella richiesta:", r.status_code)
                    
                    # se l'RSSI del pacchetto ricevuto è sotto la soglia
                    else:

                        if mserial_flag[mserial][idx] == 1: # se eravamo nei pressi di quel beacon

                            mserial_flag[mserial][idx] = 0 # cambiamo il flag a 0 per indicare che ci siamo allontanati da quel beacon
                            
                            # questo flag serve per vedere se tutti gli altri flag del macchinario erano a 0. In tal caso infatti significa che
                            # quel beacon era l'unico beacon del macchinario a cui eravamo vicini e siccome ci siamo allontanati possiamo disiscriverci dal topic del macchinario
                            flag = True
                            for i in range(0, len(macs)):
                                if i != idx:
                                    if mserial_flag[mserial][i] == 1:
                                        flag = False

                            if flag == True:
                                client.unsubscribe("/"+mserial) # cancellazione sottoscrizione al topic del macchinario
                                print("unsubscribed")

                                r = requests.delete("http://"+backend_ip+":8080/nearbyHeadphones/delete?serial="+idHeadphones+"&mserial="+mserial) # eliminiamo la vicinanza della cuffia al macchinario dal db

                                if r.status_code != 200:
                                    print("Errore nella richiesta:", r.status_code)



# Funzione per la scansione dei dispositivi Bluetooth       
def scan_ble_devices():
    scanner = Scanner().withDelegate(ScanDelegate())

    print("Scanning for BLE devices... Press Ctrl+C to stop.")

    while True:
        devices = scanner.scan(0.5) 
    

# Attesa infinita per mantenere il programma in esecuzione
try:
    while True:
    	scan_ble_devices()
except KeyboardInterrupt:
    r = requests.delete("http://"+backend_ip+":8080/nearbyHeadphones/delete/"+idHeadphones)

    if r.status_code == 200:
        print("Disconnessione della cuffia riuscita")
        client.disconnect()
    else:
        print("Errore nella richiesta:", r.status_code)


import paho.mqtt.client as mqtt
from bluepy.btle import Scanner, DefaultDelegate
import requests
from getmac import get_mac_address as gma
import sys

''' Leggi gli argomenti dalla linea di comando '''
args = sys.argv

if len(args) < 2:
    print("Usage: python ble_mqtt.py <url>")
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
client.connect("test.mosquitto.org", 1883, 60)

# Loop di rete per gestire le connessioni e i messaggi in entrata
client.loop_start()


'''ID HEADPHONES'''

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

mserial_beacon = {}
mserial_threshold = {}

machinery_flag = {}

for machinery in machineries:

    response = requests.get("http://"+backend_ip+":8080/beacon/find/" + machinery["mserial"])

    if response.status_code == 200:

        beacons = response.json()

        macs = []
        thresholds = []


        for beacon in beacons:
            macs.append(beacon["mac"].lower())
            thresholds.append(beacon["threshold"])

        mserial_beacon[machinery["mserial"]] = macs
        mserial_threshold[machinery["mserial"]] = thresholds
        machinery_flag[machinery["mserial"]] = False
    else:
        print("Errore durante la richiesta GET:", response.status_code)
    
#print(mserial_beacon)
#print(machinery_flag)

client.subscribe("/"+idHeadphones)


'''Scansione bluetooth'''

# Classe per la gestione dei pacchetti Bluetooth ricevuti
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        #global machinery_flag
        if isNewDev or isNewData:
            for mserial, macs in mserial_beacon.items():
                if dev.addr in macs:

                    idx = macs.index(dev.addr)

                    if dev.rssi > -int(mserial_threshold[mserial][idx]) and machinery_flag[mserial] == False:

                        client.subscribe("/"+mserial)

                        print("subribed con threshold ", -(int(mserial_threshold[mserial][idx])))

                        # Esegui la richiesta GET
                        response = requests.get("http://"+backend_ip+":8080/machinery/find/machinery/" + mserial)

                        # Controlla lo stato della risposta
                        if response.status_code == 200:

                            # Decodifica la risposta JSON
                            m = response.json()

                        else:
                            # Stampa un messaggio di errore
                            print("Errore durante la richiesta GET:", response.status_code)


                        payload = {
                            "serial": idHeadphones,
                            "mserial": mserial,
                            "idRoom": m["idRoom"],
                            "idBranch": m["idBranch"]
                        }
                        headers = {'Content-Type': 'application/json'}
                        r = requests.post("http://"+backend_ip+":8080/nearbyHeadphones/add", json=payload, headers=headers)

                        if r.status_code == 200:
                            machinery_flag[mserial] = True
                        else:
                            print("Errore nella richiesta:", r.status_code)
                        
                    elif dev.rssi <= -(int(mserial_threshold[mserial][idx])) and machinery_flag[mserial] == True:

                        client.unsubscribe("/"+mserial)

                        print("unsubscribed")

                        r = requests.delete("http://"+backend_ip+":8080/nearbyHeadphones/delete?serial="+idHeadphones+"&mserial="+mserial)

                        if r.status_code == 200:
                            machinery_flag[mserial] = False
                        else:
                            print("Errore nella richiesta:", r.status_code)



# Funzione per la scansione dei dispositivi Bluetooth       
def scan_ble_devices():
    scanner = Scanner().withDelegate(ScanDelegate())

    print("Scanning for BLE devices... Press Ctrl+C to stop.")

    while True:
        devices = scanner.scan(0.5)  # Scans for 0.5 seconds
    

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


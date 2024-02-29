#import paho.mqtt.client as mqtt
from bluepy.btle import Scanner, DefaultDelegate
import requests
from getmac import get_mac_address as gma

'''ID HEADPHONES'''

idHeadphones = gma()


'''GET di tutti i macchinari'''

# Esegui la richiesta GET
response = requests.get("http://192.168.1.108:8080/machinery/getAll")

# Controlla lo stato della risposta
if response.status_code == 200:

    # Decodifica la risposta JSON
    machineries = response.json()

else:
    # Stampa un messaggio di errore
    print("Errore durante la richiesta GET:", response.status_code)



'''GET dei beacon by mserial'''

mserial_beacon = {}

machinery_flag = {}

for machinery in machineries:

    response = requests.get("http://192.168.1.108:8080/beacon/find/" + machinery["mserial"])

    if response.status_code == 200:

        beacons = response.json()

        macs = []

        for beacon in beacons:
            macs.append(beacon["mac"].lower())

        mserial_beacon[machinery["mserial"]] = macs
        machinery_flag[machinery["mserial"]] = False
    else:
        print("Errore durante la richiesta GET:", response.status_code)
    
print(mserial_beacon)
print(machinery_flag)

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

                    if dev.rssi > -60 and machinery_flag[mserial] == False:

                        # Esegui la richiesta GET
                        response = requests.get("http://192.168.1.108:8080/machinery/find/machinery/" + mserial)

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
                        r = requests.post("http://192.168.1.108:8080/nearbyHeadphones/add", json=payload, headers=headers)

                        if r.status_code == 200:
                            machinery_flag[mserial] = True
                        else:
                            print("Errore nella richiesta:", r.status_code)
                        
                    elif dev.rssi <= -60 and machinery_flag[mserial] == True:
                        payload = {
                            "serial": idHeadphones,
                            "mserial": mserial
                        }
                        headers = {'Content-Type': 'application/json'}
                        r = requests.delete("http://192.168.1.108:8080/nearbyHeadphones/delete", json=payload, headers=headers)

                        if r.status_code == 200:
                            machinery_flag[mserial] = False
                        else:
                            print("Errore nella richiesta:", r.status_code)



# Funzione per la scansione dei dispositivi Bluetooth       
def scan_ble_devices():
    scanner = Scanner().withDelegate(ScanDelegate())

    print("Scanning for BLE devices... Press Ctrl+C to stop.")

    try:
        while True:
            devices = scanner.scan(0.5)  # Scans for 0.5 seconds
    except KeyboardInterrupt:
        print("Scan stopped.")


# Attesa infinita per mantenere il programma in esecuzione
try:
    while True:
    	scan_ble_devices()
except KeyboardInterrupt:
    print("Connessione al broker MQTT chiusa.")



#Quando vicino a un beacon POST sull'api nearbyHeadphones corrispondente
#Quando lontano da un beacon bisogna fare DELETE di nearbyHeadphones

'''

already_subscribed_macchinari_1 = False
already_subscribed_macchinari_2 = False

# Classe per la gestione dei pacchetti Bluetooth ricevuti
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        global already_subscribed_macchinari_1
        global already_subscribed_macchinari_2
        if isNewDev or isNewData:
            if dev.addr == "dd:d1:15:c7:6e:81":
                #print(f'Discovered device: {dev.addr} (RSSI: {dev.rssi})')
                # Subscribe e Unsubscribe dinamico
                if dev.rssi > -60 and already_subscribed_macchinari_1 == False:
                    # Iscrizione al topic "macchinari/1" una volta connessi al broker
                    # print("Subscribed to topic macchinari/1\n")
                    client.subscribe("macchinari/1")
                    already_subscribed_macchinari_1 = True
                elif dev.rssi <= -60 and already_subscribed_macchinari_1 == True:
                    # print("Unsubscribed to topic macchinari/1\n")
                    client.unsubscribe("macchinari/1")
                    already_subscribed_macchinari_1 = False


            if dev.addr == "e8:4a:92:05:c0:ca":
                #print(f'Discovered device: {dev.addr} (RSSI: {dev.rssi})')
                # Subscribe e Unsubscribe dinamico
                if dev.rssi > -50 and already_subscribed_macchinari_2 == False:
                    # Iscrizione al topic "macchinari/2" una volta connessi al broker
                    #print("Subscribed to topic macchinari/2\n")
                    client.subscribe("macchinari/2")
                    already_subscribed_macchinari_2 = True
                elif dev.rssi <= -50 and already_subscribed_macchinari_2 == True:
                    # print("Unsubscribed to topic macchinari/1\n")
                    client.unsubscribe("macchinari/2")
                    already_subscribed_macchinari_2 = False

                

# Funzione per la scansione dei dispositivi Bluetooth       
def scan_ble_devices():
    scanner = Scanner().withDelegate(ScanDelegate())

    print("Scanning for BLE devices... Press Ctrl+C to stop.")

    try:
        while True:
            devices = scanner.scan(0.5)  # Scans for 0.5 seconds
    except KeyboardInterrupt:
        print("Scan stopped.")


#################
#     MQTT      #
#################

# Callback chiamata quando il client si connette al broker
def on_connect(client, userdata, flags, rc):
    print("Connesso al broker con codice risultato: " + str(rc))

# Callback chiamata quando un messaggio viene ricevuto sul topic sottoscritto
def on_message(client, userdata, msg):
    data_e_ora_correnti = datetime.now()
    # Formattare la data e l'ora come una stringa
    stringa_formattata = data_e_ora_correnti.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nTopic {msg.topic}, Messaggio: {str(msg.payload)}, Orario: {stringa_formattata}\n")

# Configurazione del client MQTT
client = mqtt.Client()

# Impostazione delle callback
client.on_connect = on_connect
client.on_message = on_message


# Connessione al broker MQTT
client.connect("test.mosquitto.org", 1883, 60)

# Loop di rete per gestire le connessioni e i messaggi in entrata
client.loop_start()

# Attesa infinita per mantenere il programma in esecuzione
try:
    while True:
    	scan_ble_devices()
except KeyboardInterrupt:
    # Chiusura del client MQTT quando il programma viene interrotto
    client.disconnect()
    print("Connessione al broker MQTT chiusa.")

'''
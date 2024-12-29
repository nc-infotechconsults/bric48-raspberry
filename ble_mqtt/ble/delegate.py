from bluepy.btle import DefaultDelegate

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        print(dev, isNewDev, isNewData)
        # if isNewDev or isNewData:  # se arriva un pacchetto da un nuovo dispositivo o da un dispositivo conosciuto
        #     # per ogni macchinario prendiamo la lista di beacon associati corrispondente
        #     for mserial, macs in mserial_beacon.items():
        #         if dev.addr in macs:  # se il pacchetto bluetooth arrivato viene da un beacon presente nella lista

        #             # salviamo l'indice che ha il beacon nella lista.
        #             idx = macs.index(dev.addr)

        #             # se l'RSSI del pacchetto è sopra la soglia
        #             if dev.rssi > -int(mserial_threshold[mserial][idx]):

        #                 # se il flag di quel beacon è 0 (ossia se non eravamo già nelle vicinanze di quel beacon)
        #                 if mserial_flag[mserial][idx] == 0:

        #                     # impostiamoci come "nei pressi" di quel beacon
        #                     mserial_flag[mserial][idx] = 1

        #                     # questo flag serve per vedere se tutti gli altri flag del macchinario erano a 0. In tal caso infatti significa che
        #                     # non eravamo iscritti al topic di quel macchinario e ci dobbiamo iscrivere
        #                     flag = True
        #                     for i in range(0, len(macs)):
        #                         if i != idx:
        #                             if mserial_flag[mserial][i] == 1:
        #                                 flag = False

        #                     if flag == True:
        #                         # sottoscrizione al topic del macchinario
        #                         client.subscribe("/"+mserial)
        #                         print("subscribed con threshold ", -
        #                               (int(mserial_threshold[mserial][idx])))

        #                         # prendiamo il macchinario di cui stiamo nei paraggi dal db
        #                         response = requests.get(
        #                             "http://"+backend_ip+":8080/machinery/find/machinery/" + mserial)
        #                         if response.status_code == 200:
        #                             m = response.json()
        #                         else:
        #                             print("Errore durante la richiesta GET:",
        #                                   response.status_code)

        #                         # creiamo il payload da aggiungere nel db alla collezione "nearbyHeadphones". Così nel db
        #                         # risulterà che tale cuffia è nei pressi del macchinario
        #                         payload = {
        #                             "serial": idHeadphones,
        #                             "mserial": mserial,
        #                             "idRoom": m["idRoom"],
        #                             "idBranch": m["idBranch"]
        #                         }
        #                         headers = {'Content-Type': 'application/json'}
        #                         r = requests.post(
        #                             "http://"+backend_ip+":8080/nearbyHeadphones/add", json=payload, headers=headers)

        #                         if r.status_code != 200:
        #                             print("Errore nella richiesta:",
        #                                   r.status_code)

        #             # se l'RSSI del pacchetto ricevuto è sotto la soglia
        #             else:

        #                 # se eravamo nei pressi di quel beacon
        #                 if mserial_flag[mserial][idx] == 1:

        #                     # cambiamo il flag a 0 per indicare che ci siamo allontanati da quel beacon
        #                     mserial_flag[mserial][idx] = 0

        #                     # questo flag serve per vedere se tutti gli altri flag del macchinario erano a 0. In tal caso infatti significa che
        #                     # quel beacon era l'unico beacon del macchinario a cui eravamo vicini e siccome ci siamo allontanati possiamo disiscriverci dal topic del macchinario
        #                     flag = True
        #                     for i in range(0, len(macs)):
        #                         if i != idx:
        #                             if mserial_flag[mserial][i] == 1:
        #                                 flag = False

        #                     if flag == True:
        #                         # cancellazione sottoscrizione al topic del macchinario
        #                         client.unsubscribe("/"+mserial)
        #                         print("unsubscribed")

        #                         # eliminiamo la vicinanza della cuffia al macchinario dal db
        #                         r = requests.delete(
        #                             "http://"+backend_ip+":8080/nearbyHeadphones/delete?serial="+idHeadphones+"&mserial="+mserial)

        #                         if r.status_code != 200:
        #                             print("Errore nella richiesta:",
        #                                   r.status_code)

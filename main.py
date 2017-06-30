'''
Bluetooth/Pyjnius example
=========================
This was used to send some bytes to an arduino BLE.
The app must have BLUETOOTH and BLUETOOTH_ADMIN permissions.
Connect your device to your phone, via the bluetooth menu. After the
pairing is done, you'll be able to use it in the app.
'''

import kivy ###on importe la bibliothèque Kivy
kivy.require('1.8.0')

from jnius import PythonJavaClass, java_method ## on importe la bibliothèque Python pour accéder à des classes Java
from jnius import autoclass
from jnius import cast
from kivy.lang import Builder ##framework Kivy
from kivy.app import App
from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
import time
import struct

BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter') ##découverte de périphériques, interroger une liste d'appareils (appairés)
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')###Un BluetoothDevice vous permet de créer une connexion avec l'appareil ou de questionner le nom, l'adresse, la classe et l'état de liaison.
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')##  crée un socket serveur d'écoute. Lorsqu'une connexion est acceptée par le BluetoothServerSocket, il retournera une nouvelle BluetoothSocket pour gérer la connexion.
BluetoothGatt= autoclass('android.bluetooth.BluetoothGatt')##Cette classe fournit des fonctionnalités Bluetooth du GATT pour permettre la communication avec Bluetooth
BluetoothGattCallback = autoclass('android.bluetooth.BluetoothGattCallback')##utilisée pour appeler BluetoothGatt (Cette classe abstraite est utilisée pour implémenter callbacks BluetoothGatt.)
UUID = autoclass('java.util.UUID')##identifiant unique.C'est au niveau de la bande de base que sont définies les adresses matérielles des périphériques (équivalentes à l'adresse MAC d'une carte réseau).
List = autoclass('java.util.List')
Context = autoclass('android.content.Context')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
BluetoothGattService=autoclass('android.bluetooth.BluetoothGattService')
activity = PythonActivity.mActivity
btManager = activity.getSystemService(Context.BLUETOOTH_SERVICE)
Intent = autoclass('android.content.Intent')
BluetoothProfile = autoclass('android.bluetooth.BluetoothProfile')
Service=autoclass('android.app.Service')
etatconnexion=0

class PyBluetoothGattCallback(PythonJavaClass):
    __javainterfaces__ =["org/myapp/BluetoothGattImplem$OnBluetoothGattCallback"]
    __javacontext__ = 'app'

    @java_method('(Landroid/bluetooth/BluetoothGatt;II)V')
    def onConnectionStateChange(self, gatt, status, newstate):
        global etatconnexion
        Logger.info('%s' % newstate)
        etatconnexion=newstate

    @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
    def onServicesDiscovered(self, gatt, status):
        global servicesdiscovered
        Logger.info('%s' % status)
        servicesdiscovered=status#0 si discovered


BluetoothGattImplem = autoclass('org/myapp/BluetoothGattImplem')
pycallback = PyBluetoothGattCallback()
bg = BluetoothGattImplem()
bg.setCallback(pycallback)

def try_connect(name):
    global etatconnexion,servicesdiscovered

    servicesdiscovered=1
    BluetoothAdapter=btManager.getAdapter()

    paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()

    if len(paired_devices)==0: #(Existe-t-il des) peripheriques appaires
        return None, None

    for device in paired_devices:
        if device.getName() == name:
            break

    if device.getName()!=name: #Existe-t-il un peripherique du nom de '????'
        return None, None

    BluetoothGatt=None

    BluetoothGatt = device.connectGatt(Service, 0, bg)

    compteur=0
    while etatconnexion!=2:
        compteur+=1
        time.sleep(0.1)
        if compteur==100:#Delai de connexion depassee
            Logger.info('%s' % "Toto1")
            Logger.info('%s' % etatconnexion)
            return None, None

    BluetoothGatt.discoverServices()#Il faut que ca marche pour recuperer un service

    compteur=0
    while servicesdiscovered!=0:
        compteur+=1
        time.sleep(0.1)
        if compteur==100:#Delai de decouverte des services depasse
            return None, None

    service = BluetoothGatt.getService(UUID.fromString("0000ffe0-0000-1000-8000-00805f9b34fb"))
    try:
        characteristic = service.getCharacteristic(UUID.fromString("0000ffe1-0000-1000-8000-00805F9B34FB"))
    except:
        return None, None

    return BluetoothGatt, characteristic

class BluetoothApp(App):
    def build(self):
        #On cree une disposition pour l'affichage:
        Layout=BoxLayout(orientation='vertical',spacing=20,padding=(200,20))
        self.BoutonConnect=Button(text='Se connecter')
        self.BoutonConnect.bind(on_press=self.connect)
        #On ajoute le bouton dans l'affichage:
        Layout.add_widget(self.BoutonConnect)
        #un textinput pour pouvoir entrer le code:
        self.Input1 = TextInput(text="",font_size=30)
        Layout.add_widget(self.Input1)
        self.BoutonSend=Button(text='Envoyer')
        self.BoutonSend.bind(on_press=self.send)
        #On ajoute le bouton dans l'affichage:
        Layout.add_widget(self.BoutonSend)
        self.gatt=None
        self.charac=None

        return Layout

    def connect(self,instance):
        try:
            BluetoothGatt.disconnect()
        except:
            pass
        instance.background_color=[0,0,1,1]
        instance.text="En attente d'une  connexion"
        self.gatt, self.charac = try_connect('HC-05')
        if self.charac!=None:
            instance.background_color=[0,1,0,1]
            instance.text="Connecté"
        else:
            instance.background_color=[0,1,1,1]
            instance.text="Echec de connexion : Nouvel essai"

    def send(self, cmd):
        global etatconnexion
        if self.charac!=None:
            try :
                nb=int(self.Input1.text)
            except:
                cmd.text="Send : Il faut un nombre !"
                self.Input1.text=""
            if etatconnexion==2:
                for chiffre in self.Input1.text:
                    self.charac.setValue(int(chiffre),17,0)
                    BluetoothGatt.writeCharacteristic(self.charac)
            else:
                self.BoutonConnect.background_color=[1,0,0,1]
                self.BoutonConnect.text="Echec de connexion : Nouvel essai"

if __name__ == '__main__':
    BluetoothApp().run()

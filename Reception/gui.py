from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
import asyncio
from kivy.app import async_runTouchApp
from kivy.uix.label import Label
#from mainNode import AppData
from seatingLot import *
import json
import argparse
from seatingLotFSM import *
from bleStreamer import *
import kivy
import logging

# Set the desired logging level
kivy.logger.Logger.setLevel(logging.INFO)
""" def read_config(filename: str = "ble_configs.json") -> AppData:
    the_config = None
    appdata = AppData()
    with open(filename, "r") as handle:
        the_config = json.load(handle)
    appdata.all_spots = the_config["all_spots"]
    appdata.cost_per_min = the_config["cost_per_min"]
    return appdata """

class MainWindow(Screen):
    totSpaces = NumericProperty(2)
    availableSpaces = NumericProperty(2)
    seat1Available = BooleanProperty(False)
    seat2Available = BooleanProperty(False)
    seat1Updated = StringProperty("Never")
    seat2Updated = StringProperty("Never")
    buttonColorRed = ListProperty([1, .3, .4, .85])
    buttonColorGreen = ListProperty([.3, 1, .4, .85])

    def __init__(self, **kw):
        super().__init__(**kw)
        Clock.schedule_interval(self.set_spaces, 2)
        
    def set_spaces(self, dt):
        app = App.get_running_app()
        if(app):
            spaces = app._seatingLot.get_num_available_spots()
            self.availableSpaces = spaces[0]
            self.totSpaces = spaces[1]
            self.seat1Available = app._seatingLot.get_is_available('Seat_1')
            self.seat2Available = app._seatingLot.get_is_available('Seat_2')
            self.seat1Updated = app._seatingLot.get_last_updated('Seat_1')
            self.seat2Updated = app._seatingLot.get_last_updated('Seat_2')
    

class SeatingWindow(Screen):
    idFail = BooleanProperty(False)
    failReason = StringProperty("")
    seatingSpace = StringProperty(None)
    guestName = StringProperty(None)
    receiptID = StringProperty(None)
    
    def get_spot(self, guest_name):
        if(len(guest_name)==0):
            self.failReason = "Please enter a valid name"
            return False
        
        app = App.get_running_app()
        receipt_id = None
        seating_space = app._seatingLot.get_next_available_spot(guest_name)
        
        if(seating_space==None):
            self.failReason = "A guest with the same name is already seated"
            return False
        
        if(seating_space and guest_name):
            receipt_id = app._seatingLot.seat_entry(guest_name,seating_space)
        
        if(receipt_id==None):
            self.failReason = "Could not generate a receipt"
            return False
        
        self.receiptID = receipt_id
        self.seatingSpace = seating_space
        self.guestName = guest_name       

        ref_to_receipt_screen = self.manager.get_screen("receiptwindow")
        ref_to_receipt_screen.receiptID = receipt_id
        ref_to_receipt_screen.seatingSpace = seating_space
        
        self.failReason = ""
        return True
    
class ReceiptWindow(Screen):
    receiptID = StringProperty(None)
    seatingSpace = StringProperty(None)

class OpenGateWindowEntry(Screen):
    pass

class ExitWindow(Screen):
    seatingCost = NumericProperty(0)
    failReason = StringProperty("")
    
    def get_cost(self, receipt_id):
        if(len(receipt_id)==0):
            self.failReason = "Please enter a valid receipt"
            return False
        app = App.get_running_app()
        seating_cost = app._seatingLot.seat_exit(receipt_id)
        if(seating_cost):
            self.failReason = ""
        else:
            self.failReason = "Plese check your receipt ID"
            return False
        
        self.seatingCost = seating_cost if seating_cost else 0
        ref_to_receipt_screen = self.manager.get_screen("paymentwindow")
        ref_to_receipt_screen.seatingCost = self.seatingCost        
        return True

class PaymentWindow(Screen):
    balance = NumericProperty(0)
    seatingCost = NumericProperty(0)
    failReason = StringProperty("")
    
    def get_balance(self, payment_amount):
        if(len(payment_amount)==0 or (payment_amount.isdigit()==False)):
            self.failReason = "Please enter a valid amount"
            return False
        
        payment_amount = int(payment_amount)
        if(payment_amount<self.seatingCost):
            self.failReason = "The amount you paid is not sufficient"
            return False
        else:
            self.balance = payment_amount - self.seatingCost
            ref_to_receipt_screen = self.manager.get_screen("opengatewindowexit")
            ref_to_receipt_screen.seatingBalance = self.balance    
            return True

class OpenGateWindowExit(Screen):
    seatingBalance = NumericProperty(None)
    pass

class WindowManager(ScreenManager):
    pass

kv = Builder.load_file("my.kv")

class MyMainApp(App):
    def __init__(self,appData,seatingLot, **kw):
        super().__init__(**kw)
        self._appData = appData
        self._seatingLot = seatingLot
        
    def build(self):
        return kv
    

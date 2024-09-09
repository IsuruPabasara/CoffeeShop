"""
Put your code in this file and write some nice documentation.

"""

"""
Service Explorer
----------------

An example showing how to access and print out the services, characteristics and
descriptors of a connected GATT server.

Created on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""
import argparse
import asyncio
import logging
from bleak import BleakClient, BleakScanner, BLEDevice

logger = logging.getLogger(__name__)        
logger.setLevel(logging.INFO)

""" Define the blestreamer as class. """
class BLEStreamer(object):
    def __init__(self, name, seating_lot) -> None:
        self._name = name
        self._seating_lot = seating_lot
            
    async def find_with_name(self) -> BLEDevice:
        """
        Find device by name
        """
        device = await BleakScanner.find_device_by_name(
            self._name, cb=dict(use_bdaddr=False)
        )
        if device is None:
            logger.error("Could not find device with name '%s'", self._name)
        return device

    async def retry_connect(self, conn_timeout: int) -> BLEDevice:
        """
        Retry establishing connection with intervals
        """
        device = None
        tries = 1
        while(True):
            logger.info(f"Connection attempt {tries} for {self._name}...")
            tries = tries+1
            device = await self.find_with_name()
            if device is None:
                self._seating_lot.spot_occupied(self._name)
                await asyncio.sleep(conn_timeout)
            else:
                return device
        #return device
        
    def is_seating_spot_free(self,sender, data):
        """
        Display if seating spot is free. Warmer=not free
        """
        temp_val = int.from_bytes(data,'little')/100
        if(temp_val>29):
            self._seating_lot.spot_occupied(self._name)
            return False
        elif(temp_val<29):
            self._seating_lot.spot_released(self._name)
            return True
     
    def time_handler(self,sender, data):
        """
        Display the pressure
        """
        time_val = int.from_bytes(data,'little')
        self._seating_lot.spot_last_updated(self._name, time_val)

    async def read_service(self, client: BleakClient):
        """
        Read the temperature and pressure
        """
        for service in client.services:
            if(service.handle==16):
                for char in service.characteristics:
                    if "notify" in char.properties:
                        try:
                            if(char.handle==17):
                                await client.start_notify(char.uuid, self.is_seating_spot_free)
                                await asyncio.sleep(3)
                                await client.stop_notify(char.uuid)
                            if(char.handle==20):
                                await client.start_notify(char.uuid, self.time_handler)
                                await asyncio.sleep(3)
                                await client.stop_notify(char.uuid)
                        except Exception as e:
                            logger.error(
                                "  [Characteristic] %s (%s), Error: %s",
                                char,
                                ",".join(char.properties),
                                e,
                            )                


    async def display_char(self, device: BLEDevice):
        """
        Display the characteristics given by teperature and pressure
        """
        timeout_s = 0.2 
        async with BleakClient(
                device,
                services=[],
            ) as client:
                logger.info(f"Connected to {self._name}")
                while(True):
                    if client.is_connected:
                        await self.read_service(client)
                    else:
                        return None
                    await asyncio.sleep(timeout_s)
            

    async def ble_streamer(self):
        device = None
        while(True):
            if device is None:    
                logger.info("starting scan...")
                device = await self.retry_connect(5)
                if device is None:
                    logger.info("Device was not found, aborting scan...")
                    return
            else:
                logger.info("connecting to device...")
                device = await self.display_char(device)
            
async def test_ble(name, seating_lot):
    our_ble = BLEStreamer(name, seating_lot)
    await our_ble.ble_streamer()

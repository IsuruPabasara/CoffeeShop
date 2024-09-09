import time
import uuid
from datetime import timezone 
import datetime 

class SeatingLot(object):
    def __init__(self, all_spots, costpermin) -> None:
        self._current_transaction = {}
        self._costpermin = costpermin
        self._seating_log = {}
        all_spots_det = {}
        for idx in range(len(all_spots)):
            all_spots_det[all_spots[idx]] = {
                "last_updated":"Never",
                "available":False
            }
        self._all_spots_det = all_spots_det
        self._all_spots = all_spots

        """ self._seating_log = {
            "ABC":{
                "1234" : {
                    "entry":1714943947,
                    "exit":None,
                    "payment":None,
                    "space":"A"
                },
                "1233" : {
                    "entry":1714933947,
                    "exit":1714938947,
                    "payment":2,
                    "space":"B"
                }
            },
            "ABD":{
                "1232" : {
                    "entry":1714953947,
                    "exit":1714938947,
                    "payment":None,
                    "space":"B"
                },
                "1231" : {
                    "entry":1714933947,
                    "exit":1714938947,
                    "payment":2,
                    "space":"A"
                }
            }
        }
        """

    def get_next_available_spot(self, guest_name:str) -> str:
        """
        Returns the next spot available for seating
        """
        seating_history = self._seating_log.get(guest_name)
        if(seating_history!=None):
            for value in seating_history.values():
                if(value['exit']==None):
                    return None
                
        for spot,details in self._all_spots_det.items():
            if(details['available']):
                return str(spot)  
        return None
        

    def get_num_available_spots(self) -> tuple:
        """
        Returns count of seating spots
        """
        all_spots_count = 0
        available_spots_count = 0
        print(self._all_spots_det)
        for details in (self._all_spots_det).values():
            all_spots_count=all_spots_count+1
            if(details['available']):
                available_spots_count = available_spots_count + 1
        return [available_spots_count,all_spots_count]
    

    def seat_entry(self, guest_name: str, seating_space:str) -> str:
        """
        Logs a guest_name entering the seat
        Returns the recipt id
        """
        dt = datetime.datetime.now(timezone.utc) 
        utc_time = dt.replace(tzinfo=timezone.utc) 
        utc_timestamp_entry = round(utc_time.timestamp()) 

        receipt_id = str(uuid.uuid1())[:5] 
        self._seating_log.setdefault(guest_name,{})
        self._seating_log[guest_name][receipt_id] = {
            "entry":utc_timestamp_entry,
            "exit":None,
            "payment":None,
            "space":seating_space
        }
        return receipt_id
    

    def seat_exit(self, receipt_id:str) -> float:
        """
        Logs a guest_name exiting the seat
        Returns the payment amount
        """
        guest_name = None
        for guest_nameid,receipts in self._seating_log.items():
            if(receipts.get(receipt_id)!=None):
                guest_name = guest_nameid

        if(guest_name==None):
            return None        

        dt = datetime.datetime.now(timezone.utc) 
        utc_time = dt.replace(tzinfo=timezone.utc) 
        utc_timestamp_exit = round(utc_time.timestamp()) 
        utc_timestamp_entry = self._seating_log[guest_name][receipt_id]["entry"]
        seat_cost = self.payment_calc(utc_timestamp_entry,utc_timestamp_exit)
        
        self._seating_log[guest_name][receipt_id]["exit"] = utc_timestamp_exit
        self._seating_log[guest_name][receipt_id]["payment"] = seat_cost
        return seat_cost

    def payment_calc(self, entry_time: int, exit_time:int) -> float:
        cost = (exit_time - entry_time)*self._costpermin
        return cost
    
    def spot_occupied(self, seating_space:str)-> bool:
        print(f"called occupied by {seating_space}")
        self._all_spots_det[seating_space]['available'] = False
        
    def spot_released(self, seating_space:str)-> bool:
        print(f"called released by {seating_space}")
        self._all_spots_det[seating_space]['available'] = True

    def spot_last_updated(self, seating_space:str, last_updated:int)-> bool:
        dt_object = datetime.datetime.fromtimestamp(last_updated)

        print("Date and Time:", dt_object)

        formatted_date_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        print("Formatted Date and Time:", formatted_date_time)
        self._all_spots_det[seating_space]['last_updated'] = formatted_date_time

    def get_last_updated(self, seating_space:str)-> str:
        if(self._all_spots_det[seating_space]['last_updated']):
            return self._all_spots_det[seating_space]['last_updated']
        return "Never"

    def get_is_available(self, seating_space:str)-> bool:
        return self._all_spots_det[seating_space]['available']

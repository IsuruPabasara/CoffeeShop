from loguru import logger
import transitions
from transitions.extensions.asyncio import AsyncMachine, AsyncTimeout
import asyncio

async def ainput(prompt: str = ""):
    return await asyncio.to_thread(input, prompt)

""" Define the async seating lot FSM. """
class SeatingLotFSM(AsyncMachine):
    def __init__(self, seating_lot) -> None:
        self._seating_lot = seating_lot
        self._is_gate_locked = True
        self._states = ['welcome', 'entry_screen','exit_screen','open_gate']
        super().__init__(
            self, states=self._states, send_event=True, queued=True
        )
        self._add_transitions()

    def _add_transitions(self) -> None:
        self.add_transition(trigger="tr_bootup", source="initial", dest="welcome", after="run_welcome")
        self.add_transition(trigger="tr_press_enter", source="welcome", dest="entry_screen", after="run_entry_screen")
        self.add_transition(trigger="tr_valid_veh", source="entry_screen", dest="open_gate", after="run_open_gate")
        self.add_transition(trigger="tr_invalid_veh", source="entry_screen", dest="welcome", after="run_welcome")
        self.add_transition(trigger="tr_close_gate", source="open_gate", dest="welcome", after="run_welcome")        
        self.add_transition(trigger="tr_press_exit", source="welcome", dest="exit_screen", after="run_exit_screen")
        self.add_transition(trigger="tr_id_fail", source="exit_screen", dest="exit_screen", after="run_exit_screen")
        self.add_transition(trigger="tr_payment_pass", source="exit_screen", dest="open_gate", after="run_open_gate")
        self.add_transition(trigger="tr_payment_fail", source="exit_screen", dest="welcome", after="run_entry_screen")
        
    async def run_welcome(self, event: transitions.EventData) -> None:
        """
        This is the default display on the seating gate.
        Will notify how many spaces are available.
        """
        while True:
            self._is_gate_locked = True
            [available_spots,all_spots] = self._seating_lot.get_num_available_spots()
            logger.info("Welcome to the seating lot!")
            logger.info(f"Our current ocupancy is {all_spots-available_spots} out of {all_spots}")
            seat_or_exit = await ainput("Seating(P) or Exit(E)?")
            
            if(seat_or_exit!=None):
                if(seat_or_exit == "P"):
                    if(available_spots>0):
                        return await self.dispatch("tr_press_enter")
                    else:
                        logger.info("Sorry all seating spots are occupied")
                    
                elif(seat_or_exit == "E"):
                    return await self.dispatch("tr_press_exit")
                else:
                    logger.info("Wrong input")
    
    async def run_entry_screen(self, event: transitions.EventData) -> None:
        """
        This is the display on the seating gate when entering.
        Will notify where to seat.
        """
        self._is_gate_locked = True
        guest_name = await ainput("What is your name?")
        seating_spot = self._seating_lot.get_next_available_spot(guest_name)
        if(seating_spot==None):
            logger.info("A guest with the same name is already seated")
            return await self.dispatch("tr_invalid_veh")

        logger.info(f"The seating spot assigned to you {guest_name} is {seating_spot}")
        receipt_id = self._seating_lot.seat_entry(guest_name,seating_spot)
        logger.info(f"Your receipt id is {receipt_id}")
        logger.info("Send signal to Zephyr to light up")
        return await self.dispatch("tr_valid_veh")
        
    async def run_open_gate(self, event: transitions.EventData) -> None:
        """
        The gate is open.
        """
        self._is_gate_locked = False
        logger.info("Gate is open")
        _ = input(">>> Press enter after going through the gate... ")
        logger.info("Gate is closed")
        return await self.dispatch("tr_close_gate")   
        
    async def run_exit_screen(self, event: transitions.EventData) -> None:
        """
        This is the display on the seating gate when exiting.
        Will notify where to seat.
        """
        self._is_gate_locked = True
        receipt_id = await ainput("What is your receipt number?")
        payment_cost = self._seating_lot.seat_exit(receipt_id)

        if(payment_cost == None):
            logger.info("Invalid receipt number")
            return await self.dispatch("tr_id_fail")

        logger.info(f"Your cost of stay is {payment_cost}")
        while True:
            cash = await ainput("Insert cash : $")
            if(cash and int(cash)>=payment_cost):
                logger.info(f"Your change is : ${int(cash)-payment_cost}")
                return await self.dispatch("tr_payment_pass")
            else:
                logger.info("not enough cash")

async def test_fsm(seating_lot):
    our_fsm = SeatingLotFSM(seating_lot)
    print("hello, attempting to boot up the FSM...")
    await our_fsm.dispatch("tr_bootup")
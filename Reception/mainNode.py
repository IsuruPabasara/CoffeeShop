import asyncio
import json
from seatingLot import *
from seatingLotFSM import *
from bleStreamer import *
from gui import MyMainApp

class AppData(object):
    cost_per_min = 0
    seating_spaces = []

def read_config(filename: str = "ble_configs.json") -> AppData:
    the_config = None
    appdata = AppData()
    with open(filename, "r") as handle:
        the_config = json.load(handle)
    appdata.all_spots = the_config["all_spots"]
    appdata.cost_per_min = the_config["cost_per_min"]
    return appdata

async def main(appdata,seating_lot):
    task_list = []
    for idx in range(len(appdata.all_spots)):
        log_level = logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
        )
        task_list.append(asyncio.create_task(test_ble(appdata.all_spots[idx],seating_lot)))

    logging.info("Main started")
    logging.info(f'Current registered tasks: {len(asyncio.all_tasks())}')
    task_fsm = asyncio.create_task(test_fsm(seating_lot))
    await MyMainApp(appdata,seating_lot).async_run()
    await task_fsm
    for idx in range(len(task_list)):
        await task_list[idx]    
    logging.info("Main Ended")

if __name__ == '__main__':
    appdata = read_config() 
    seating_lot = SeatingLot(all_spots=appdata.all_spots, costpermin=appdata.cost_per_min)
    asyncio.run(main(appdata,seating_lot,)) # creats an envent loop

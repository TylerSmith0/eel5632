## Python-specific imports
import asyncio
import logging

###################################################################
## Custom imports
from models import Sensor

async def verify_parameters(data):
    """Verifies that the provided data is enough to create an
        instance of a new Sensor() object and returns that Sensor
        object and a status indicator."""
    
    ## Init vars
    ok = True
    sensor = {}
    
    ## Loop through data keys and compare to requirements
    reqs = {"id": False, "type": False, "spot": False}
    for k in data:
        if k in reqs and (data[k] is not None):
            reqs[k] = True

    ## Ensure reqs is all True:
    for k in reqs:
        if not reqs[k]:
            ok = False
            resp = {"error": f"Invalid sensor init -- missing {k}"}
            logging.info(f"UTIL > {resp['error']}")
            break

    return ok

async def add_sensor_to_rtdb(sensor, db):
    """Adds the Sensor provided to the RTDB and includes its key
        in the keys db of SQLite and MySQL auth"""

    _err = False

    ## Confirm ID is not already in RTDB and insert
    if db.reference(f'sensors/{sensor["id"]}').get() is None:
        db.reference(f'sensors/{sensor["id"]}').set(sensor)
        logging.info(f'UTIL > Added {sensor["id"]} to RTDB.')

        ## TO DO: Add Auth key to data structure
        
        return (_err, db.reference(f'sensors/{sensor["id"]}').get())
    
    ## Otherwise, return an error code and error out
    _err = True
    return (_err, {'error': f'{sensor["id"]} already exists in RTDB.'})



async def add_spot_to_rtdb(spot, db):
    """Adds the Spot provided to the RTDB"""

    _err = False

    data = {
        'id': spot,
        'free': 'true',
        'sensors': {"spot": spot},
    }

    ## Confirm ID is not already in RTDB and insert
    if db.reference(f'spots/{spot}').get() is None:
        print("Confirmed spot doesn't exists")
        print(f"setting {spot} to {data}")
        try:
            db.reference(f'spots/{spot}').set(data)
        except Exception as e:
            print(e)
        print("all done!")
        logging.info(f'UTIL > Added {spot} to RTDB.')        
        return (_err, db.reference(f'spots/{spot}').get())
    
    ## Otherwise, return an error code and error out
    _err = True
    return (_err, {'error': f'{spot} already exists in RTDB.'})


## Authenticate with a given id
async def auth_id(id, key):
    """Authenticates a given key to the applicable ID provided."""

    ## No key provided, error out:
    if key is None:
        return False


    ## TODO: Set up Auth structure and confirm it contains the key

    ## Temporarily assign this as True
    return True


async def exists(domain="sensors", id=None, db=None):
    """Returns True if a given sensor ID exists in the provided DB, otherwise False."""

    ## If ID is none, error out:
    if id is None:
        return False

    ## If db is none, error out:
    if db is None:
        return False

    ## Make query to RTDB
    if db.reference(f'{domain}/{id}').get() is None:
        return False

    return True
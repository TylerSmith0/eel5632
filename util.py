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
    error = False
    sensor = {}
    
    ## Loop through data keys and compare to requirements
    reqs = {"id": False, "type": False}
    for k in data:
        if k in reqs and (data[k] is not None and
                             data[k] != ""):
            sensor[k] = data[k]
            reqs[k] = True

    ## Ensure reqs is all True:
    for k in reqs:
        if not reqs[k]:
            error = True
            resp = {"error": f"Invalid sensor init -- missing {k}"}
            logging.info(f"UTIL > {resp['error']}")
            break

    ## If all checks pass, return sensor info
    if not error:
        resp = sensor

    return error, resp

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


## May not need this function...
async def update_info(id):
    """Returns an updated Sensor object with live data from
        Firebase RTDB."""

    ## TO DO: Create link to RTDB and error-check for valid ID
    return Sensor()


## Authenticate with a given id
async def auth_id(id, key):
    """Authenticates a given key to the applicable ID provided."""

    ## TO DO: Set up Auth structure and confirm it contains the key

    ## Temporarily assign this as True
    return True


async def exists(id, db):
    """Returns True if a given ID exists in the provided DB, otherwise False."""

    ## Make query to RTDB
    if db.reference(f'sensors/{id}').get() is None:
        return False

    return True
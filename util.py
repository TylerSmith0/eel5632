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
        if "key" in sensor:
            del sensor["key"]
        db.reference(f'sensors/{sensor["id"]}').set(sensor)
        logging.info(f'UTIL > Added {sensor["id"]} to RTDB.')

        ## TODO: Update parking spot, if existing, to include this sensor
        if "spot" in sensor:
            print("updating sensor spot")
            await update_sensor_spot(sensor, sensor["id"], db)

        ## TODO: Add Auth key to data structure
        
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
        try:
            db.reference(f'spots/{spot}').set(data)
        except Exception as e:
            print(e)
            return (True, {'error': 'Error when adding new spot to RTDB.'})
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


async def update_sensor_spot(data, id, db):
    print("in func")
    ## Confirm sensor ID exists
    if not (await exists("sensors", id, db)):
        return {"error": "Sensor ID does not exist."}
    print("past 1")
    ## Check for Auth Key in obj:
    if "key" not in data:
        return {"error": "No auth key provided in JSON object."}
    print("past 2")
    ## Confirm auth key:
    if not (await auth_id(id, data["key"])):
        return {"error": "Improper authentication key was provided for given sensor."}
    print("past 3")
    ## Confirm spot is provided in data:
    if "spot" not in data:
        return {"error": "No spot provided in JSON object."}
    print("past 4")
    spot = data["spot"]
    _err = False
    ## Confirm spot exists, if not make one
    if not (await exists("spots", spot, db)):
        print("Adding to rtdb")
        _err, spot = await add_spot_to_rtdb(spot, db)
    else:
        print("spot exists")
        spot = db.reference(f"spots/{spot}").get()
        print(spot)

    if _err:
        return {"error": "Error getting spot data. Please confirm it exists in RTDB."}
    print("past 5")
    ## Add sensor ID to sensors object in spot
    spot['sensors'][id] = id
    print(spot)
    ## Reference sensor object:
    sensor = db.reference(f"sensors/{id}").get()
    print(sensor)
    ## Unlink current spot, if applicable
    oldSpot = sensor["spot"]
    print(oldSpot)
    if (await exists("spots", oldSpot, db)):
        print("old spot exists, ulinking:")
        oldSpotObj = db.reference(f"spots/{oldSpot}").get()
        del oldSpotObj["sensors"][id]
        db.reference(f"spots/{oldSpot}").set(oldSpotObj)

    sensor["spot"] = spot["id"] # Set spot id to sensor's spot parameter
    print(sensor)
    ## remove auth key if exists
    if "key" in sensor:
        print("deleting key")
        del sensor["key"]

    ## setting:
    print("setting these puppies")
    print(sensor)
    print(spot)
    db.reference(f"sensors/{id}").set(sensor)
    db.reference(f"spots/{spot['id']}").set(spot)
    return sensor
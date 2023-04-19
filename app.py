## Python-specific imports
import os
import asyncio
import sqlite3
import util
import logging
import urllib.parse
import urllib.request
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
## Flask imports
from flask import Flask, render_template, request, json

# Firebase admin imports
import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import db
###################################################################
## Custom imports
from models import Sensor

###################################################################
load_dotenv()
logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s  |  %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

app = Flask(__name__)

###################################################################
## Load in configuration files and environment variables and set 
## up logging for the app.

cred = credentials.Certificate(os.environ.get("FIREBASE_AUTH_LOC"))
fb = firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ.get("FIREBASE_URL"),
})


## Occupancy Values for different types of sensors:

occ = {
    "ultrasonic": ["True", "true", 1, True],
     "us": ["True", "true", 1, True], 
     "usonic": ["True", "true", 1, True], 
     "US": ["True", "true", 1, True],
}


###################################################################
## Initialization routine run on startup 
@app.before_first_request
async def startup():
    """Initialize the SQLite database that queries a static MySQL database
        for hashed sensor keys. Provides a base-level authentication for 
        sensors being added to the system, and attempts to mitigate a
        malicious node spoofing the parking sensor's data."""

    logging.info("Starting up app...")

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=monitor_spots, trigger="interval", seconds=10)
    scheduler.start()
    # with sqlite3.connect("database.db") as con:
    #     cur = con.cursor()
    #     with open('schema.sql') as f:
    #         cur.executescript(f.read())
    #         logging.info("Returning from SQL Schema setup.")



def monitor_spots():
    """Iterates through every parking spot in the RTDB and updates the spot's free value
        based on the status of its dependent sensors."""

    try:
        spots = db.reference(f"/spots").get()
        print(spots)
        for spot in spots:
            print(f"Checking {spot}")
            flag = False
            ## Check all of the sensor values
            for sensor in spots[spot]["sensors"]:
                print(f"Sensor is {sensor}")
                ## Skip if it's referring to itself
                if sensor == "spot":
                    continue

                ## Check if sensor value matches the global OCCUPIED state
                try:
                    s = db.reference(f"/sensors/{sensor}").get()
                    # print(f"Returned sensors is {s}")
                    # print(occ)
                    if s["type"] in occ:
                        occ_state = occ[s["type"]]
                    else:
                        # print("not in occ")
                        continue
                except Exception as e:
                    logging.info(f"{e} | APP > MONITOR_SPOTS | Invalid sensor type for occupancy array.")
                    ## sensor["free"] = False  ## Don't do anything!
                    continue

                # print(spots[spot]["sensors"][sensor]["value"])
                # print(occ_state)
                # print(s["value"])
                # print(occ_state)
                if s["value"] in occ_state:
                    ## Change spot to occupied and continue to next spot
                    spots[spot]["free"] = False
                    # print("Updating to FALSE")
                    try:
                        db.reference(f"/spots/{spot}").set(spots[spot])
                        flag = True
                    except Exception as e:
                        logging.error(f"{e} | APP > MONITOR_SPOTS | Unable to set parking spot to False value.")
                        ## sensor["free"] = False  ## Don't do anything!
                    break
            
            ## If we get here, we can make it true! (If it's not already)
            if not flag and not spots[spot]["free"]:
                ## Change spot to UNoccupied
                spots[spot]["free"] = True
                try:
                    db.reference(f"/spots/{spots[spot]['id']}").set(spots[spot])
                except Exception as e:
                    logging.error(f"{e} | APP > MONITOR_SPOTS | Unable to set parking spot to False value.")



    except Exception as e:
        logging.error(f"{e} | APP > MONITOR_SPOTS | Unable to run scheduled function.")
    
###################################################################
## Home Page view
@app.route("/")
async def home():
    """Returns the homepage of the EEL5632 website in HTML."""

    return render_template('home.html')

###################################################################
## Team Page view 
@app.route("/team")
async def team():
    """Returns a brief info page on the HEDGEhogs team in HTML."""
    return render_template('team.html')

###################################################################
## Data Page view
@app.route("/data")
@app.route("/data/")
async def data():
    """Returns a tutorial of how to use the API in HTML."""

    return render_template('data.html')

###################################################################
## Data View Page Home
@app.route("/data/sensor")
@app.route("/data/sensor/")
@app.route("/data/sensor/view")
@app.route("/data/sensor/view/")
async def sensor_data_view_home():
    ## Query for list of sensors:
    sensors = db.reference('sensors').get()
    
    ## Create empty list if none exists
    if sensors is None:
        sensors = {}

    return render_template('sensor_data_home.html', sensors=sensors)

###################################################################
## Data View Page (Human-readable version)
@app.route("/data/sensor/view/<id>", methods=["GET"])
async def sensor_data_view(id=None):
    """Returns the Human-Readable webpage in HTML for a sensor from
        a given sensor id."""

    ## Check if sensor exists:
    data = db.reference(f"sensors/{id}").get()
    if data is None:
        data = {'error': 'Sensor ID does not exist in RTDB.'}
        return render_template('sensor_data_nonexist.html')

    return render_template('sensor_data.html', sensor=data)


## Returns JSON-only object, intended mainly for mobile app.
@app.route("/data/sensor/<id>", methods=["GET", "POST"])
async def sensor_data(id=None):
    if id is None:
        logging.warning("")
        return {'error': 'No ID provided.'}

    if request.method == "GET":

        ## Return the sensor data from the given ID
        data = db.reference(f"sensors/{id}").get()
        if data is None:
            data = {'error': 'Sensor ID does not exist in RTDB.'}
        return data

    elif request.method == "POST":
        # Get values from POST body:
        if request.is_json:# is None:
            data = request.get_json()
        else:
            try:
                data = request.get_data()
                if type(data) is bytes:
                    data = data.decode('utf8')
                if "&" in data:
                    keys = data.split("&")
                    data = {}
                    for k in keys:
                        d = k.split("=")
                        data[d[0]] = d[1]
                else:
                    data = eval(data)
            except Exception as e:
                logging.warning("APP > SENSOR_DATA | Invalid data type " + 
                    "provided on JSON read.")
                data = {"error": "Invalid data type provided. Please ensure " + \
                        "you're setting data type in body to JSON."}
                return data
        
        # First, we authenticate
        for key in data:
            if key == "key":
                ## Attempt to create ID (will error out otherwise):
                if not (await util.exists("sensors", id, db)):
                    ## Confirm all parameters are present:
                    if (await util.verify_parameters(data)):
                        ## Add sensor to the RTDB:
                        _err, data = await util.add_sensor_to_rtdb(data, db)
                        ## Remove auth key from response
                        if "key" in data:
                            del data["key"]
                        return data
                    else:
                        return {'error': 'Invalid parameters provided in JSON object.'}

                ## Confirm authentication
                if (await util.auth_id(id, data[key])):
                    
                    ## Get current item:
                    currData = db.reference(f"sensors/{id}").get()
                    
                    ## Compare current spot to new spot, if exists:
                    if "spot" in data:
                        if data["spot"] != currData["spot"]:
                            resp = await util.update_sensor_spot(data, id, db)
                            if "error" in resp:
                                return resp["error"]

                    ## Remove auth key from data
                    if "key" in data:
                        del data["key"]

                    ## Add to existing object, appending whatever is missing:
                    for i in currData:
                        if i not in data:
                            data[i] = currData[i]

                    ## Update DB value
                    db.reference(f'sensors/{id}').set(data)
                    data['updated'] = 'true'
                    return data

        # Read the data at the posts reference (this is a blocking operation)
        return {'error': 'No Authentication key was provided to update the sensor values.'}

    ## Otherwise wrong HTTP request
    return {'error': 'Invalid HTTP Request -- must use either GET or POST.'}


###################################################################
## Get and Set Parking Spot for a Sensor
@app.route("/data/sensor/<id>/spot", methods=["GET", "POST"])
async def sensor_spot(id=None):
    ## Error-check for None types
    if id is None:
        return {"error": "None-type provided for sensor ID"}

    if request.method == 'GET':
        ## Confirm sensor exists:
        if (await util.exists("sensors", id, db)):
            try:
                ## Query for spot in sensor object:
                spot = db.reference(f"sensors/{id}").get()["spot"]
            except Exception as e:
                logging.warning("APP > SENSOR_SPOT | Sensor spot key does not exist")
                return {"error": "Sensor spot key does not exist in RTDB."}
            
            ## Return spot:
            spot = db.reference(f"spots/{spot}").get()
            if spot is None:
                spot = {"error": "Spot does not exist or is not configured."}
            return spot

        ## Sensor does not exist    
        return {"error": "Sensor id does not exist."}

    # Get values from POST body:
    elif request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            data = request.get_json()
        else:
            try:
                data = json.loads(request.data)
            except Exception as e:
                logging.warning("APP > SENSOR_DATA | Invalid data type " + 
                    "provided on JSON read.")
                data = {"error": "Invalid data type provided. Please ensure" + \
                        "you're setting data type in body to JSON."}
                return data
        
        return await util.update_sensor_spot(data, id, db)





###################################################################
## Data View Page (Human-readable version)
@app.route("/data/sensor/init/<id>", methods=["POST"])
async def init(id=None):
    """Initialize a new sensor with the service. Must provide an Auth key and
        a unique Sensor ID. All other parameters are not required.
        
        Returns JSON object created in Firebase RTDB."""
    
    ## Check request type and process input:
    if request.method == "POST":
        ## Get values from POST body:
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            data = request.get_json()
        else:
            try:
                data = json.loads(request.data)
            except Exception as e:
                print(f"{e} || Exception while processing json from request.data")
                return {}

        ## Confirm that values from POST body are valid:
        _ok = await util.verify_parameters(data)
        if not _ok:
            ## Error out and return error msg in JSON object
            return {'error': 'Invalid parameters provided.'}

        ## Create Sensor object in RTDB and add to keys
        _err, s = await util.add_sensor_to_rtdb(data, db)

        ## If error occurs, return the error message as a JSON obj
        if _err:
            logging.warning(f"APP > {s['error']}")
            return s

        ## Otherwise, return the newly created object
        s["url"] = os.environ.get("FIREBASE_URL")+f"sensors/{s['id']}"
        return s



###################################################################
## Spot Home View Page (Human-readable version)
@app.route("/data/spot")
@app.route("/data/spot/")
@app.route("/data/spot/view")
@app.route("/data/spot/view/")
async def spots_view():
    """Returns a comprehensive list of all spots in the RTDB."""

    spots = db.reference("spots").get()

    return render_template("spots_view.html", spots=spots)



###################################################################
## Spot JSON Object Return
@app.route("/data/spot/<id>")
async def spot_obj(id=None):
    """Returns JSON object of spot information."""
    if id is None:
        spot = {}

    if (await util.exists("spots", id, db)):    
        spot = db.reference(f"/spots/{id}").get()
    else:
        spot = {}

    return spot



###################################################################
## Spot JSON Object Return
@app.route("/data/spot/<id>/free")
async def spot_free(id=None):
    """Returns True or False if spot is available."""
    if id is None:
        free = False

    if (await util.exists("spots", id, db)):
        try:  
            spot = db.reference(f"/spots/{id}").get()
            free = spot["free"]
        except Exception as e:
            logging.warn(f"{e} | APP > SPOT_OBJ | Error getting Spot object from Firebase.")
            free = False
    else:
        free = False

    return free



###################################################################
## Spots JSON List Return
@app.route("/data/spots")
@app.route("/data/spots/")
async def spots_avail():
    """Returns True or False if spot is available."""

    try:  
        spots = db.reference(f"/spots").get()
    except Exception as e:
        logging.warn(f"{e} | APP > SPOT_OBJ | Error getting Spots list from Firebase.")
        spots = {}

    return spots



###################################################################
## Spot View Page (Human-readable version)
@app.route("/data/spot/view/<id>")
async def spot_view(id=None):
    """Returns human-readable version of a given spot's information"""
    if id is None:
        spot = {}

    if (await util.exists("spots", id, db)):    
        spot = db.reference(f"/spots/{id}").get()
    else:
        spot = {}

    return render_template('spot_view.html', spot=spot)



##################################################
## Plates list
##
@app.route("/data/plates")
@app.route("/data/plates/")
async def plates():
    """Returns a list of the plates that are currently in the RTDB."""

    try:
        plates = db.reference(f"/plates").get()
    except Exception as e:
        logging.warn(f"{e} | APP > PLATES | Error getting Plates list from Firebase.")
        plates = {}
    return plates



##################################################
## Plates list
##
@app.route("/data/plates/<id>", methods=["GET", "POST", "DELETE"])
async def plates_getset(id=None):
    """Adds or removes a plate to/from the RTDB."""
    if id is None:
        return {"error": "None id type provided."}

    if request.method == "POST":

        # Get values from POST body:
        if request.is_json:# is None:
            data = request.get_json()
        else:
            try:
                data = request.get_data()
                if type(data) is bytes:
                    data = data.decode('utf8')
                if "&" in data:
                    keys = data.split("&")
                    data = {}
                    for k in keys:
                        d = k.split("=")
                        data[d[0]] = d[1]
                else:
                    data = eval(data)
            except Exception as e:
                logging.warning("APP > SENSOR_DATA | Invalid data type " + 
                    "provided on JSON read.")
                data = {"error": "Invalid data type provided. Please ensure " + \
                        "you're setting data type in body to JSON."}
                return data

        ## Adding a plate:
        try:
            if (await util.exists("plates", id, db)):
                return {"error": "Plate already exists in RTDB."}
            
            plates = db.reference(f"/plates/{id}").set(data)
        except Exception as e:
            logging.warn(f"{e} | APP > PLATES | Error getting Plates list from Firebase.")
            plates = {}
        return data

    elif request.method == "DELETE":
        try:
            if (await util.exists("plates", id, db)):
                db.reference(f"/plates/{id}").delete()
                return {"status": f"{id} deleted from RTDB."}
        except Exception as e:
            logging.warn(f"{e} | APP > PLATES | Error deleting {id} from RTDB.")
        return {"error": "An unspecified error occurred while trying to delete a license plate."}

    return {"error": "Unspecified request type -- Plates only takes POST and DELETE requests."}



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
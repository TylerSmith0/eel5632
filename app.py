## Python-specific imports
import os
import asyncio
import sqlite3
import util
import logging
from dotenv import load_dotenv

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
logging.basicConfig(filename=os.environ.get("LOGGING_FILE_LOC_APP"),
                    filemode='a',
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


###################################################################
## Initialization routine run on startup 
@app.before_first_request
async def startup():
    """Initialize the SQLite database that queries a static MySQL database
        for hashed sensor keys. Provides a base-level authentication for 
        sensors being added to the system, and attempts to mitigate a
        malicious node spoofing the parking sensor's data."""

    logging.info("Starting up app...")

    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        with open('schema.sql') as f:
            cur.executescript(f.read())
            logging.info("Returning from SQL Schema setup.")

    
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
@app.route("/data/view")
@app.route("/data/view/")
async def sensor_data_view_home():
    sensors = db.reference('sensors').get()
    
    if sensors is None:
        sensors = {}
    
    # try:
    #     data = {}
    #     for sensor in sensors:
    #         data[sensor] = request.path + f'/{sensor}'
    # except Exception as e:
    #     logging.warning("APP > SENSOR_DATA_VIEW_HOME | Error" +
    #         " processing sensors from returned structure.")

    return render_template('sensor_data_home.html', sensors=sensors)

###################################################################
## Data View Page (Human-readable version)
@app.route("/data/view/<id>", methods=["GET"])
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
@app.route("/data/<id>", methods=["GET", "POST"])
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
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            data = request.get_json()
        else:
            try:
                data = json.loads(request.data)
            except Exception as e:
                logging.warning("APP > SENSOR_DATA | Invalid data type " + 
                    "provided on JSON read.")
                data = {"error": "Invalid data type provided. Please ensure' + \
                        you're setting data type in body to JSON."}
                return data
        
        # First, we authenticate
        for key in data:
            if key == "key":

                ## Attempt to create ID (will error out otherwise):
                if not (await util.exists(id, db)):
                    if (await util.verify_parameters(data)):
                        await util.add_sensor_to_rtdb(data, db)
                    else:
                        return {'error': 'Invalid parameters provided in JSON object.'}

                ## Confirm auth
                if (await util.auth_id(id, data[key])):

                    ## Remove auth key from data:
                    vals = {}
                    for i in data:
                        if i != "key":
                            vals[i] = data[i]
                        
                    ## Update DB value
                    db.reference(f'sensors/{id}').set(vals)
                    vals['updated'] = 'true'
                    return vals

        # Read the data at the posts reference (this is a blocking operation)
        return {'error': 'No Authentication key was provided to update the sensor values.'}

    ## Otherwise wrong HTTP request
    return {'error': 'Invalid HTTP Request -- must use either GET or POST.'}


###################################################################
## Data View Page (Human-readable version)
@app.route("/init/<id>", methods=["POST"])
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
        _err, s = await util.verify_parameters(data)
        if _err:
            ## Error out and return error msg in JSON object
            return s

        ## Create Sensor object in RTDB and add to keys
        _err, s = await util.add_sensor_to_rtdb(s, db)

        ## If error occurs, return the error message as a JSON obj
        if _err:
            logging.info(f"APP > {s['error']}")
            return s

        ## Otherwise, return the newly created object
        s["url"] = os.environ.get("FIREBASE_URL")+f"sensors/{s['id']}"
        return s


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
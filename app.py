## Python-specific imports
import os
import asyncio
import sqlite3
import util
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

app = Flask(__name__)

###################################################################
## Load in configuration files and environment variables.
load_dotenv()
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

    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        with open('schema.sql') as f:
            cur.executescript(f.read())

    
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
## Data View Page (Human-readable version)
@app.route("/data/view/<id>", methods=["GET"])
def sensor_data_view(id=None):
    """Returns the Human-Readable webpage in HTML for a sensor from
        a given sensor id."""

    ## TO DO: Get the Sensor() object and return its information

    sensor = {
        'id': id,
        'name': "My Name"
    }
    return render_template('sensor_data.html', sensor=sensor)


## Returns JSON-only object, intended mainly for mobile app.
@app.route("/data/<id>", methods=["GET", "POST"])
async def sensor_data(id=None):
    if id is None:
        return {}

    if request.method == "GET":

        ## Return the sensor data from the given ID
        return id

    elif request.method == "POST":
        # Get values from POST body:
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            data = request.get_json()
        else:
            try:
                data = json.loads(request.data)
            except Exception as e:
                data = {"error": "Invalid data type provided. Please ensure' + \
                        you're setting data type in body to JSON."}
        
        # First, we authenticate
        for key in data:
            if key == "key":
                # flag = await attempt_auth()
                print("true")


        # If we pass auth, then update values
        # Get a database reference to our posts
        ref = db.reference('sensors')

# Read the data at the posts reference (this is a blocking operation)
        return ref.get()

        # Finally, return true
        return data


###################################################################
## Data View Page (Human-readable version)
@app.route("/init/<id>", methods=["POST"])
async def init(id=None):
    """Initialize a new sensor with the service. Must provide an Auth key and
        a unique Sensor ID. All other parameters are not required.
        
        Returns JSON object created in Firebase RTDB."""
    
    ## Check request type and process input:
    if request.method == "POST":
        # Get values from POST body:
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            data = request.get_json()
        else:
            try:
                data = json.loads(request.data)
            except Exception as e:
                print(f"{e} || Exception while processing json from request.data")
                return {}
        _err, s = await util.verify_parameters(data)
        if _err:
            ## Error out and return an empty JSON object
            return {}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
import os
import asyncio
import sqlite3

from flask import Flask, render_template, request, json
from models import Sensor
# Import the Firebase service
import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import db
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

cred = credentials.Certificate(os.environ.get("FIREBASE_AUTH_LOC"))
fb = firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://eel5632-hedgehogs-default-rtdb.firebaseio.com/'
})

## Init SQLite from SQL DB
@app.before_first_request
async def startup():
    # fb = firebase.FirebaseApplication('https://eel5632-hedgehogs-default-rtdb.firebaseio.com/', None)

    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        with open('schema.sql') as f:
            cur.executescript(f.read())

    

@app.route("/")
async def home():
    return render_template('home.html')
    
@app.route("/team")
async def team():
    # res = fb.get('/team', None)
    # print(res)
    return render_template('team.html')

@app.route("/data")
@app.route("/data/")
async def data():
    return render_template('data.html')

## Returns JSON-only object, for mobile app.
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
                data = {"error": "Invalid data type provided. Please ensure you're setting data type in body to JSON."}
        
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

@app.route("/data/view/<id>", methods=["GET"])
def sensor_data_view(id=None):
    sensor = {
        'id': id,
        'name': "My Name"
    }
    return render_template('sensor_data.html', sensor=sensor)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
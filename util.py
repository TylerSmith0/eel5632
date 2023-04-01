import asyncio

from models import Sensor

async def verify_parameters(data):
    """Verifies that the provided data is enough to create an
        instance of a new Sensor() object and returns that Sensor
        object and a status indicator."""
    error = False

    ## TO DO: Process and validate the provided JSON data

    return error, Sensor()


async def update_info(id):
    """Returns an updated Sensor object with live data from
        Firebase RTDB."""

    ## TO DO: Create link to RTDB and error-check for valid ID
    return Sensor()
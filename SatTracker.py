import requests
import json
import logging
import urllib3
from skyfield.api import EarthSatellite, load
import folium
import webbrowser
import os

# Suppress only the single InsecureRequestWarning from urllib3 needed.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging to display debug information
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def fetch_tle(satellite_id):
    """
    Fetches the TLE data for the given satellite ID from the NASA TLE API.

    Args:
        satellite_id (int): The NORAD satellite ID.

    Returns:
        dict: The JSON response as a dictionary if the request is successful.
        None: If the request fails.
    """
    url = f"https://tle.ivanstanojevic.me/api/tle/{satellite_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3',
        'Accept': 'application/json',
    }

    try:
        logger.debug(f"Sending GET request to URL: {url} with headers: {headers}")
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        logger.debug(f"Received response with status code: {response.status_code}")
        response.raise_for_status()
        tle_data = response.json()
        logger.debug(f"Response JSON: {tle_data}")
        return tle_data
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred: {req_err}")
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decode error: {json_err}")

    return None


def calculate_satellite_position(tle_data):
    """
    Calculates the current geographic position (latitude and longitude) of the satellite.

    Args:
        tle_data (dict): The TLE data as a dictionary.

    Returns:
        tuple: (latitude, longitude) in degrees if successful.
        None: If calculation fails.
    """
    try:
        # Extract TLE lines
        line1 = tle_data['line1']
        line2 = tle_data['line2']
        name = tle_data['name']
        logger.debug(f"Satellite Name: {name}")
        logger.debug(f"TLE Line 1: {line1}")
        logger.debug(f"TLE Line 2: {line2}")

        # Create EarthSatellite object
        satellite = EarthSatellite(line1, line2, name, load.timescale())

        # Get current time
        ts = load.timescale()
        t = ts.now()

        # Get the geocentric position of the satellite
        geocentric = satellite.at(t)

        # Get the subpoint (latitude, longitude, elevation)
        subpoint = geocentric.subpoint()
        latitude = subpoint.latitude.degrees
        longitude = subpoint.longitude.degrees
        elevation = subpoint.elevation.km

        logger.debug(f"Satellite Position - Latitude: {latitude}, Longitude: {longitude}, Elevation: {elevation} km")

        return (latitude, longitude)
    except Exception as e:
        logger.error(f"Error calculating satellite position: {e}")
        return None


def create_map(latitude, longitude, satellite_name):
    """
    Creates an interactive map showing the satellite's current location.

    Args:
        latitude (float): Satellite's latitude.
        longitude (float): Satellite's longitude.
        satellite_name (str): Name of the satellite.

    Returns:
        folium.Map: The generated map object.
    """
    try:
        # Create a map centered at the satellite's location
        sat_map = folium.Map(location=[latitude, longitude], zoom_start=4)

        # Add a marker for the satellite's position
        folium.Marker(
            [latitude, longitude],
            popup=f"{satellite_name}<br>Lat: {latitude:.2f}°, Lon: {longitude:.2f}°",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(sat_map)

        # Optionally, add a marker for the satellite's location with a different icon or color
        folium.CircleMarker(
            location=[latitude, longitude],
            radius=10,
            popup=f"{satellite_name}",
            color="crimson",
            fill=True,
            fill_color="crimson"
        ).add_to(sat_map)

        return sat_map
    except Exception as e:
        logger.error(f"Error creating map: {e}")
        return None


def main():
    while True:
        user_input = input("Enter the Satellite ID (NORAD ID) or 'exit' to quit: ").strip()

        if user_input.lower() == 'exit':
            print("Exiting the program. Goodbye!")
            break

        if not user_input.isdigit():
            print("Invalid input. Please enter a numeric Satellite ID.")
            continue

        satellite_id = int(user_input)

        tle_data = fetch_tle(satellite_id)

        if tle_data:
            position = calculate_satellite_position(tle_data)
            if position:
                latitude, longitude = position
                satellite_name = tle_data.get('name', 'Unknown Satellite')

                # Create the map
                sat_map = create_map(latitude, longitude, satellite_name)
                if sat_map:
                    # Save the map to an HTML file
                    map_filename = f"{satellite_id}_location_map.html"
                    sat_map.save(map_filename)
                    print(f"\nTLE Data Retrieved Successfully for {satellite_name}:")
                    print(json.dumps(tle_data, indent=4))
                    print(f"\nSatellite location map has been saved to {map_filename}.")

                    # Automatically open the map in the default web browser
                    map_path = os.path.abspath(map_filename)
                    webbrowser.open(f'file://{map_path}')
                else:
                    print("Failed to create the map.")
            else:
                print("Failed to calculate satellite position.")
        else:
            print("Failed to retrieve TLE data.\n")


if __name__ == "__main__":
    main()

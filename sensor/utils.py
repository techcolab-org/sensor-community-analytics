from typing import Dict

import requests


def get_sensor_details(sensor_id) -> Dict:
   url = f'https://data.sensor.community/airrohr/v1/sensor/{sensor_id}/'
   try:
      response = requests.get(url)
      if response.status_code == 200:
         data = response.json()
         first_data = data[0]

         station_latitude = first_data['location']['latitude']
         station_longitude = first_data['location']['longitude']
         station_altitude = first_data['location']['altitude']

         sensor_type_manufacturer = first_data['sensor']['sensor_type']['manufacturer']
         sensor_type_name = first_data['sensor']['sensor_type']['name']

         sensordatavalues = first_data['sensordatavalues']
         sensor_value_types = []
         for item in sensordatavalues:
            sensor_value_types.append(item['value_type'])

         return{
            'station_latitude': station_latitude,
            'station_longitude': station_longitude,
            'station_altitude': station_altitude,
            'sensor_type_manufacturer': sensor_type_manufacturer,
            'sensor_type_name': sensor_type_name,
            'sensor_value_types': sensor_value_types
         }

   except Exception as e:
      return {}


from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

_geolocator = Nominatim(user_agent="sensolog_app")
_reverse = RateLimiter(_geolocator.reverse, min_delay_seconds=1)

def reverse_geocode(point):
    """
    point: GEOS Point (lon, lat)
    """
    if not point:
        return None

    location = _reverse(
        (point.y, point.x),  # lat, lon
        exactly_one=True,
        language="en",
    )

    if not location:
        return None

    address = location.raw.get("address", {})

    return {
        "display_name": location.address,
        "country": address.get("country"),
        "state": address.get("state"),
        "city": address.get("city")
                or address.get("town")
                or address.get("village"),
    }



if __name__ == '__main__':
   get_sensor_details(94331)
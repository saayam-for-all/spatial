from models import LocationData
from extensions import db

def process_location_data(data):
    lat = data.get('latitude')
    long = data.get('longitude')
    city = data.get('city')
    country = data.get('country')

    location = LocationData(
        latitude=lat,
        longitude=long,
        city=city,
        country=country
    )
    
    db.session.add(location)
    db.session.commit()

    return {"latitude": lat, "longitude": long, "city": city, "country": country}
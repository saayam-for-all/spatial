# spatial
This repo consists of all the work related to geo spatial support

This Flask-based microservice captures and stores geographical spatial data (latitude, longitude, city, country) received from mobile or web clients.

## Features:
- Capture and process latitude and longitude.
- Store data in a relational database (e.g., SQLite for local testing or PostgreSQL for production).
- Provide a REST endpoint to capture or get location information.
- Provide a REST endpoint to get top 'N' nearest neighbour's location for a given location.

## Project Structure:
- **app.py**: Main application file with route definitions.
- **config.py**: Configuration settings for the application.
- **extensions.py**: Initializes Flask extensions (SQLAlchemy for database management).
- **models.py**: Defines database models.
- **location.py**: Contains the logic for processing and storing the location data.
- **util.py**: Helper file for spatial calculations.

## Setup Instructions:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/geo-location-service.git
   cd geo-location-service

2.	Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # For Linux/macOS
    venv\Scripts\activate  # For Windows

3. Install Requirements
    ```bash
    pip install -r requirements.txt

4. Setup the database
    ```bash
    flask shell
    from app import db
    db.create_all()
    exit()

5. Starting the Flask server
    •	For Linux/macOS:
   
        export FLASK_APP=app
        flask run
    
    •	For Windows:
   
        set FLASK_APP=app
        flask run

## API Instructions:
1.	Sending a Request (assuming that our server is running at localhost):
   
      •	Capture Location (with address):
  	
            Method: POST
            URL: http://<localhost>/location
            Headers:
               Key: Content-Type
               Value: application/json
            Body (raw JSON sample example):
               {
                   "user_id": 1,
                   "address": "1600 Amphitheatre Parkway, Mountain View, CA"
               }
      
   
      •	Capture Location (using current location):
  	
            Method: POST
            URL: http://<localhost>/location
            Headers:
               Key: Content-Type
               Value: application/json
            Body (raw JSON sample example):
               {
                   "user_id": 2,
                   "use_current_location": true
               }
            
   
      •	 Capture Location (no address provided, will use IP):

            Method: POST
            URL: http://<localhost>/location
            Headers:
               Key: Content-Type
               Value: application/json
            Body (raw JSON sample example):
               {
                   "user_id": 3
               }


2. Get User Location:
   
         Method: GET
         URL: http://<localhost>/user_location/<user_id>
         Sample output (for user_id = 1):
            {
              "user_id": 1,
              "latitude": 37.4220,
              "longitude": -122.0841,
              "timestamp": "2023-05-20T15:30:45.123456"
            }
   
3. Get 'N' Nearest Volunteer Location:
   
         Method: POST
         URL: http://<localhost>/nearest_volunteers
          Headers:
               Key: Content-Type
               Value: application/json

            Body (raw JSON sample example):
               {
                  "latitude": <latitude value>,
                  "longitude": <longitude value>,
                  "limit": <limit on total numbers of volunteers to match>
                  "min_radius": <minimum radius in KM>,
                  "max_radius": <maximum radius in KM>,
                  "exception_id": <user id which we should not process>
               }

5. Update Volunteer's avilability:
   
         Method: POST
         URL: http://<localhost>/update_availability
          Headers:
               Key: Content-Type
               Value: application/json
            Body (raw JSON sample example):
               {
                  "user_id": <user_id>,
                  "availability": <true or false>
               } 

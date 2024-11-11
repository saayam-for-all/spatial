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

## Running the Test Suite:
1. test_app.py: checks all the api's exposed in app.py

         $ python3 -m pytest test_app.py -v

         Sample output:
         ================================================ test session starts ================================================

         test_app.py::test_01_capture_location_use_current_location PASSED                                             [ 14%]
         test_app.py::test_01_capture_location_with_address PASSED                                                     [ 28%]
         test_app.py::test_01_capture_location_invalid_data PASSED                                                     [ 42%]
         test_app.py::test_02_get_user_location PASSED                                                                 [ 57%]
         test_app.py::test_02_get_user_location_not_found PASSED                                                       [ 71%]
         test_app.py::test_03_find_nearest_volunteers PASSED                                                           [ 85%]
         test_app.py::test_03_find_nearest_volunteers_invalid_data PASSED                                              [100%]

         ================================================= 7 passed in 0.83s =================================================

3. test_location.py: checks all the menthods written in location.py in various scenarios

         $ python3 -m pytest test_location.py -v
         
         Sample output:
         ================================================ test session starts ================================================
         
         test_location.py::test_01_volunteers_in_different_tiles PASSED                                                [  3%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[normal_case] PASSED                                [  6%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[with_min_radius] PASSED                            [  9%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[unavailable_volunteers] PASSED                     [ 12%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[no_volunteers_in_area] PASSED                      [ 16%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[volunteers_outside_radius] PASSED                  [ 19%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[same_tile_search] PASSED                           [ 22%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[cross_tile_search] PASSED                          [ 25%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[global_search] PASSED                              [ 29%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[date_line_search] PASSED                           [ 32%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[pole_search] PASSED                                [ 35%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[zero_radius_search] PASSED                         [ 38%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[negative_radius] PASSED                            [ 41%]
         test_location.py::test_02_get_nearest_volunteers_scenarios[reversed_radius_bounds] PASSED                     [ 45%]
         test_location.py::test_03_lat_lon_tile_conversion PASSED                                                      [ 48%]
         test_location.py::test_04_tile_bounds PASSED                                                                  [ 51%]
         test_location.py::test_05_neighboring_tiles PASSED                                                            [ 54%]
         test_location.py::test_06_calculate_distance[coordinates0-157.2] PASSED                                       [ 58%]
         test_location.py::test_06_calculate_distance[coordinates1-0] PASSED                                           [ 61%]
         test_location.py::test_06_calculate_distance[coordinates2-20015.1] PASSED                                     [ 64%]
         test_location.py::test_07_get_location_by_address[mock_response0-London-expected0-Valid address] PASSED       [ 67%]
         test_location.py::test_07_get_location_by_address[mock_response1-NonexistentPlace-None-Invalid address] PASSED [ 70%]
         test_location.py::test_07_get_location_by_address[mock_response2-New York-expected2-Another valid address] PASSED [ 74%]
         test_location.py::test_07_get_location_by_address[None-Paris-None-RequestException scenario] PASSED           [ 77%]
         test_location.py::test_07_get_location_by_address[mock_response4-Berlin-None-KeyError scenario] PASSED        [ 80%]
         test_location.py::test_08_get_location_by_ip[mock_response0-8.8.8.8-expected0-Valid IP] PASSED                [ 83%]
         test_location.py::test_08_get_location_by_ip[mock_response1-1.1.1.1-expected1-Another valid IP] PASSED        [ 87%]
         test_location.py::test_08_get_location_by_ip[None-192.168.0.1-expected2-RequestException scenario] PASSED     [ 90%]
         test_location.py::test_08_get_location_by_ip[mock_response3-10.0.0.1-expected3-KeyError scenario] PASSED      [ 93%]
         test_location.py::test_08_get_location_by_ip[mock_response4-172.16.0.1-expected4-ValueError scenario] PASSED  [ 96%]
         test_location.py::test_09_get_location_integration PASSED                                                     [100%]
         
         ================================================ 31 passed in 7.51s =================================================

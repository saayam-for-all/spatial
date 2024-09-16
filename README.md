# spatial
This repo consists of all the work related to geo spatial support

This Flask-based microservice captures and stores geographical spatial data (latitude, longitude, city, country) received from mobile or web clients.

## Features:
- Capture and process latitude and longitude, along with city and country.
- Store data in a relational database (e.g., SQLite for local testing or PostgreSQL for production).
- Provide a REST endpoint to capture location information.

## Project Structure:
- **app.py**: Main application file with route definitions.
- **config.py**: Configuration settings for the application.
- **extensions.py**: Initializes Flask extensions (SQLAlchemy for database management).
- **models.py**: Defines database models.
- **location.py**: Contains the logic for processing and storing the location data.

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
        ```bash
        export FLASK_APP=app
        flask run
    
    •	For Windows:
        ```bash
        set FLASK_APP=app
        flask run

6.	Sending a Request:
    ```bash
    curl -X POST http://127.0.0.1:5000/location -H "Content-Type: application/json" \
    -d '{"latitude": "40.7128", "longitude": "-74.0060", "city": "New York", "country": "USA"}'
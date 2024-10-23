from extensions import db
from datetime import datetime, timezone

# User database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_requests = db.relationship('LocationRequest', backref='user', lazy=True)
    is_volunteer = db.Column(db.Boolean, default=False)
    tile_id = db.Column(db.String(16), index=True)
    last_login = db.Column(db.DateTime, default=datetime.now(timezone.utc))

# Volunteer database
class Volunteer(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    availability = db.Column(db.Boolean, default=True)
    
# Location reqtests made database
class LocationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<LocationRequest {self.latitude}, {self.longitude}>'

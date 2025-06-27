from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_watered = db.Column(db.DateTime(timezone=True), nullable=True)
    soil_moisture = db.Column(db.Integer)
    temperature = db.Column(db.Integer)
    system_status = db.Column(db.String(150))
    plant_status = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    plant_name = db.Column(db.String(150))
    plants = db.relationship('Plant')
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime
from .models import Plant, User
from . import db
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import board
import busio
import time
import threading
import logging

views = Blueprint('views', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sensor_data = {
    "last_watered": "--",
    "soil_moisture": 0.0,
    "temperature": 0.0,
    "plant_status": "Not Connected"
}

# Initialize sensors with error handling
try:
    dhtDevice = adafruit_dht.DHT11(board.D4)
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    channel = AnalogIn(ads, ADS.P0)
    logger.info("Sensors initialized successfully")
except Exception as e:
    logger.error(f"Sensor initialization failed: {e}")
    raise

DRY_VOLTAGE = 1.0
WET_VOLTAGE = 2.8

# Thread management
active_threads = {}  # Dictionary to track threads {user_id: thread}

def start_background_thread(app, user_id):
    if user_id in active_threads:
        logger.info(f"Thread already running for user {user_id}")
        return
    
    def thread_func():
        logger.info(f"Starting sensor loop for user {user_id}")
        try:
            with app.app_context():
                read_sensor_loop(user_id)
        except Exception as e:
            logger.error(f"Thread for user {user_id} crashed: {e}")
        finally:
            active_threads.pop(user_id, None)
            logger.info(f"Thread for user {user_id} stopped")

    thread = threading.Thread(target=thread_func, daemon=True)
    thread.start()
    active_threads[user_id] = thread
    logger.info(f"Started new thread for user {user_id}")

def read_sensor_loop(user_id):
    while True:
        try:
            # Read temperature
            try:
                temperature = dhtDevice.temperature
                temperature = int(temperature)
            except Exception as e:
                logger.error(f"DHT11 read failed: {e}")
                temperature = None

            # Read moisture
            try:
                moisture_voltage = channel.voltage
            except Exception as e:
                logger.error(f"ADS1115 read failed: {e}")
                moisture_voltage = 0

            if temperature is None:
                logger.warning("Skipping update due to failed temperature reading")
                time.sleep(5)
                continue

            # Calculate moisture percentage
            soil_moisture = (moisture_voltage - DRY_VOLTAGE) / (WET_VOLTAGE - DRY_VOLTAGE) * 100
            soil_moisture = max(0, min(100, soil_moisture))
            soil_moisture = int(soil_moisture)

            # Update sensor data
            sensor_data.update({
                "last_watered": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "soil_moisture": soil_moisture,
                "temperature": temperature,
            })

            # Update database
            try:
                plant = Plant.query.filter_by(user_id=user_id).first()
                if plant:
                    plant.temperature = temperature
                    plant.soil_moisture = soil_moisture
                    db.session.commit()
            except Exception as e:
                logger.error(f"Database update failed: {e}")
                db.session.rollback()

            time.sleep(5)

        except Exception as e:
            logger.error(f"Unexpected error in sensor loop: {e}")
            time.sleep(5)

@views.route('/landing')
def landing():
    return render_template("landing.html")

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    user_plants = Plant.query.filter_by(user_id=current_user.id).first_or_404()
    user_plants.system_status = "Connected"
    db.session.commit()
    start_background_thread(current_app._get_current_object(), current_user.id)
    return render_template("home.html", user=current_user)

@views.route('/system', methods=['POST', 'GET'])
@login_required
def system():
    plant = Plant.query.filter_by(user_id=current_user.id).first()
    system_status = plant.system_status
    plant_status = plant.plant_status
    if plant:
        return jsonify({
            "last_watered": plant.last_watered.strftime("%Y-%m-%d %H:%M:%S") if plant.last_watered else None,
            "soil_moisture": plant.soil_moisture,
            "temperature": plant.temperature,
            "system_status": system_status,
            "plant_status": plant_status
        })
    else:
        return jsonify({
            "last_watered": "Unknown",
            "soil_moisture": 0,
            "temperature": 0,
            "system_status": "Unknown",
            "plant_status": "Unknown"
        })
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='prophet')  # suppress plotly warnings

from flask import Flask, jsonify, request
from flask_cors import CORS
from prophet import Prophet
from dateutil.relativedelta import relativedelta
from pymodbus.client import ModbusSerialClient as ModbusClient
import pandas as pd
import socket
import time
from threading import Thread, Event
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000",
    "https://opticool.vercel.app",
    "https://opticoolweb-backend.onrender.com"
]}})

# IoT config
esp32_host = "192.168.0.102"
esp8266_host = "192.168.0.103"
port = 8080

# Shared states
polling_thread = None
stop_event = Event()
start_event = Event()
ac_temperature = 24  # default temp
power_status = 0

# Modbus connection (without 'method' arg)
client = ModbusClient(port='COM4', baudrate=9600, timeout=1)

# TCP sender to ESP
def send_command_to_esp(host, message):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.sendall(message.encode())
    except Exception as e:
        print(f"Error sending to {host}: {e}")

# Trigger devices via ESP
def control_devices():
    global power_status
    power_status = 1
    message = f"temperature:{ac_temperature},power_status:{power_status}"
    
    send_command_to_esp(esp8266_host, message)
    send_command_to_esp(esp32_host, message)
    time.sleep(3)
    send_command_to_esp(esp8266_host, message)

# Monitor sensor temperature (from Modbus)
def check_temp_set_point():
    while not stop_event.is_set():
        try:
            if client.connect():
                result = client.read_holding_registers(0, 2, slave=1)
                if not result.isError():
                    current_temp = result.registers[1] / 10
                    print(f"[Sensor1] Temp: {current_temp}°C")
                result2 = client.read_holding_registers(0, 2, slave=4)
                if not result2.isError():
                    outside_temp = result2.registers[1] / 10
                    print(f"[Sensor4] Outside Temp: {outside_temp}°C")
                time.sleep(10)
        except Exception as e:
            print(f"Error in temp set point check: {e}")

def start_polling_threads():
    global polling_thread
    if polling_thread is None:
        polling_thread = Thread(target=check_temp_set_point)
        polling_thread.start()

def stop_polling_threads():
    global polling_thread
    stop_event.set()
    if polling_thread and polling_thread.is_alive():
        polling_thread.join()
    polling_thread = None

# --- Flask Routes ---

@app.route('/start', methods=['POST'])
def start_polling():
    try:
        client.connect()
    except Exception as e:
        print(f"Error: {e}")
    stop_event.clear()
    start_event.set()
    start_polling_threads()
    Thread(target=control_devices).start()
    return jsonify({'message': 'Polling and control started'}), 200

@app.route('/stop', methods=['POST'])
def stop_polling():
    global power_status
    if client.connected:
        client.close()
    start_event.clear()
    stop_polling_threads()

    power_status = 0
    message = f"temperature:{ac_temperature},power_status:{power_status}"
    send_command_to_esp(esp32_host, message)
    send_command_to_esp(esp8266_host, message)
    time.sleep(8)
    send_command_to_esp(esp8266_host, message)

    return jsonify({'message': 'Polling stopped'}), 200

@app.route('/adjust_temperature', methods=['POST'])
def adjust_temperature():
    global ac_temperature
    adjustment = request.json.get('adjustment')
    if adjustment == 'up' and ac_temperature < 25:
        ac_temperature += 1
    elif adjustment == 'down' and ac_temperature > 19:
        ac_temperature -= 1

    message = f"temperature:{ac_temperature},power_status:{power_status}"
    send_command_to_esp(esp32_host, message)
    send_command_to_esp(esp8266_host, message)
    return jsonify({'temperature': ac_temperature})

@app.route('/predictpower', methods=['POST'])
def predict_power():
    data = request.json
    df = pd.DataFrame(data)
    if df.shape[0] < 2:
        return jsonify([])

    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
    df = df.rename(columns={'timestamp': 'ds', 'consumption': 'y'})

    model = Prophet(
        changepoint_prior_scale=0.5,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False
    )
    model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    model.fit(df)

    last_date = df['ds'].max()
    future_end = last_date + relativedelta(months=3)
    future_dates = pd.date_range(
        start=last_date + relativedelta(months=1),
        end=future_end,
        freq='MS'
    ).tz_localize(None)

    future_df = pd.DataFrame({'ds': future_dates})
    forecast = model.predict(future_df)

    results = [
        {'timestamp': row['ds'].isoformat(), 'consumption': row['yhat']}
        for _, row in forecast.iterrows()
    ]
    return jsonify(results)

# --- Run Server ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True)

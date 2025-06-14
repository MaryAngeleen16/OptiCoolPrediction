from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from prophet import Prophet
from dateutil.relativedelta import relativedelta
import os

app = Flask(__name__)

# ✅ Allow CORS from frontend domains
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000",
    "https://opticool.vercel.app",
    "https://opticoolweb-backend.onrender.com"
]}})

# ---------- Forecasting Endpoint ----------
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

# ---------- Device Control Endpoints ----------
current_temp = 24
devices = {
    "AC": False,
    "EFans": False,
    "Blower": False,
    "Exhaust": False,
}

@app.route('/api/getTemp', methods=['GET'])
def get_temp():
    return jsonify(temp=current_temp)

@app.route('/api/adjustTemp', methods=['POST'])
def adjust_temp():
    global current_temp
    data = request.json
    current_temp = data.get("temp", current_temp)
    print(f"[LOG] AC temperature set to: {current_temp}°C")
    return jsonify(success=True, new_temp=current_temp)

@app.route('/api/turnOnAllAC', methods=['POST'])
def turn_on_all_ac():
    devices["AC"] = True
    print("[LOG] All ACs turned ON")
    return jsonify(success=True)

@app.route('/api/turnOffAllAC', methods=['POST'])
def turn_off_all_ac():
    devices["AC"] = False
    print("[LOG] All ACs turned OFF")
    return jsonify(success=True)

@app.route('/api/turnOnEFans', methods=['POST'])
def turn_on_efans():
    devices["EFans"] = True
    print("[LOG] EFans turned ON")
    return jsonify(success=True)

@app.route('/api/turnOffEFans', methods=['POST'])
def turn_off_efans():
    devices["EFans"] = False
    print("[LOG] EFans turned OFF")
    return jsonify(success=True)

@app.route('/api/turnOnBlower', methods=['POST'])
def turn_on_blower():
    devices["Blower"] = True
    print("[LOG] Blower turned ON")
    return jsonify(success=True)

@app.route('/api/turnOffBlower', methods=['POST'])
def turn_off_blower():
    devices["Blower"] = False
    print("[LOG] Blower turned OFF")
    return jsonify(success=True)

@app.route('/api/turnOnExhaust', methods=['POST'])
def turn_on_exhaust():
    devices["Exhaust"] = True
    print("[LOG] Exhaust turned ON")
    return jsonify(success=True)

@app.route('/api/turnOffExhaust', methods=['POST'])
def turn_off_exhaust():
    devices["Exhaust"] = False
    print("[LOG] Exhaust turned OFF")
    return jsonify(success=True)

# ---------- Run the app ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

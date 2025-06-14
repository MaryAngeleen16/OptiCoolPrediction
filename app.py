from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from prophet import Prophet
from dateutil.relativedelta import relativedelta
import os
from gpio import GPIOController  # Make sure gpio.py is in the same folder

app = Flask(__name__)

# ✅ CORS setup
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000",
    "https://opticool.vercel.app",
    "https://opticoolweb-backend.onrender.com"
]}})

# ✅ Initialize GPIO controller
gpio = GPIOController()


# ✅ Power prediction route
@app.route('/predictpower', methods=['POST'])
def predict_power():
    data = request.json
    df = pd.DataFrame(data)

    if df.shape[0] < 2:
        return jsonify([])

    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
    df = df.rename(columns={'timestamp': 'ds', 'consumption': 'y'})

    model = Prophet(changepoint_prior_scale=0.5,
                    yearly_seasonality=False,
                    weekly_seasonality=False,
                    daily_seasonality=False)
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


# ✅ AC controls
@app.route('/api/turnOnAllAC', methods=['POST'])
def turn_on_all_ac():
    gpio.turn_on_ac_units()
    print("[LOG] All ACs turned ON (GPIO)")
    return jsonify(success=True)

@app.route('/api/turnOffAllAC', methods=['POST'])
def turn_off_all_ac():
    gpio.turn_off_ac_units()
    print("[LOG] All ACs turned OFF (GPIO)")
    return jsonify(success=True)


# ✅ EFan controls
@app.route('/api/turnOnEFans', methods=['POST'])
def turn_on_efans():
    gpio.turn_on_e_fans()
    print("[LOG] EFans turned ON (GPIO)")
    return jsonify(success=True)

@app.route('/api/turnOffEFans', methods=['POST'])
def turn_off_efans():
    gpio.turn_off_e_fans()
    print("[LOG] EFans turned OFF (GPIO)")
    return jsonify(success=True)


# ✅ Blower controls
@app.route('/api/turnOnBlower', methods=['POST'])
def turn_on_blower():
    gpio.turn_on_timed_blower()
    print("[LOG] Blower turned ON (timed GPIO)")
    return jsonify(success=True)

@app.route('/api/turnOffBlower', methods=['POST'])
def turn_off_blower():
    gpio.turn_off_blower()
    print("[LOG] Blower turned OFF (GPIO)")
    return jsonify(success=True)


# ✅ Exhaust controls
@app.route('/api/turnOnExhaust', methods=['POST'])
def turn_on_exhaust():
    gpio.turn_on_timed_exhaust()
    print("[LOG] Exhaust turned ON (timed GPIO)")
    return jsonify(success=True)

@app.route('/api/turnOffExhaust', methods=['POST'])
def turn_off_exhaust():
    gpio.turn_off_exhaust()
    print("[LOG] Exhaust turned OFF (GPIO)")
    return jsonify(success=True)


# ✅ Clean up GPIO on shutdown
import atexit
@atexit.register
def cleanup_gpio():
    gpio.cleanup()
    print("[LOG] GPIO cleaned up on shutdown")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

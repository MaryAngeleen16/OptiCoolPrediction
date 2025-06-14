from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from prophet import Prophet
from dateutil.relativedelta import relativedelta
import os

app = Flask(__name__)

# ✅ Proper CORS setup for development & production frontend
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000",
    "https://opticool.vercel.app",
    "https://opticoolweb-backend.onrender.com"
]}})

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
    future_end = last_date + relativedelta(months=3)  # forecast 3 months instead of 6

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



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
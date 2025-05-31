from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from prophet import Prophet
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",                    # for local React dev
    "https://opticoolweb-backend.onrender.com"  # for deployed frontend
])

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')  # Change '*' to your frontend URL in production
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/predictpower', methods=['POST'])
def predict_power():
    data = request.json
    df = pd.DataFrame(data)
    if df.shape[0] < 2:
        return jsonify([])

    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
    df = df.rename(columns={'timestamp': 'ds', 'consumption': 'y'})

    model = Prophet()
    model.fit(df)

    last_date = df['ds'].max()
    future_end = last_date + relativedelta(months=6)
    future_dates = pd.date_range(start=last_date + relativedelta(months=1),
                                 end=future_end, freq='MS')
    future_df = pd.DataFrame({'ds': future_dates})
    forecast = model.predict(future_df)

    results = [{'timestamp': row['ds'].isoformat(), 'consumption': row['yhat']} for _, row in forecast.iterrows()]
    return jsonify(results)

if __name__ == '__main__':
    app.run()

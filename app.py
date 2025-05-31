from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from prophet import Prophet
from datetime import timedelta
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
CORS(app)

@app.route('/predictpower', methods=['POST'])
def predict_power():
    data = request.json
    df = pd.DataFrame(data)

    if df.shape[0] < 2:
        return jsonify([])

    # Convert timestamp and strip timezone
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)

    # Rename columns for Prophet
    df = df.rename(columns={'timestamp': 'ds', 'consumption': 'y'})

    # Create and fit the Prophet model
    model = Prophet()
    model.fit(df)

    # Forecast 6 months from last data point
    last_date = df['ds'].max()
    future_end = last_date + relativedelta(months=6)

    future_dates = pd.date_range(start=last_date + relativedelta(months=1),
                                 end=future_end,
                                 freq='MS')
    future_df = pd.DataFrame({'ds': future_dates})

    forecast = model.predict(future_df)

    results = []
    for _, row in forecast.iterrows():
        results.append({
            'timestamp': row['ds'].isoformat(),
            'consumption': row['yhat']
        })

    return jsonify(results)

if __name__ == '__main__':
    app.run()

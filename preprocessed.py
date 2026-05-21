import pandas as pd
import numpy as np
import os

path = os.path.join(os.path.dirname(__file__), 'one_room_apartement.csv')
df = pd.read_csv(path)
print(f"Loaded: {df.shape}")

keep = ['timestamp', 'temperature', 'humidity']
df = df[keep].copy()

df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True)

anomaly_dates = ['2023-07-09', '2023-04-17', '2023-05-21']
mask = df['timestamp'].dt.date.astype(str).isin(anomaly_dates)
print(f"Anomaly rows dropped: {mask.sum()}")
df = df[~mask].reset_index(drop=True)

df['year']        = df['timestamp'].dt.year
df['month']       = df['timestamp'].dt.month
df['day_of_week'] = df['timestamp'].dt.dayofweek   # 0=Mon, 6=Sun
df['hour']        = df['timestamp'].dt.hour
df['quarter']     = df['timestamp'].dt.quarter
df['is_weekend']  = df['day_of_week'].isin([5, 6]).astype(int)

df.drop(columns=['timestamp'], inplace=True)

# 6. Comfort score (1–10, integer)
# Temperature: ideal 20–22°C (WHO & EN 15251 for living rooms)
# Humidity:    ideal 40–60%

def temp_score(t):
    if 20 <= t <= 22:
        return 1.0
    elif 16 <= t < 20:
        return (t - 16) / (20 - 16)
    elif 22 < t <= 28:
        return (28 - t) / (28 - 22)
    else:
        return 0.0

def hum_score(h):
    if 40 <= h <= 60:
        return 1.0
    elif 20 <= h < 40:
        return (h - 20) / (40 - 20)
    elif 60 < h <= 80:
        return (80 - h) / (80 - 60)
    else:
        return 0.0

df['_t_score'] = df['temperature'].apply(temp_score)
df['_h_score'] = df['humidity'].apply(hum_score)

# Weighted: temperature 60%, humidity 40%
raw = 0.6 * df['_t_score'] + 0.4 * df['_h_score']

# Scale to 1–10, round to integer
df['comfort'] = (raw * 9 + 1).round(0).astype(int)

df.drop(columns=['_t_score', '_h_score'], inplace=True)

print(f"\nFinal shape: {df.shape}")
print(f"\nColumns: {list(df.columns)}")
print(f"\nComfort distribution:")
print(df['comfort'].value_counts().sort_index())
print(f"\nSample:")
print(df.head(10).to_string())

out = os.path.join(os.path.dirname(__file__), 'preprocessed.csv')
df.to_csv(out, index=False)
print(f"Final shape: {df.shape}")
print(f"Saved to: {out}")




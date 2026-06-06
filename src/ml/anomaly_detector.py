import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import pickle
import os

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100
        )
        self.label_encoders = {}
        self.is_trained = False
        self.feature_columns = [
            'amount', 'hour_of_day', 'merchant_category_encoded',
            'location_encoded', 'is_foreign_location'
        ]

    def prepare_features(self, transaction: dict) -> np.ndarray:
        if 'merchant_category' not in self.label_encoders:
            self.label_encoders['merchant_category'] = LabelEncoder()
            self.label_encoders['merchant_category'].fit([
                'grocery', 'restaurant', 'gas_station', 'online_retail',
                'electronics', 'pharmacy', 'travel', 'entertainment',
                'clothing', 'jewelry'
            ])

        if 'location' not in self.label_encoders:
            self.label_encoders['location'] = LabelEncoder()
            self.label_encoders['location'].fit([
                'New York, NY', 'Los Angeles, CA', 'Chicago, IL',
                'Houston, TX', 'Phoenix, AZ', 'Philadelphia, PA',
                'San Antonio, TX', 'San Diego, CA', 'Dallas, TX',
                'San Jose, CA', 'Austin, TX', 'Miami, FL',
                'Seattle, WA', 'Denver, CO', 'Boston, MA',
                'Lagos, Nigeria', 'Moscow, Russia', 'Beijing, China',
                'Cairo, Egypt', 'Mumbai, India'
            ])

        try:
            category_encoded = self.label_encoders['merchant_category'].transform(
                [transaction.get('merchant_category', 'grocery')]
            )[0]
        except ValueError:
            category_encoded = 0

        try:
            location_encoded = self.label_encoders['location'].transform(
                [transaction.get('location', 'New York, NY')]
            )[0]
        except ValueError:
            location_encoded = 99

        features = np.array([[
            float(transaction.get('amount', 0)),
            float(transaction.get('hour_of_day', 12)),
            float(category_encoded),
            float(location_encoded),
            float(transaction.get('is_foreign_location', False))
        ]])

        return features

    def train(self, transactions: list):
        print(f"Training Isolation Forest on {len(transactions)} transactions...")
        feature_matrix = []
        for t in transactions:
            features = self.prepare_features(t)
            feature_matrix.append(features[0])

        X = np.array(feature_matrix)
        self.model.fit(X)
        self.is_trained = True
        print("Model trained successfully.")

    def predict(self, transaction: dict) -> dict:
        features = self.prepare_features(transaction)
        prediction = self.model.predict(features)[0]
        anomaly_score = self.model.score_samples(features)[0]
        normalized_score = 1 / (1 + np.exp(anomaly_score))
        is_anomaly = prediction == -1

        return {
            'is_anomaly': bool(is_anomaly),
            'anomaly_score': float(normalized_score),
            'raw_score': float(anomaly_score)
        }

    def save_model(self, path: str = 'models/anomaly_detector.pkl'):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        print(f"Model saved to {path}")

    @classmethod
    def load_model(cls, path: str = 'models/anomaly_detector.pkl'):
        with open(path, 'rb') as f:
            return pickle.load(f)
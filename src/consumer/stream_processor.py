import json
import time
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv
from ml.anomaly_detector import AnomalyDetector
from ai.explanation_engine import ExplanationEngine
from snowflake.snowflake_loader import SnowflakeLoader

load_dotenv('../../config/.env')

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'financial_transactions')
KAFKA_ANOMALY_TOPIC = os.getenv('KAFKA_ANOMALY_TOPIC', 'anomaly_alerts')

def main():
    print("Initializing Stream Processor...")

    # Initialize components
    detector = AnomalyDetector()
    explanation_engine = ExplanationEngine()
    snowflake_loader = SnowflakeLoader()

    # Warm up model with synthetic data
    print("Warming up ML model...")
    synthetic_data = []
    import random
    for _ in range(500):
        synthetic_data.append({
            'amount': random.uniform(10, 300),
            'hour_of_day': random.randint(8, 22),
            'merchant_category': random.choice([
                'grocery', 'restaurant', 'gas_station',
                'online_retail', 'electronics'
            ]),
            'location': random.choice([
                'New York, NY', 'Los Angeles, CA', 'Chicago, IL',
                'Houston, TX', 'Phoenix, AZ'
            ]),
            'is_foreign_location': False
        })
    detector.train(synthetic_data)

    # Set up Kafka consumer
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        group_id='fraud-detection-group'
    )

    # Set up Kafka producer for anomaly alerts
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    print(f"Listening to Kafka topic: {KAFKA_TOPIC}")
    print("Stream processor is live. Detecting anomalies in real time...\n")

    processed = 0
    anomalies_found = 0

    for message in consumer:
        transaction = message.value

        # Run ML prediction
        result = detector.predict(transaction)
        transaction['anomaly_score'] = result['anomaly_score']
        transaction['is_anomaly'] = result['is_anomaly']

        # Load to Snowflake
        snowflake_loader.insert_transaction(transaction)

        if result['is_anomaly']:
            anomalies_found += 1

            # Get GPT-4 explanation
            explanation = explanation_engine.explain(transaction)
            transaction['ai_explanation'] = explanation

            # Send to anomaly topic
            producer.send(KAFKA_ANOMALY_TOPIC, value=transaction)

            # Load flagged transaction to Snowflake
            snowflake_loader.insert_flagged_transaction(transaction)

            print(f"🚨 ANOMALY DETECTED!")
            print(f"   Customer: {transaction['customer_id']}")
            print(f"   Amount: ${transaction['amount']}")
            print(f"   Merchant: {transaction['merchant']}")
            print(f"   Location: {transaction['location']}")
            print(f"   Score: {result['anomaly_score']:.4f}")
            print(f"   AI: {explanation[:100]}...")
            print()

        processed += 1
        if processed % 100 == 0:
            print(f"Processed: {processed} | Anomalies: {anomalies_found}")

if __name__ == "__main__":
    main()
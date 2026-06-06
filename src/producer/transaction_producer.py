import json
import time
import random
import uuid
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker
from dotenv import load_dotenv
import os

load_dotenv('../config/.env')

fake = Faker()

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'financial_transactions')

MERCHANT_CATEGORIES = [
    'grocery', 'restaurant', 'gas_station', 'online_retail',
    'electronics', 'pharmacy', 'travel', 'entertainment',
    'clothing', 'jewelry'
]

MERCHANTS = {
    'grocery': ['Walmart', 'Whole Foods', 'Trader Joes', 'Kroger', 'Safeway'],
    'restaurant': ['McDonalds', 'Chipotle', 'Olive Garden', 'Starbucks', 'Subway'],
    'gas_station': ['Shell', 'Chevron', 'BP', 'ExxonMobil', 'Valero'],
    'online_retail': ['Amazon', 'eBay', 'Etsy', 'Shopify Store', 'Walmart Online'],
    'electronics': ['Best Buy', 'Apple Store', 'Microsoft Store', 'GameStop', 'Newegg'],
    'pharmacy': ['CVS', 'Walgreens', 'Rite Aid', 'Walmart Pharmacy', 'Costco Pharmacy'],
    'travel': ['Delta Airlines', 'Marriott', 'Airbnb', 'Uber', 'Lyft'],
    'entertainment': ['Netflix', 'Spotify', 'AMC Theaters', 'Ticketmaster', 'Steam'],
    'clothing': ['Nike', 'Zara', 'H&M', 'Gap', 'Nordstrom'],
    'jewelry': ['Tiffany', 'Zales', 'Kay Jewelers', 'Pandora', 'Cartier']
}

NORMAL_AMOUNT_RANGES = {
    'grocery': (10, 200),
    'restaurant': (5, 100),
    'gas_station': (20, 80),
    'online_retail': (10, 300),
    'electronics': (20, 500),
    'pharmacy': (5, 150),
    'travel': (50, 800),
    'entertainment': (5, 50),
    'clothing': (20, 300),
    'jewelry': (50, 500)
}

LOCATIONS = [
    'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
    'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
    'Dallas, TX', 'San Jose, CA', 'Austin, TX', 'Miami, FL',
    'Seattle, WA', 'Denver, CO', 'Boston, MA'
]

def generate_normal_transaction(customer_id, usual_location):
    category = random.choice(MERCHANT_CATEGORIES)
    merchant = random.choice(MERCHANTS[category])
    min_amt, max_amt = NORMAL_AMOUNT_RANGES[category]
    amount = round(random.uniform(min_amt, max_amt), 2)
    
    return {
        'transaction_id': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat(),
        'customer_id': customer_id,
        'amount': amount,
        'merchant': merchant,
        'merchant_category': category,
        'location': usual_location,
        'hour_of_day': datetime.utcnow().hour,
        'is_foreign_location': False
    }

def generate_anomalous_transaction(customer_id, usual_location):
    anomaly_type = random.choice([
        'huge_amount', 'foreign_location', 'unusual_hour',
        'unusual_category', 'multiple_locations'
    ])
    
    category = random.choice(MERCHANT_CATEGORIES)
    merchant = random.choice(MERCHANTS[category])
    
    if anomaly_type == 'huge_amount':
        amount = round(random.uniform(2000, 15000), 2)
        location = usual_location
        hour = datetime.utcnow().hour
        is_foreign = False
        
    elif anomaly_type == 'foreign_location':
        amount = round(random.uniform(500, 3000), 2)
        foreign_locations = ['Lagos, Nigeria', 'Moscow, Russia', 
                           'Beijing, China', 'Cairo, Egypt', 'Mumbai, India']
        location = random.choice(foreign_locations)
        hour = datetime.utcnow().hour
        is_foreign = True
        
    elif anomaly_type == 'unusual_hour':
        amount = round(random.uniform(100, 1000), 2)
        location = usual_location
        hour = random.choice([1, 2, 3, 4])
        is_foreign = False
        
    elif anomaly_type == 'unusual_category':
        category = 'jewelry'
        merchant = random.choice(MERCHANTS['jewelry'])
        amount = round(random.uniform(1000, 8000), 2)
        location = usual_location
        hour = datetime.utcnow().hour
        is_foreign = False
        
    else:
        amount = round(random.uniform(200, 1000), 2)
        different_locations = [l for l in LOCATIONS if l != usual_location]
        location = random.choice(different_locations)
        hour = datetime.utcnow().hour
        is_foreign = False
    
    return {
        'transaction_id': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat(),
        'customer_id': customer_id,
        'amount': amount,
        'merchant': merchant,
        'merchant_category': category,
        'location': location,
        'hour_of_day': hour,
        'is_foreign_location': is_foreign
    }

def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8')
    )

def main():
    print("Starting Transaction Producer...")
    print(f"Streaming to Kafka topic: {KAFKA_TOPIC}")
    
    producer = create_producer()
    
    # Generate 100 realistic customers with usual locations
    customers = {
        f'CUST_{i:04d}': random.choice(LOCATIONS)
        for i in range(100)
    }
    
    transaction_count = 0
    anomaly_count = 0
    
    try:
        while True:
            customer_id = random.choice(list(customers.keys()))
            usual_location = customers[customer_id]
            
            # 5% of transactions are anomalous
            if random.random() < 0.05:
                transaction = generate_anomalous_transaction(customer_id, usual_location)
                anomaly_count += 1
            else:
                transaction = generate_normal_transaction(customer_id, usual_location)
            
            producer.send(
                KAFKA_TOPIC,
                key=customer_id,
                value=transaction
            )
            
            transaction_count += 1
            
            if transaction_count % 100 == 0:
                print(f"Sent {transaction_count} transactions | "
                      f"Anomalies injected: {anomaly_count} | "
                      f"Rate: ~10 tx/sec")
            
            time.sleep(0.1)  # 10 transactions per second
            
    except KeyboardInterrupt:
        print(f"\nProducer stopped.")
        print(f"Total transactions sent: {transaction_count}")
        print(f"Total anomalies injected: {anomaly_count}")
        producer.close()

if __name__ == "__main__":
    main()
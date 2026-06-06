# 🛡️ Real-Time Financial Fraud Detection Pipeline

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-3.4-black?style=flat-square&logo=apachekafka)
![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-29B5E8?style=flat-square&logo=snowflake)
![OpenAI](https://img.shields.io/badge/GPT--4o%20Mini-AI%20Powered-412991?style=flat-square&logo=openai)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat-square&logo=docker)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit)

---

## The Problem I Wanted to Solve

Most fraud detection systems work in batches — they analyze yesterday's transactions and flag suspicious ones hours after the damage is already done. I wanted to build something that catches fraud **the moment it happens**, not the morning after.

This project is an end-to-end real-time streaming pipeline that processes financial transactions as they arrive, scores each one with a machine learning model in under 100 milliseconds, and when something looks wrong — GPT-4 writes a plain English explanation of exactly why it's suspicious. Everything surfaces on a live dashboard that updates in real time.

I built this from scratch — no tutorials, no copy-paste templates. Every component was designed, debugged and connected manually.

---

## What It Does

Imagine you're a bank processing millions of transactions a day. Your job is to catch the fraudulent ones instantly — before the customer's money is gone. That's the problem this system solves.

A transaction producer simulates a real bank's stream — generating realistic customer transactions with merchant names, locations, amounts and timestamps. 5% of them are secretly anomalous — unusually large amounts, foreign locations, 3am purchases, sudden location switches. These stream into Apache Kafka at 10 transactions per second.

A stream processor sits on top of Kafka and reads every message as it arrives. Each transaction gets passed to an Isolation Forest machine learning model which scores it for anomaly probability in real time. If the model flags it — GPT-4o Mini automatically generates a human-readable explanation of what's suspicious about it. Everything lands in Snowflake. A Streamlit dashboard shows it all live.

---

## Architecture
Transaction Producer (Python + Faker)
↓
Apache Kafka — financial_transactions topic
↓
Stream Processor (Python)
↓
Isolation Forest ML Model (scikit-learn)
↓
/         
Normal       Anomaly
↓               ↓
Snowflake      GPT-4o Mini Explanation
ALL_TXN              ↓
Kafka — anomaly_alerts topic
↓
Snowflake FLAGGED_TRANSACTIONS
↓
Live Streamlit Dashboard

---

## Tech Stack

| Layer | Technology |
|---|---|
| Streaming | Apache Kafka 3.4, Zookeeper |
| ML Model | Isolation Forest (scikit-learn) |
| AI Layer | OpenAI GPT-4o Mini |
| Data Warehouse | Snowflake |
| Dashboard | Streamlit, Plotly |
| Infrastructure | Docker, Docker Compose |
| Language | Python 3.11 |
| Monitoring | Kafka UI, Grafana |

---

## The Dashboard

The Streamlit dashboard is what ties everything together visually. It pulls live from Snowflake and auto-refreshes every 15 seconds showing:

- A live scrolling transaction ticker like a stock market feed
- KPI cards showing total transactions, anomalies detected, average amount and total volume monitored
- A real-time line chart of transaction volume vs anomalies over time
- An anomaly rate gauge that changes color based on threat level
- A breakdown of fraud by merchant category and geographic location
- A live alert feed showing the latest flagged transactions with their AI-generated explanations
- An AI Query Assistant where you type a question in plain English and get a data-powered answer back instantly

---

## How the ML Works

The model is an Isolation Forest — an unsupervised algorithm that learns what normal looks like without needing labeled fraud data. It builds 100 decision trees and scores each transaction based on how easy it is to isolate from the rest. Anomalies are the ones that stand out.

Features used per transaction: amount, hour of day, merchant category, location, and whether it's a foreign location.

Five types of anomalies are injected into the stream to test detection:

1. **Huge amount** — transaction 10x above the category average
2. **Foreign location** — transaction from Lagos, Moscow, Beijing or similar
3. **Unusual hour** — transaction between 1 and 4 AM
4. **Unusual category** — high value jewelry purchase from a customer who never buys jewelry
5. **Location switch** — transaction from a city inconsistent with recent history

---

## What GPT-4 Adds

When Isolation Forest flags a transaction, instead of just showing a score — GPT-4o Mini reads the transaction features and writes a plain English explanation of why it's suspicious. Something like:

*"This $4,847 charge at Kay Jewelers is 340% above this customer's typical spend, and it originated from Lagos, Nigeria — inconsistent with their usual Phoenix, AZ location. The combination of an unusual amount, unfamiliar merchant category and foreign location makes this transaction high risk."*

That's not just a number. That's something a fraud analyst can actually act on.

The dashboard also has an AI Query Assistant. You type a question like "which merchant category has the highest fraud rate today" and it translates that to SQL, queries Snowflake, and returns a human insight — not just a table.

---

## Getting Started

### What You Need
- Python 3.11+
- Docker Desktop
- Snowflake account (free 30-day trial at snowflake.com)
- OpenAI API key (platform.openai.com)

### Setup

```bash
# Clone the repo
git clone https://github.com/devsp18/realtime-fraud-detection.git
cd realtime-fraud-detection

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up credentials
cp config/.env.example config/.env
# Fill in your Snowflake and OpenAI credentials
```

### Start the Infrastructure

```bash
cd docker
docker-compose up -d
```

This starts Kafka on localhost:9092, Kafka UI on localhost:8080, Grafana on localhost:3000 and Zookeeper on localhost:2181.

### Run the Pipeline

You need three terminal windows running simultaneously.

**Terminal 1 — Transaction Producer**
```bash
source venv/bin/activate
cd src/producer
python3.11 transaction_producer.py
```

**Terminal 2 — Stream Processor + ML**
```bash
source venv/bin/activate
cd src/consumer
python3.11 stream_processor.py
```

**Terminal 3 — Dashboard**
```bash
source venv/bin/activate
cd src/dashboard
streamlit run app.py
```

Dashboard is at **http://localhost:8501**
Kafka UI is at **http://localhost:8080**
Grafana is at **http://localhost:3000**

---

## Project Structure
realtime-fraud-detection/
├── src/
│   ├── producer/
│   │   └── transaction_producer.py    # Generates and streams transactions
│   ├── consumer/
│   │   └── stream_processor.py        # Reads stream, runs ML, routes alerts
│   ├── ml/
│   │   └── anomaly_detector.py        # Isolation Forest model
│   ├── ai/
│   │   ├── explanation_engine.py      # GPT-4 fraud explanations
│   │   ├── alert_summarizer.py        # Periodic AI risk summaries
│   │   └── nl_query_interface.py      # Natural language to SQL
│   ├── snowflake/
│   │   └── snowflake_loader.py        # Snowflake writes with auto-reconnect
│   └── dashboard/
│       └── app.py                     # Streamlit live dashboard
├── docker/
│   └── docker-compose.yml             # Full infrastructure setup
├── config/
│   ├── .env                           # Your credentials (never committed)
│   └── .env.example                   # Credential template
└── requirements.txt

---

## Performance

- Throughput: 10 transactions per second (adjustable)
- Anomaly detection latency: under 100ms per transaction
- ML model warmup: 500 synthetic training transactions
- Snowflake writes: under 500ms with automatic reconnection on failure

---

## What I'd Build Next

There's a lot of room to make this more production-grade. A few things on my list:

- Replace the warmup training with a proper offline-trained model saved to disk
- Add LSTM neural network for sequential pattern detection across a customer's transaction history
- MLflow for experiment tracking and model versioning
- FastAPI REST endpoint so other services can call the model directly
- Proper Airflow DAG for scheduled model retraining as new fraud patterns emerge
- Full Docker containerization of the Python services so the whole thing starts with one command

---

## About This Project

I built this because I wanted to work at the intersection of data engineering, machine learning and AI in a way that solves a real problem. Fraud costs the global financial industry over $40 billion a year. Real-time detection matters.

Every component in this system was built from scratch — the Kafka producer, the ML pipeline, the Snowflake integration, the AI explanation layer, the dashboard. It took days of debugging distributed systems, connection timeouts and streaming edge cases. That process taught me more than any course could.

---

## Author

**Satyam Patel**
Business Data Analytics, Minor in Economics — Arizona State University

[LinkedIn](https://linkedin.com/in/patelsatyam18) • [GitHub](https://github.com/devsp18)
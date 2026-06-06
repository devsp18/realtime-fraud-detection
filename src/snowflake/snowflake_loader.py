import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv('../../config/.env')

class SnowflakeLoader:
    def __init__(self):
        self.account = os.getenv('SNOWFLAKE_ACCOUNT')
        self.user = os.getenv('SNOWFLAKE_USER')
        self.password = os.getenv('SNOWFLAKE_PASSWORD')
        self.database = os.getenv('SNOWFLAKE_DATABASE')
        self.schema = os.getenv('SNOWFLAKE_SCHEMA')
        self.warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
        self._connect()

    def _connect(self):
        self.conn = snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            database=self.database,
            schema=self.schema,
            warehouse=self.warehouse,
            network_timeout=30,
            login_timeout=30
        )
        self.cursor = self.conn.cursor()
        print("Connected to Snowflake successfully.")

    def _reconnect(self):
        try:
            self.cursor.close()
            self.conn.close()
        except:
            pass
        self._connect()

    def insert_transaction(self, transaction: dict):
        try:
            self.cursor.execute("""
                INSERT INTO FRAUD_DETECTION.TRANSACTIONS.ALL_TRANSACTIONS (
                    TRANSACTION_ID, TIMESTAMP, AMOUNT, MERCHANT,
                    MERCHANT_CATEGORY, LOCATION, CUSTOMER_ID,
                    ANOMALY_SCORE, IS_ANOMALY
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction.get('transaction_id'),
                transaction.get('timestamp'),
                transaction.get('amount'),
                transaction.get('merchant'),
                transaction.get('merchant_category'),
                transaction.get('location'),
                transaction.get('customer_id'),
                transaction.get('anomaly_score', 0),
                transaction.get('is_anomaly', False)
            ))
        except Exception as e:
            print(f"Reconnecting to Snowflake...")
            self._reconnect()

    def insert_flagged_transaction(self, transaction: dict):
        try:
            self.cursor.execute("""
                INSERT INTO FRAUD_DETECTION.TRANSACTIONS.FLAGGED_TRANSACTIONS (
                    TRANSACTION_ID, TIMESTAMP, AMOUNT, MERCHANT,
                    MERCHANT_CATEGORY, LOCATION, CUSTOMER_ID,
                    ANOMALY_SCORE, IS_ANOMALY, AI_EXPLANATION
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction.get('transaction_id'),
                transaction.get('timestamp'),
                transaction.get('amount'),
                transaction.get('merchant'),
                transaction.get('merchant_category'),
                transaction.get('location'),
                transaction.get('customer_id'),
                transaction.get('anomaly_score', 0),
                transaction.get('is_anomaly', False),
                transaction.get('ai_explanation', '')
            ))
        except Exception as e:
            print(f"Reconnecting to Snowflake...")
            self._reconnect()

    def close(self):
        self.cursor.close()
        self.conn.close()
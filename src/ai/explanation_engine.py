import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('../../config/.env')

class ExplanationEngine:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"

    def explain(self, transaction: dict) -> str:
        try:
            prompt = f"""You are a fraud analyst AI. Analyze this flagged transaction and explain in 2 sentences why it is suspicious.

Transaction Details:
- Customer ID: {transaction.get('customer_id')}
- Amount: ${transaction.get('amount')}
- Merchant: {transaction.get('merchant')}
- Category: {transaction.get('merchant_category')}
- Location: {transaction.get('location')}
- Time (hour): {transaction.get('hour_of_day')}
- Foreign Location: {transaction.get('is_foreign_location')}
- Anomaly Score: {transaction.get('anomaly_score', 0):.4f}

Be specific about what makes this transaction suspicious. Keep it concise and professional."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Anomaly detected with score {transaction.get('anomaly_score', 0):.4f}. Manual review required."
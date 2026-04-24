from fastapi import FastAPI
from kafka import KafkaProducer
import valkey.asyncio as valkey
import os

# OpenTelemetry Imports
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

# Configuration from Environment Variables
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka-service.app.svc.cluster.local:9092")
VALKEY_URL = os.getenv("VALKEY_URL", "redis://valkey:6379")

# Clients
v_client = valkey.from_url(VALKEY_URL)
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

@app.post("/send")
async def send_data(data: dict):
    # 1. Update state in Valkey
    msg_id = data.get("id", "unknown")
    await v_client.set(f"msg:{msg_id}", "processed")
    
    # 2. Push to Kafka
    producer.send('app-topic', value=str(data).encode())
    
    return {"status": "success", "id": msg_id}

# This line enables automatic tracing for all FastAPI routes
FastAPIInstrumentor.instrument_app(app)
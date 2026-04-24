from fastapi import FastAPI
from kafka import KafkaProducer
import redis.asyncio as redis
import os
import json

# OpenTelemetry Imports
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

# Configuration from Environment Variables
# These should match your Service names in Kubernetes
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka-service.app.svc.cluster.local:9092")
VALKEY_URL = os.getenv("VALKEY_URL", "redis://valkey:6379")

# Initialize Clients
# redis.from_url works perfectly with Valkey
v_client = redis.from_url(VALKEY_URL, decode_responses=True)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/send")
async def send_data(data: dict):
    """
    1. Receives JSON data
    2. Sets a status key in Valkey
    3. Pushes the message to Kafka
    """
    msg_id = data.get("id", "unknown")
    
    # 1. Update state in Valkey
    await v_client.set(f"msg:{msg_id}", "processed")
    
    # 2. Push to Kafka
    producer.send('app-topic', value=data)
    producer.flush()
    
    return {
        "status": "success", 
        "id": msg_id, 
        "storage": "valkey",
        "queue": "kafka"
    }

# Enable automatic tracing for all FastAPI routes
FastAPIInstrumentor.instrument_app(app)
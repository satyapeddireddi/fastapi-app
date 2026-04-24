import time
import json
import os
from fastapi import FastAPI
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import redis.asyncio as redis

app = FastAPI()

KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka-service:9092")
VALKEY_URL = os.getenv("VALKEY_URL", "redis://valkey:6379")

# Async Client for Valkey
v_client = redis.from_url(VALKEY_URL, decode_responses=True)

# Robust Kafka Producer Initialization
producer = None
print(f"Connecting to Kafka at {KAFKA_SERVER}...")

for i in range(20):  # Try for ~100 seconds
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=10000  # Give it time to respond
        )
        print("Successfully connected to Kafka!")
        break
    except NoBrokersAvailable:
        print(f"Kafka not ready yet (attempt {i+1}/20)... waiting 5s")
        time.sleep(5)

if not producer:
    print("Failed to connect to Kafka after multiple attempts. Exiting.")
    exit(1)

@app.post("/send")
async def send_data(data: dict):
    msg_id = data.get("id", "unknown")
    await v_client.set(f"msg:{msg_id}", "processed")
    producer.send('app-topic', value=data)
    return {"status": "success", "id": msg_id}
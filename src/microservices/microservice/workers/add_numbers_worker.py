"""
Add Numbers worker for MassTransit/RabbitMQ.
Consumes AddNumbersCommand messages, computes sum, and publishes AddNumbersResult responses.
"""

import os
import sys
import json
import uuid
import datetime
import pika

# RabbitMQ connection settings from environment
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

# Stable worker queue name provided by orchestrator (Aspire) via env var
WORKER_QUEUE = os.getenv('WORKER_QUEUE', 'hackathon.add-numbers')


def callback(ch, method, properties, body):
    """Process AddNumbersCommand and publish AddNumbersResult"""
    try:
        message = json.loads(body)
        print(f"[RECV] Received message: {json.dumps(message, indent=2)[:500]}...")

        # MassTransit wraps the payload in 'message'
        command = message.get('message', message)

        a = command.get('a', command.get('A', 0))
        b = command.get('b', command.get('B', 0))

        print(f"[PROC] Computing {a} + {b}")
        result_sum = a + b

        # Determine reply queue
        reply_routing_key = properties.reply_to
        if not reply_routing_key:
            resp_addr = message.get('responseAddress') or message.get('response_address')
            if isinstance(resp_addr, str) and '/' in resp_addr:
                reply_routing_key = resp_addr.rsplit('/', 1)[-1]
                if '?' in reply_routing_key:
                    reply_routing_key = reply_routing_key.split('?', 1)[0]
        if not reply_routing_key:
            raise Exception("Unable to determine reply queue (no reply_to and no responseAddress)")

        print(f"[SEND] Replying to queue: {reply_routing_key}")

        corr_id = (properties.correlation_id
                   or message.get('correlationId')
                   or message.get('requestId')
                   or str(uuid.uuid4()))

        # Create response in MassTransit envelope format
        response_envelope = {
            "messageId": str(uuid.uuid4()),
            "requestId": corr_id,
            "correlationId": corr_id,
            "conversationId": message.get("conversationId"),
            "sourceAddress": f"rabbitmq://{RABBITMQ_HOST}/{WORKER_QUEUE}",
            "destinationAddress": f"rabbitmq://{RABBITMQ_HOST}/{reply_routing_key}",
            "messageType": [
                "urn:message:Hackathon.Domain.Messages:AddNumbersResult"
            ],
            "message": {
                "sum": result_sum
            },
            "sentTime": datetime.datetime.utcnow().isoformat() + "Z"
        }

        ch.basic_publish(
            exchange='',
            routing_key=reply_routing_key,
            properties=pika.BasicProperties(
                correlation_id=corr_id,
                content_type='application/vnd.masstransit+json'
            ),
            body=json.dumps(response_envelope)
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[OK] Result: {a} + {b} = {result_sum}")

    except Exception as e:
        print(f"[ERROR] Error processing AddNumbers request: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    """Start the Add Numbers worker"""
    print("Add Numbers Worker starting...")
    print(f"   RabbitMQ Host: {RABBITMQ_HOST}")
    print(f"   RabbitMQ Port: {RABBITMQ_PORT}")
    print(f"   RabbitMQ User: {RABBITMQ_USER}")
    print(f"   Queue: {WORKER_QUEUE}")

    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )
        channel = connection.channel()
        print("[OK] Connected to RabbitMQ successfully")
    except Exception as e:
        print(f"[ERROR] Failed to connect to RabbitMQ: {e}")
        import traceback
        traceback.print_exc()
        return

    # Declare durable worker queue
    channel.queue_declare(queue=WORKER_QUEUE, durable=True)

    # Process one message at a time
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=WORKER_QUEUE,
        on_message_callback=callback
    )

    print(f"[OK] Add Numbers Worker ready. Waiting for messages on '{WORKER_QUEUE}'...")
    print("   Press Ctrl+C to exit")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down Add Numbers Worker...")
        channel.stop_consuming()

    connection.close()
    print("[STOP] Add Numbers Worker stopped")


if __name__ == '__main__':
    try:
        print("=" * 60)
        print("ADD NUMBERS WORKER STARTING")
        print("=" * 60)
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        print("=" * 60)
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

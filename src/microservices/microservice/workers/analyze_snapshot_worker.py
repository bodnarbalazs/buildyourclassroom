"""
Analyze Snapshot worker for MassTransit/RabbitMQ.
Consumes AnalyzeSnapshotCommand messages (session_id + base64 image),
runs emotion analysis, saves to DB, and publishes AnalyzeSnapshotResult responses.
"""

import asyncio
import base64
import datetime
import json
import os
import sys
import uuid

import pika

from services.emotion_analyzer import EmotionAnalyzer
from services.emotion_repository import EmotionRepository
from shared.database import get_database_url

# RabbitMQ connection settings from environment
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

# Stable worker queue name provided by orchestrator (Aspire) via env var
WORKER_QUEUE = os.getenv('WORKER_QUEUE', 'hackathon.analyze-snapshot')

_analyzer = EmotionAnalyzer()

# Async DB access from a sync pika callback via a dedicated event loop
_loop = asyncio.new_event_loop()


def _init_db():
    """Create the async engine and session factory once at startup."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    url = get_database_url()
    engine = create_async_engine(url, echo=False, pool_size=5, max_overflow=10)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _save_snapshot(session_factory, session_id, faces, processing_ms):
    """Run the repository save inside a proper async session."""
    async with session_factory() as db:
        repo = EmotionRepository(db)
        session = await repo.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        if session.ended_at:
            raise ValueError(f"Session {session_id} already ended")
        snapshot = await repo.save_snapshot(
            session_id=session_id,
            faces=faces,
            processing_ms=processing_ms,
        )
        return snapshot


def _build_snapshot_response(snapshot):
    """Serialize snapshot ORM object to a dict for the MassTransit envelope."""
    return {
        "snapshotId": str(snapshot.id),
        "sessionId": str(snapshot.session_id),
        "capturedAt": snapshot.captured_at.isoformat(),
        "faceCount": snapshot.face_count,
        "processingMs": snapshot.processing_ms,
        "faces": [
            {
                "faceIndex": fr.face_index,
                "bbox": {"x": fr.bbox_x, "y": fr.bbox_y, "w": fr.bbox_w, "h": fr.bbox_h},
                "dominantEmotion": fr.dominant_emotion,
                "emotionScores": fr.emotion_scores,
                "engagementLevel": fr.engagement_level,
                "engagementScore": fr.engagement_score,
            }
            for fr in snapshot.face_results
        ],
    }


def make_callback(session_factory):
    """Create the message callback with a captured DB session factory."""

    def callback(ch, method, properties, body):
        """Process AnalyzeSnapshotCommand and publish AnalyzeSnapshotResult."""
        try:
            message = json.loads(body)
            print(f"[RECV] Received AnalyzeSnapshot command")

            command = message.get('message', message)

            session_id_raw = command.get('sessionId') or command.get('session_id')
            image_b64 = command.get('imageBase64') or command.get('image_base64')

            if not session_id_raw or not image_b64:
                raise ValueError("Missing sessionId or imageBase64 in command")

            session_id = uuid.UUID(str(session_id_raw))
            image_bytes = base64.b64decode(image_b64)
            print(f"[PROC] Analyzing image ({len(image_bytes)} bytes) for session {session_id}")

            # CPU-bound emotion analysis (synchronous)
            result = _analyzer.analyze_image(image_bytes)
            print(f"[PROC] Found {len(result.faces)} faces in {result.processing_ms}ms")

            # Persist to database
            snapshot = _loop.run_until_complete(
                _save_snapshot(session_factory, session_id, result.faces, result.processing_ms)
            )
            print(f"[PROC] Saved snapshot {snapshot.id}")

            # Determine reply queue
            reply_routing_key = properties.reply_to
            if not reply_routing_key:
                resp_addr = message.get('responseAddress') or message.get('response_address')
                if isinstance(resp_addr, str) and '/' in resp_addr:
                    reply_routing_key = resp_addr.rsplit('/', 1)[-1]
                    if '?' in reply_routing_key:
                        reply_routing_key = reply_routing_key.split('?', 1)[0]
            if not reply_routing_key:
                raise ValueError("Unable to determine reply queue")

            corr_id = (
                properties.correlation_id
                or message.get('correlationId')
                or message.get('requestId')
                or str(uuid.uuid4())
            )

            response_envelope = {
                "messageId": str(uuid.uuid4()),
                "requestId": corr_id,
                "correlationId": corr_id,
                "conversationId": message.get("conversationId"),
                "sourceAddress": f"rabbitmq://{RABBITMQ_HOST}/{WORKER_QUEUE}",
                "destinationAddress": f"rabbitmq://{RABBITMQ_HOST}/{reply_routing_key}",
                "messageType": [
                    "urn:message:Hackathon.Domain.Messages:AnalyzeSnapshotResult"
                ],
                "message": _build_snapshot_response(snapshot),
                "sentTime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

            ch.basic_publish(
                exchange='',
                routing_key=reply_routing_key,
                properties=pika.BasicProperties(
                    correlation_id=corr_id,
                    content_type='application/vnd.masstransit+json',
                ),
                body=json.dumps(response_envelope),
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"[OK] Snapshot analyzed: {len(result.faces)} faces, {result.processing_ms}ms")

        except Exception as e:
            print(f"[ERROR] Error processing AnalyzeSnapshot: {e}")
            import traceback
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    return callback


def main():
    """Start the Analyze Snapshot worker."""
    print("Analyze Snapshot Worker starting...")
    print(f"   RabbitMQ Host: {RABBITMQ_HOST}")
    print(f"   RabbitMQ Port: {RABBITMQ_PORT}")
    print(f"   RabbitMQ User: {RABBITMQ_USER}")
    print(f"   Queue: {WORKER_QUEUE}")

    print("[INIT] Warming up emotion model...")
    _analyzer.warm_up()
    print("[OK] Emotion model ready")

    print("[INIT] Initializing database...")
    session_factory = _init_db()
    print("[OK] Database ready")

    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
        )
        channel = connection.channel()
        print("[OK] Connected to RabbitMQ successfully")
    except Exception as e:
        print(f"[ERROR] Failed to connect to RabbitMQ: {e}")
        import traceback
        traceback.print_exc()
        return

    channel.queue_declare(queue=WORKER_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=WORKER_QUEUE, on_message_callback=make_callback(session_factory))

    print(f"[OK] Analyze Snapshot Worker ready. Waiting for messages on '{WORKER_QUEUE}'...")
    print("   Press Ctrl+C to exit")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down Analyze Snapshot Worker...")
        channel.stop_consuming()

    connection.close()
    _loop.close()
    print("[STOP] Analyze Snapshot Worker stopped")


if __name__ == '__main__':
    try:
        print("=" * 60)
        print("ANALYZE SNAPSHOT WORKER STARTING")
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

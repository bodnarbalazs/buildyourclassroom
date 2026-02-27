"""Shared fixtures for worker callback tests."""

import json
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_channel():
    """Pre-configured mock pika channel."""
    ch = MagicMock()
    ch.basic_publish.return_value = None
    ch.basic_ack.return_value = None
    ch.basic_nack.return_value = None
    return ch


@pytest.fixture
def mock_method():
    """Mock delivery method with delivery_tag."""
    method = MagicMock()
    method.delivery_tag = 42
    return method


@pytest.fixture
def mock_properties():
    """Mock BasicProperties with reply_to and correlation_id."""
    props = MagicMock()
    props.reply_to = "reply-queue"
    props.correlation_id = "corr-123"
    props.headers = {}
    return props


def make_envelope(message_type: str, body: dict) -> bytes:
    """Build a MassTransit JSON envelope."""
    return json.dumps({
        "messageType": [f"urn:message:{message_type}"],
        "message": body,
        "conversationId": "conv-001",
    }).encode()

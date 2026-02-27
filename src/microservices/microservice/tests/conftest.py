"""Shared test fixtures."""
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def app():
    from api.main import app as real_app
    return real_app


@pytest.fixture
def client(app):
    return TestClient(app)

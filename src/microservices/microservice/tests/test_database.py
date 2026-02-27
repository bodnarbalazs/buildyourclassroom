"""Tests for shared/database.py connection string parsing."""
from shared.database import parse_npgsql_connection_string


def test_standard_connection_string():
    npgsql = "Host=myhost;Port=5433;Database=mydb;Username=admin;Password=secret123"
    url = parse_npgsql_connection_string(npgsql)
    assert url == "postgresql+asyncpg://admin:secret123@myhost:5433/mydb"


def test_defaults_when_fields_missing():
    url = parse_npgsql_connection_string("")
    assert url == "postgresql+asyncpg://postgres:@localhost:5432/hackathondb"


def test_case_insensitive_keys():
    npgsql = "host=h;PORT=1234;database=d;username=u;password=p"
    url = parse_npgsql_connection_string(npgsql)
    assert url == "postgresql+asyncpg://u:p@h:1234/d"


def test_extra_whitespace():
    npgsql = " Host = srv ; Port = 5432 ; Database = db ; Username = user ; Password = pw "
    url = parse_npgsql_connection_string(npgsql)
    assert url == "postgresql+asyncpg://user:pw@srv:5432/db"


def test_password_with_special_chars():
    npgsql = "Host=h;Port=5432;Database=d;Username=u;Password=p@ss=w0rd;extra"
    url = parse_npgsql_connection_string(npgsql)
    assert "p@ss=w0rd" in url

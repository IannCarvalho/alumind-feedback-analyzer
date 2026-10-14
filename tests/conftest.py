"""Shared pytest fixtures and environment setup.

A dummy OPENAI_API_KEY is set before any app import because FeedbackAnalyzer
validates the key at construction time and the api blueprint builds one at
import time. Tests here are unit-level and do not touch a real database — the
models use the PostgreSQL UUID type, which does not run on SQLite, so DB-backed
integration tests are intentionally out of scope for this suite.
"""
import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

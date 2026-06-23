"""
Database + caching layer.

Cached results are served instantly on repeat queries. The freshness
factor in the confidence formula decays based on how old a cached
record is (see Section 8 of the build plan) — old cache entries don't
get thrown away, they just count for less until a fresh scrape replaces them.
"""
import json
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class CachedSearch(Base):
    __tablename__ = "cached_searches"
    query_key = Column(String, primary_key=True)
    result_json = Column(Text, nullable=False)
    cached_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


def normalize_query_key(query: str) -> str:
    return query.strip().lower()


def get_cached_result(query: str):
    session = SessionLocal()
    try:
        row = session.get(CachedSearch, normalize_query_key(query))
        if not row:
            return None, None
        age_days = (datetime.utcnow() - row.cached_at).days
        return json.loads(row.result_json), age_days
    finally:
        session.close()


def save_cached_result(query: str, result_dict: dict):
    session = SessionLocal()
    try:
        key = normalize_query_key(query)
        row = session.get(CachedSearch, key)
        payload = json.dumps(result_dict, default=str)
        if row:
            row.result_json = payload
            row.cached_at = datetime.utcnow()
        else:
            row = CachedSearch(query_key=key, result_json=payload, cached_at=datetime.utcnow())
            session.add(row)
        session.commit()
    finally:
        session.close()


def freshness_factor(age_days: int | None) -> float:
    if age_days is None:
        return 1.0
    if age_days < 7:
        return 1.0
    if age_days < 30:
        return 0.9
    if age_days < 90:
        return 0.75
    return 0.5

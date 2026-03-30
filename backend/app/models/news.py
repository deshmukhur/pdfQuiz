"""News article model."""

from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from app.models.base import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    headline = Column(Text, nullable=False)
    source = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    url = Column(Text, nullable=True)
    related_symbols = Column(ARRAY(Text), nullable=True)
    sentiment_score = Column(Numeric, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

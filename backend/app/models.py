from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base, now_utc  # use our UTC helper

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True)
    contact_name = Column(String, index=True)
    email = Column(String, index=True)
    title = Column(String)
    website = Column(String)
    notes = Column(Text, default="")
    score = Column(Float, default=0.0)
    stage = Column(String, default="new")  # new -> qualified -> contacted -> meeting -> won/lost
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc)

    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="lead", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    role = Column(String)  # user/assistant/system
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    lead = relationship("Lead", back_populates="messages")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    type = Column(String)        # created, scored, messaged, stage_change, meeting
    detail = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    lead = relationship("Lead", back_populates="activities")

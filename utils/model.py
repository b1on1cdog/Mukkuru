# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
""" SQLite model classes
This module should NOT import other Mukkuru modules (Exception: database.py).\n
"""
import uuid
from sqlalchemy import Column, Integer, String, Float#, create_engine
from sqlalchemy import Text, CheckConstraint, JSON
from sqlalchemy.ext.mutable import MutableDict

#from sqlalchemy.orm import relationship
from utils.database import Base
import json

class Game(Base):
    ''' Stores game information '''
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    app_id = Column(String, nullable= False)
    AppName = Column(String, nullable=False)
    Exe = Column(String, nullable=False)
    Source = Column(String, nullable=False)
    Type = Column(String, nullable=False)
    Extra = Column(MutableDict.as_mutable(JSON), nullable=True)

class Video(Base):
    ''' Stores video information '''
    __tablename__ = "videos"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(64), nullable=False)
    path = Column(String(1024), nullable=False)
    file = Column(String(1024), nullable=False)
    url = Column(String(512), nullable=False)
    resume = Column(Float, default=0.0)
    thumbnail = Column(String(1024), nullable=True) # thumbnail path
    thumbnail_url = Column(String(512), nullable=True)

class Config(Base):
    ''' Stores Mukkuru settings '''
    __tablename__ = "config"
    id = Column(Integer, primary_key=True)
    config_raw = Column("config", Text, CheckConstraint("json_valid(config)"))

    @property
    def config(self):
        return json.loads(self.config_raw) if self.config_raw else {}

    @config.setter
    def config(self, value):
        self.config_raw = json.dumps(value)

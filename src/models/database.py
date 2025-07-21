"""
Database models for construction estimation project management
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

Base = declarative_base()


class Project(Base):
    """Project model for construction estimation"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Project-wide defaults (stored as JSON for flexibility)
    default_finishes = Column(JSON)  # flooring, wall_finish, ceiling_finish
    default_trim = Column(JSON)      # baseboard, quarter_round, crown_molding
    
    # Relationships
    floors = relationship("Floor", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class Floor(Base):
    """Floor model (ground_floor, second_floor, etc.)"""
    __tablename__ = 'floors'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    name = Column(String(100), nullable=False)  # ground_floor, second_floor
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="floors")
    rooms = relationship("Room", back_populates="floor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Floor(id={self.id}, name='{self.name}')>"


class Room(Base):
    """Room model with measurements from YAML"""
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    floor_id = Column(Integer, ForeignKey('floors.id'), nullable=False)
    name = Column(String(100), nullable=False)
    
    # Measurements from YAML
    dimensions = Column(String(100))  # "7' 11\" x 5' 3 3/4\""
    ceiling_height = Column(String(20))  # "7'"
    
    # Measurement data (stored as JSON for flexibility)
    measurements = Column(JSON)  # volume, surfaces, perimeters
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    floor = relationship("Floor", back_populates="rooms")
    work_scope = relationship("WorkScope", back_populates="room", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Room(id={self.id}, name='{self.name}')>"


class WorkScope(Base):
    """Work scope for each room"""
    __tablename__ = 'work_scopes'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    
    # Use project defaults flag
    use_project_defaults = Column(Boolean, default=True)
    
    # Override finishes (if not using defaults)
    flooring_override = Column(String(100))
    wall_finish_override = Column(String(100))
    ceiling_finish_override = Column(String(100))
    
    # Override trim (stored as JSON)
    trim_overrides = Column(JSON)
    
    # Paint scope
    paint_scope = Column(String(50))  # walls_only, ceiling_only, both, none
    
    # Demo'd scope (already demolished) - stored as JSON
    demod_scope = Column(JSON)
    
    # Removal scope (to be demolished) - stored as JSON
    removal_scope = Column(JSON)
    
    # Specific tasks (stored as JSON arrays)
    remove_replace_items = Column(JSON)
    detach_reset_items = Column(JSON)
    protection_items = Column(JSON)
    
    # General notes
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room = relationship("Room", back_populates="work_scope")
    
    def __repr__(self):
        return f"<WorkScope(id={self.id}, room_id={self.room_id})>"


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str = None):
        """Initialize database connection"""
        if database_url is None:
            # Default to SQLite in data directory
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
            os.makedirs(data_dir, exist_ok=True)
            database_url = f"sqlite:///{os.path.join(data_dir, 'construction_estimation.db')}"
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()


# Global database manager instance
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get or create database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session():
    """Get database session"""
    return get_db_manager().get_session()
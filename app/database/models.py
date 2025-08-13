"""
Modelos SQLAlchemy para o banco de dados do Mídia Church
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    role = Column(String(20), default='member')
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    created_events = relationship("Event", back_populates="creator")
    attendance_records = relationship("Attendance", back_populates="user")
    uploaded_media = relationship("MediaContent", back_populates="uploader")
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    assigned_routines = relationship("Routine", foreign_keys="Routine.assigned_to", back_populates="assignee")
    created_routines = relationship("Routine", foreign_keys="Routine.created_by", back_populates="creator")
    ai_conversations = relationship("AIConversation", back_populates="user")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(50), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    location = Column(String(200))
    max_attendees = Column(Integer, default=0)
    requires_registration = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    creator = relationship("User", back_populates="created_events")
    attendance_records = relationship("Attendance", back_populates="event")

class Attendance(Base):
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    present = Column(Boolean, default=False)
    check_in_time = Column(DateTime)
    notes = Column(Text)
    
    # Relacionamentos
    event = relationship("Event", back_populates="attendance_records")
    user = relationship("User", back_populates="attendance_records")

class MediaContent(Base):
    __tablename__ = 'media_content'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    category = Column(String(100))
    tags = Column(Text)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    uploaded_at = Column(DateTime, default=func.now())
    file_size = Column(Integer)
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    uploader = relationship("User", back_populates="uploaded_media")

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(String(50), default='announcement')
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_pinned = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")

class Routine(Base):
    __tablename__ = 'routines'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    frequency = Column(String(50), nullable=False)
    assigned_to = Column(Integer, ForeignKey('users.id'))
    due_date = Column(Date)
    completed = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_routines")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_routines")

class AIConversation(Base):
    __tablename__ = 'ai_conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    user = relationship("User", back_populates="ai_conversations")

class SecurityLog(Base):
    __tablename__ = 'security_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    user_id = Column(String(50))
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=func.now())

class SystemSetting(Base):
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=func.now())

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    recipient_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default='notification')
    sent_at = Column(DateTime, default=func.now())
    read_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")

class MeetingReport(Base):
    __tablename__ = 'meeting_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    title = Column(String(200), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    participants = Column(Text)  # JSON string
    decisions = Column(Text)
    action_items = Column(Text)  # JSON string
    next_steps = Column(Text)
    status = Column(String(20), default='draft')
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    event = relationship("Event")
    creator = relationship("User")

class ReportTemplate(Base):
    __tablename__ = 'report_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    creator = relationship("User")
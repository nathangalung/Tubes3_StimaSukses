# Defines database table models.

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Date
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ApplicantProfile(Base):
    """Applicant personal information table."""
    __tablename__ = 'applicant_profile'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    phone = Column(String(50))
    address = Column(Text)
    linkedin_url = Column(String(255))
    # Add other personal info fields

    applications = relationship("ApplicationDetail", back_populates="applicant")

    def __repr__(self):
        return f"<ApplicantProfile(id={self.id}, name='{self.name}')>"

class ApplicationDetail(Base):
    """Application details and CV path."""
    __tablename__ = 'application_detail'

    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(Integer, ForeignKey('applicant_profile.id'), nullable=False)
    cv_path = Column(String(255), nullable=False) # Path to CV file
    application_date = Column(Date)
    job_position = Column(String(255))
    # Add other application specific fields

    # Extracted CV information (can be stored here or processed on-demand)
    # These fields would be populated by regex_extractor
    summary_overview = Column(Text)
    skills = Column(Text) # Could be comma-separated or JSON
    work_experience = Column(Text) # Could be JSON
    education_history = Column(Text) # Could be JSON

    applicant = relationship("ApplicantProfile", back_populates="applications")

    def __repr__(self):
        return f"<ApplicationDetail(id={self.id}, applicant_id={self.applicant_id}, cv_path='{self.cv_path}')>"

# Example: To create tables in a SQLite DB (for simplicity here)
# from .config import DATABASE_URL # Assuming config.py has DATABASE_URL
# engine = create_engine(DATABASE_URL) # e.g., 'mysql+mysqlconnector://user:password@host/db_name'
# Base.metadata.create_all(engine)
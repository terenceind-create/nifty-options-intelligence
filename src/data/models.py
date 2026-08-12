# src/data/models.py
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import settings

Base = declarative_base()

class OptionsTick(Base):
    """Options data storage"""
    __tablename__ = 'options_ticks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    spot_price = Column(Float)
    atm_strike = Column(Integer)
    days_to_expiry = Column(Integer)
    
    ce_ltp = Column(Float)
    ce_bid = Column(Float)
    ce_ask = Column(Float)
    ce_oi = Column(Integer)
    ce_oi_change = Column(Integer)
    ce_volume = Column(Integer)
    ce_iv = Column(Float)
    ce_delta = Column(Float)
    ce_gamma = Column(Float)
    ce_theta = Column(Float)
    ce_vega = Column(Float)
    
    pe_ltp = Column(Float)
    pe_bid = Column(Float)
    pe_ask = Column(Float)
    pe_oi = Column(Integer)
    pe_oi_change = Column(Integer)
    pe_volume = Column(Integer)
    pe_iv = Column(Float)
    pe_delta = Column(Float)
    pe_gamma = Column(Float)
    pe_theta = Column(Float)
    pe_vega = Column(Float)
    
    pcr = Column(Float)
    is_expiry_day = Column(Boolean, default=False)

class FII_DII_Data(Base):
    """FII/DII daily data"""
    __tablename__ = 'fii_dii_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, index=True)
    fii_net = Column(Float)
    dii_net = Column(Float)

# Create engine and tables
engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_db_session():
    """Get database session"""
    return SessionLocal()
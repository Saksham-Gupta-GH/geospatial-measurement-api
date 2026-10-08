from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class GeoFile(Base):
    __tablename__ = "geofiles"
    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    feature_count = Column(Integer)
    crs = Column(String)
    status = Column(String)
    
    features = relationship("Feature", back_populates="file")

class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("geofiles.id"))
    feature_index = Column(Integer)
    geom_type = Column(String)
    geometry_wkt = Column(String)
    properties = Column(JSON)
    measurement = Column(Float, nullable=True) # Area or Length
    
    file = relationship("GeoFile", back_populates="features")

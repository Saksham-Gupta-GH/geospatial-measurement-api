import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from geo_utils import process_file

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Geospatial File Measurement API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/files/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith('.zip') or file.filename.endswith('.kml')):
        raise HTTPException(status_code=400, detail="Only .zip (Shapefile) and .kml files are supported.")
        
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    db_file = models.GeoFile(
        id=file_id, 
        filename=file.filename, 
        status="PROCESSING",
        feature_count=0,
        crs="Unknown"
    )
    db.add(db_file)
    db.commit()
    
    try:
        crs, feature_count, features_list = process_file(file_path, file.filename)
        
        db_file.crs = crs
        db_file.feature_count = feature_count
        db_file.status = "COMPLETED"
        
        for feat in features_list:
            db_feat = models.Feature(
                file_id=file_id,
                feature_index=feat["feature_index"],
                geom_type=feat["geom_type"],
                geometry_wkt=feat["geometry_wkt"],
                properties=feat["properties"],
                measurement=feat["measurement"]
            )
            db.add(db_feat)
            
        db.commit()
    except Exception as e:
        db_file.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            
    return {"id": file_id, "status": db_file.status}

@app.get("/api/files/{file_id}/")
def get_file_info(file_id: str, db: Session = Depends(get_db)):
    db_file = db.query(models.GeoFile).filter(models.GeoFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "feature_count": db_file.feature_count,
        "crs": db_file.crs,
        "status": db_file.status
    }

@app.get("/api/files/{file_id}/measurements/")
def get_measurements(file_id: str, db: Session = Depends(get_db)):
    db_file = db.query(models.GeoFile).filter(models.GeoFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    if db_file.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="File processing is not completed.")
        
    features = db.query(models.Feature).filter(models.Feature.file_id == file_id).all()
    
    results = [{"feature_index": f.feature_index, "geometry_type": f.geom_type, "properties": f.properties, "measurement": f.measurement} for f in features]
        
    return {"file_id": file_id, "measurements": results}

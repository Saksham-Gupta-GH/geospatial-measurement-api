# Geospatial File Measurement API

A backend service built with FastAPI that accepts geospatial files (Shapefile in `.zip` or `.kml`), extracts their features, and calculates geographic measurements (Area for Polygons, Length for LineStrings).

## Setup Instructions

1. **Clone the repository**
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`. You can view the interactive Swagger UI at `http://localhost:8000/docs`.

## API Documentation

### 1. Upload File
**Endpoint**: `POST /api/files/`
- **Description**: Uploads and processes a geospatial file (`.zip` containing a Shapefile, or `.kml`).
- **Body**: `multipart/form-data` with key `file`.
- **Response**:
  ```json
  {
      "id": "uuid-string",
      "status": "COMPLETED"
  }
  ```

### 2. File Information
**Endpoint**: `GET /api/files/{id}/`
- **Description**: Returns information about the uploaded file.
- **Response**:
  ```json
  {
      "id": "uuid-string",
      "filename": "survey.kml",
      "feature_count": 120,
      "crs": "EPSG:4326",
      "status": "COMPLETED"
  }
  ```

### 3. Measurements
**Endpoint**: `GET /api/files/{id}/measurements/`
- **Description**: Returns the extracted features, their properties, and calculated measurements (area in square meters for polygons, length in meters for lines).
- **Response**:
  ```json
  {
      "file_id": "uuid-string",
      "measurements": [
          {
              "feature_index": 0,
              "geometry_type": "Polygon",
              "properties": {"name": "Zone A"},
              "measurement": 15423.5
          }
      ]
  }
  ```

## Architecture & Design Decisions

- **Framework**: **FastAPI** was chosen for its high performance, automatic OpenAPI documentation generation, and modern async support.
- **Database**: SQLite (via SQLAlchemy ORM) is used to store file metadata and feature measurements, keeping the application portable and easy to run without external database dependencies.
- **File Processing Flow**: Files are saved to a temporary `uploads/` directory. If a `.zip` is detected, it is extracted into a temporary directory to locate the `.shp` file. `fiona` is configured to enable KML driver support.
- **CRS Handling & Measurement Calculation**: 
  - To calculate accurate areas and distances in meters, geographic coordinates (like EPSG:4326) cannot be used directly. 
  - The application uses `geopandas.GeoDataFrame.estimate_utm_crs()` to dynamically project the geometry into the most appropriate local UTM zone based on its bounds. If that fails, it falls back to a global Equal Area projection.
  - Polygons yield `area` (m²), LineStrings yield `length` (m), and Points yield `0.0`. Unsupported geometries are ignored gracefully during processing.

## Learning and Future Scope
- **Learning**: Gained deeper experience in robust CRS projection strategies for dynamic datasets, particularly utilizing local UTM zones to minimize measurement distortion without hardcoding a specific EPSG.
- **Future Scope**: 
  1. Offload file processing to a background worker (e.g., Celery or FastAPI BackgroundTasks) so the API can return a job ID instantly for massive files.
  2. Add support for GeoJSON and direct PostGIS integration for scalable spatial querying.

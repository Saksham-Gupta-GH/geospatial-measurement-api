import os
import zipfile
import tempfile
import geopandas as gpd
import fiona

# Enable KML support in fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

def process_file(filepath: str, filename: str):
    ext = filename.lower().split('.')[-1]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = filepath
        if ext == 'zip':
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            
            shp_files = []
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    if f.endswith('.shp'):
                        shp_files.append(os.path.join(root, f))
            if not shp_files:
                raise ValueError("No .shp file found in the zip archive.")
            target_path = shp_files[0]

        try:
            gdf = gpd.read_file(target_path)
        except Exception as e:
            raise ValueError(f"Error reading geospatial file: {str(e)}")

        crs = str(gdf.crs) if gdf.crs else "Unknown"
        feature_count = len(gdf)
        features_list = []

        # Convert to a projected CRS to calculate accurate measurements in meters
        if gdf.crs and gdf.crs.is_geographic:
            try:
                projected_gdf = gdf.to_crs(gdf.estimate_utm_crs())
            except Exception:
                projected_gdf = gdf.to_crs("EPSG:6933")
        else:
            projected_gdf = gdf

        for index, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
                
            geom_type = geom.geom_type
            proj_geom = projected_gdf.loc[index].geometry
            
            measurement = None
            if geom_type in ['Polygon', 'MultiPolygon']:
                measurement = proj_geom.area 
            elif geom_type in ['LineString', 'MultiLineString']:
                measurement = proj_geom.length 
            elif geom_type in ['Point', 'MultiPoint']:
                measurement = 0.0 
            
            # Extract properties dynamically
            props = {col: row[col] for col in gdf.columns if col != 'geometry' and not isinstance(row[col], (list, dict))}
            
            features_list.append({
                "feature_index": index,
                "geom_type": geom_type,
                "geometry_wkt": geom.wkt,
                "properties": props,
                "measurement": measurement
            })
            
        return crs, feature_count, features_list

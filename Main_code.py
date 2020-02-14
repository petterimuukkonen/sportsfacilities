import pandas as pd
import geopandas as gpd
from pyproj import CRS
import requests
import geojson

# Fetching data from WFS using requests, in json format, using bounding box over the helsinki area
r = requests.get("""http://lipas.cc.jyu.fi/geoserver/lipas/ows?service=wfs&version=2.0.0&request=GetFeature&typeNames=lipas:lipas_3110_uimahalli&bbox=361500.0001438780454919,6665250.0001345984637737,403750.0001343561452813,6698000.0001281434670091,EPSG:3067&outputFormat=json""")

# Creating GeoDataFrame from geojson
lipas_data = gpd.GeoDataFrame.from_features(geojson.loads(r.content))

# Removing unnecessary attributes from lipas_data
lipas_data = lipas_data[["geometry","id","nimi_fi","nimi_se","tyyppikoodi","tyyppi_nimi_fi"]]


## Creating a list of YKR_IDs based on the location of sport facilities
# Set filepath  and read YKR grid
ykr_fp = r"data/MetropAccess_YKR_grid_EurefFIN.shp"
ykr_grid = gpd.read_file(ykr_fp)

# Define crs for lipas_data (ykr_grid is already set)
lipas_data.crs = {'init':'epsg:3067'}

# Executing a spatial join to find out YKR-grid cells that have a sport facility inside them
lipas_join = gpd.sjoin(lipas_data, ykr_grid, how="inner", op="within")

# Unique YKR_IDs into a list
ykr_list = lipas_join['YKR_ID'].unique().tolist()

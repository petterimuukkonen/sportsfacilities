# importing modules
import geopandas as gpd
import pandas as pd
import numpy as np
import pyproj
import os.path 
import requests
import geojson
from geocube.api.core import make_geocube
## if geocube has not been installed before use "conda install -c conda-forge geocube" in terminal

def GetLipasData(typecode, typename):
    """
    This function fetches Lipas data from WFS and sets crs - EMIL muokkailee ja käy läpi :)
    """
        # Fetching data from WFS using requests, in json format, using bounding box over the helsinki area
    r = requests.get("""http://lipas.cc.jyu.fi/geoserver/lipas/ows?service=wfs&version=2.0.0&request=GetFeature&typeNames=lipas:lipas_"""+typecode+"""_"""+typename+"""&bbox=361500.0001438780454919,6665250.0001345984637737,403750.0001343561452813,6698000.0001281434670091,EPSG:3067&outputFormat=json""")

    # Creating GeoDataFrame from geojson
    lipas_data = gpd.GeoDataFrame.from_features(geojson.loads(r.content))

    # Removing unnecessary attributes from lipas_data
    lipas_data = lipas_data[["geometry","id","nimi_fi","nimi_se","tyyppikoodi","tyyppi_nimi_fi"]]
    
    # Define crs for lipas_data
    lipas_data.crs = {'init':'epsg:3067'}
       
    return lipas_data


def CreateYkrList(lipas_data):
    """
    This function creates a list of YKR_IDs based on the location of sport facilities in lipas_data. For fething right YKR_IDs MetropAccess_YKR_grid is used (Helsinki greater region).
    """
    
    # Set filepath  and read YKR grid
    ykr_fp = r"data/MetropAccess_YKR_grid_EurefFIN.shp"
    ykr_grid = gpd.read_file(ykr_fp)
    ykr_grid.crs = {'init':'epsg:3067'}

    # Executing a spatial join to find out YKR-grid cells that have a sport facility inside them
    join = gpd.sjoin(lipas_data, ykr_grid, how="inner", op="within")

    # Unique YKR_IDs into a list
    ykr_list = join['YKR_ID'].unique().tolist()

    return ykr_list


    
def GeodataframeToTiff(geodata, lipastype, lipasname):
    """
    This function turns values of already defined attributes from geodataframe grid into TIFF-rasters.
    Function takes geodataframe as geodata, and sport facility code as lipastype and name as lipasname.
    Geodataframe has to have minimum travel times to sport facility in columns specified in attr_list.
    Function has been designed for spatial resolution of 250m x 250m (MetropAccess_YKR_grid).
    """
    # defining attributes that will be tranformed into TIFF-files
    attr_list = ["min_t_bike","min_t_pt","min_t_car"]
    #attr_list = ["min_t_bike_f", "min_t_bike_s","min_t_pt_r","min_t_pr_m","min_t_car_r","min_t_car_m", "min_t_walk_f", "min_t_walk_s"]
    
    # creating a raster cube from geodataframe and selected attribute values
    cube = make_geocube(vector_data=geodata, measurements= attr_list, resolution=(250, -250))
    
    # writing all 
    cube.min_t_bike.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_bike_f_t.tif")
    cube.min_t_pt.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_r_t.tif")
    cube.min_t_car.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_car_r_t.tif")
    #cube.min_t_bike_f.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_bike_f_t.tif")
    #cube.min_t_pt_r.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_r_t.tif")
    #cube.min_t_car_r.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_car_r_t.tif")
    #cube.min_t_bike_s.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_bike_s_t.tif")
    #cube.min_t_pt_m.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_m_t.tif")
    #cube.min_t_car_m.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_car_m_t.tif")
    #cube.min_t_walk_f.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_walk_f_t.tif")
    #cube.min_t_walk_s.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_walk_s_t.tif")
    print("Files saved.")

    
def FileFinder(YKR_ids):
    """
    Gets the data for certain cell of Helsinki Travel time matrix. Insert a list of YKR ids. 
    """
    #create a list for the outputs
    filepaths = []
    
    #make sure that user input is a list, otherwise print a message to the user
    if(type(YKR_ids)!=list):
        print("Please make sure that input is a list")
    
    #loop over the inputs and keep track of loops
    for num, i in enumerate(YKR_ids):
        
        #access the first 4 numbers of the input which indicate the folder name (xxx added in the string)
        folder = str(i)[0:4]
        
        #put together the filepath according to the filepaths when you unzip Travel Time Matrix
        fp = r"data/HelsinkiTravelTimeMatrix2018/" + folder + "xxx/travel_times_to_ " + str(i) + ".txt"
        #Print which file is under process and how many in total
        print("Processing file " + fp + ". Progress: " + str(num+1) + "/" + str(len(YKR_ids)))
        
        #make sure that a file exists with that path, otherwise print a warning
        if(os.path.isfile(fp)==False):
            print("WARNING: FILE DOES NOT EXIST")
        #add the filepath to filepaths list
        filepaths.append(fp)
    
    #return filepaths
    return filepaths


def TableJoiner(filepaths):
    """
    Gets the YKR grid and merges the grid with accessibility data from chosen grid cells.
    """

    #access the YKR grid to get the spatial extent and geometry (has to be saved in data folder)
    fpgrid = "data/MetropAccess_YKR_grid_EurefFIN.shp"
    grid = gpd.read_file(fpgrid)

    #iterate over filepaths
    for i, fp in enumerate(filepaths):

        #read in the file
        data = pd.read_csv(fp, sep=";", usecols=["from_id", "bike_f_t", "pt_r_t", "car_r_t"])
        #get the cell number
        cell_ID = fp.split("_")[-1][:-4]
        #create new names for each added columns by the number of the file under processing (i)
        new_names = {"from_id": "YKR_ID", "bike_f_t": "bike_f_t_" + str(i), "pt_r_t": "pt_r_t_" + str(i),
                    "car_r_t": "car_r_t_" + str(i)}
        data= data.rename(columns=new_names)
    
        #merge file with grid on the id of cells and remove no data values
        grid = grid.merge(data, on="YKR_ID")
        grid.replace(to_replace=-1, value=np.nan, inplace=True)
        grid = grid.dropna()

    #initialise empty columns for minimum travel times
    grid["min_t_bike"] = None
    grid["min_t_car"] = None
    grid["min_t_pt"] = None

    
    #if there are multiple destination points, count the minimum travel time to closest destination point
    if(len(filepaths)>1):
        
        #first assign all columns starting with "bike" to variable bike_cols (with list comprehension)
        bike_cols = [col for col in grid if col.startswith("bike")]
        #apply minimum function to those columns and save the value to min column. Repeat for others.
        grid["min_t_bike"] = grid[bike_cols].apply(min, axis=1)
        
        car_cols = [col for col in grid if col.startswith("car")]
        grid["min_t_car"] = grid[car_cols].apply(min, axis=1)
        
        pt_cols = [col for col in grid if col.startswith("pt")]
        grid["min_t_pt"] = grid[pt_cols].apply(min, axis=1)
        
    return grid

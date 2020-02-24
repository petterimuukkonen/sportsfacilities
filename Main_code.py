# importing modules
import geopandas as gpd
import pandas as pd
import numpy as np
import pyproj
import os.path 
import requests
import geojson
from geocube.api.core import make_geocube
import mapclassify
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import contextily as ctx
import os.path 
from pyproj import CRS
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
    attr_list = ["min_t_bike_f", "min_t_bike_s","min_t_pt_r","min_t_pt_m","min_t_car_r","min_t_car_m", "min_t_walk"]
    
    # creating a raster cube from geodataframe and selected attribute values
    cube = make_geocube(vector_data=geodata, measurements= attr_list, resolution=(250, -250))
    
    
    #for i in attr_list:
        #column_name = i
        #cube.column_name.rio.to_raster("outputs/"+ lipastype + "_"+ lipasname + i + ".tif")
        
    # writing all 
    cube.min_t_bike_f.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_bike_f_t.tiff")
    cube.min_t_pt_r.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_r_t.tiff")
    cube.min_t_car_r.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_car_r_t.tiff")
    cube.min_t_bike_s.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_bike_s_t.tiff")
    cube.min_t_pt_m.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_m_t.tiff")
    cube.min_t_car_m.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_car_m_t.tiff")
    cube.min_t_walk.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_walk_f_t.tiff")
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
        data = pd.read_csv(fp, sep=";", usecols=["from_id", "bike_f_t", "bike_s_t", "pt_r_t", "pt_m_t", "car_r_t",
                                                "car_m_t", "walk_t"])
        #get the cell number
        cell_ID = fp.split("_")[-1][:-4]
        #create new names for each added columns by the number of the file under processing (i)
        new_names = {"from_id": "YKR_ID", "bike_f_t": "bike_f_t_" + str(i), "bike_s_t": "bike_s_t_" + str(i), 
                     "pt_r_t": "pt_r_t_" + str(i), "pt_m_t": "pt_m_t_" + str(i), "car_m_t": "car_m_t_" + str(i),
                    "car_r_t": "car_r_t_" + str(i), "walk_t": "walk_t_" + str(i)}
        data= data.rename(columns=new_names)
    
        #merge file with grid on the id of cells and remove no data values
        grid = grid.merge(data, on="YKR_ID")
        grid.replace(to_replace=-1, value=np.nan, inplace=True)
        grid = grid.dropna()

    #initialise empty columns for minimum travel times
    grid["min_t_bike_f"] = None
    grid["min_t_bike_s"] = None
    grid["min_t_car_r"] = None
    grid["min_t_car_m"] = None
    grid["min_t_pt_r"] = None
    grid["min_t_pt_m"] = None
    grid["min_t_walk"] = None

    
    #if there are multiple destination points, count the minimum travel time to closest destination point
    if(len(filepaths)>1):
        
        #first assign all columns starting with "bike_f" to variable bike_cols (with list comprehension)
        bikef_cols = [col for col in grid if col.startswith("bike_f")]
        #apply minimum function to those columns and save the value to min column. Repeat for others.
        grid["min_t_bike_f"] = grid[bikef_cols].apply(min, axis=1)
        
        bikes_cols = [col for col in grid if col.startswith("bike_s")]
        grid["min_t_bike_s"] = grid[bikes_cols].apply(min, axis=1)
        
        carr_cols = [col for col in grid if col.startswith("car_r")]
        grid["min_t_car_r"] = grid[carr_cols].apply(min, axis=1)
        
        carm_cols = [col for col in grid if col.startswith("car_m")]
        grid["min_t_car_m"] = grid[carm_cols].apply(min, axis=1)
        
        ptr_cols = [col for col in grid if col.startswith("pt_r")]
        grid["min_t_pt_r"] = grid[ptr_cols].apply(min, axis=1)
        
        ptm_cols = [col for col in grid if col.startswith("pt_m")]
        grid["min_t_pt_m"] = grid[ptm_cols].apply(min, axis=1)
        
        walk_cols = [col for col in grid if col.startswith("walk")]
        grid["min_t_walk"] = grid[walk_cols].apply(min, axis=1)
        
    return grid

def Visualiser(geodata, column_name, lipasname):
    
    travel_method = column_name.split("_")[2]
    
    #define class breaks to array seen below (upper limits), apply this classification to pt and car travel times
    bins = [0,5,10,15,20,25,30,40,50,60]
    classifier = mapclassify.UserDefined.make(bins)
    
    #make new columns with class values
    geodata["classified"] = geodata[[column_name]].apply(classifier)
    
    #change crs to add basemap later
    geodata = geodata.to_crs(epsg=3857)
            
    #plot
    fig, ax = plt.subplots(figsize=(10,6.5))

    #plot the travel times according to the classified field
    geodata.plot(ax= ax, column=geodata["classified"], cmap="RdYlBu", legend=True)
    cbar = fig.axes[1]
    cbar.set_yticklabels(bins)
    
    #add basemap with contextify
    cartodb_url = "https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png" 

    ctx.add_basemap(ax, attribution="Source: Helsinki region travel time matrix by UH. Basemap: OSM light", 
                    url=cartodb_url)


    #add scalebar
    scalebar = ScaleBar(1.0, location=4)
    plt.gca().add_artist(scalebar)

    #add north arrow
    x, y, arrow_length = 0.9, 0.2, 0.115
    ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length), arrowprops=dict(facecolor='black', width=5,                 headwidth=15),ha='center', va='center', fontsize=20, xycoords=ax.transAxes)
    
    #add title and show map
    ax.set_title("Travel times to " +lipasname+ " by " + travel_method, fontsize=24)

    #save and return fig
    output_fig = "outputs/traveltimes" + column_name + ".png"
    plt.savefig(output_fig)
    return output_fig
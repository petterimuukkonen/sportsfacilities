# importing modules
import geopandas as gpd
import pandas as pd
import numpy as np
import pyproj
import os.path 
import requests
import geojson
from geocube.api.core import make_geocube
import math
import shapely
import mapclassify
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import contextily as ctx
import folium
import os.path 
from pyproj import CRS


def GetLipasData(typecode, typename):
    """
    This function fetches Lipas data from WFS and sets crs. First argument is 4 digit typecode and second is the typename in Finnish. Exhaustive list of these can be found from file LIPAS_codes.csv.
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


def GetLipasUserFriendly(filepath):
    """ 
    This function makes it easier for the user to choose what kind of lipas data to get and returns it as a dataframe. As an argument, insert the filepath to csv file containing LIPAS codes. First, the function is asking you to insert a code of one of the main sport facilities type and after that brings out the subgroups of that particular main group. Sports facilities that are type of area or line have been filtered out.
    """
    
    # Importing lipas code data as csv from for example r"data/Codes_LIPAS_csv.csv"
    lipas_codes = pd.read_csv(filepath)
    
    # Dropping alternatives that are assosciated with polygon or linestring data (not from subgroup titles)
    for index, row in lipas_codes.iterrows():
         if np.isnan(row['alaryhmä']):
                lipas_codes = lipas_codes[~lipas_codes['Liikuntapaikkatyyppi=karttatason nimi suomeksi'].str.contains('alue')]
                lipas_codes = lipas_codes[~lipas_codes['Liikuntapaikkatyyppi=karttatason nimi suomeksi'].str.contains('alueet')]
                lipas_codes = lipas_codes[~lipas_codes['Liikuntapaikkatyyppi=karttatason nimi suomeksi'].str.contains('rata')]
                lipas_codes = lipas_codes[~lipas_codes['Liikuntapaikkatyyppi=karttatason nimi suomeksi'].str.contains('reitti')]
                lipas_codes = lipas_codes[~lipas_codes['Liikuntapaikkatyyppi=karttatason nimi suomeksi'].str.contains('reitit')]
                
    # Print the list of subgroups
    for index, row in lipas_codes.iterrows():
        if row['alaryhmä'] > 0:
            print(int(row['alaryhmä']), row['Liikuntapaikkatyyppi=karttatason nimi suomeksi'])

    # User gives input as the code
    user_input = int(input('Anna kyseisen liikuntapaikkatyypin numero'))

    # Fetching the start and stop index for the lipas codes
    for index, row in lipas_codes.iterrows():
        if user_input == row['alaryhmä']:
            start = index
            break
    for index, row in lipas_codes.iterrows():
        if user_input < row['alaryhmä']:
            stop = index
            break
            
    # Printing the items in the subgroup
    print("Valitse liikuntapaikkatyyppi")
    for index, row in lipas_codes.iterrows():
        if start < index and stop > index:
            print(row['Koodi'], row['Liikuntapaikkatyyppi=karttatason nimi suomeksi'])
            
    # Another user input as the code
    user_input = int(input("Liikuntapaikkatyypin koodi"))
    
    # Fetching the correct items from the WFS
    for index, row in lipas_codes.iterrows():
        if row['Koodi'] == user_input:
            r_string = """http://lipas.cc.jyu.fi/geoserver/lipas/ows?service=wfs&version=2.0.0&request=GetFeature&typeNames=lipas:""" + row['karttatason tekninen nimi'] + """&bbox=361500.0001438780454919,6665250.0001345984637737,403750.0001343561452813,6698000.0001281434670091,EPSG:3067&outputFormat=json"""
            r = requests.get(r_string)
            json = r.json()
            
            # If there's no items at all there will be a message printed
            if json['totalFeatures'] < 1:
                print("Ei yhtäkään kyseistä paikkaa löydetty")
            # The fetched items are printed out for the user
            else:

                lipas_data = gpd.GeoDataFrame.from_features(geojson.loads(r.content))

    # Dropping all rows without point geometry
    for index, row in lipas_data.iterrows():
                    if type(row['geometry']) != shapely.geometry.point.Point:
                        lipas_data.drop(index, inplace=True)

    if len(lipas_data) == 0:
        print("Ei yhtäkään kyseistä paikkaa löydetty")
    else:
        print("Löysimme seuraavat paikat:")
        print(lipas_data['nimi_fi'])
        
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
    Gets the YKR grid and merges the grid with accessibility data from chosen grid cells. Takes a list of filepaths of Travel Time Matrix files (txt) as the argument.
    """

    #access the YKR grid to get the spatial extent and geometry (has to be saved in data folder)
    fpgrid = "data/MetropAccess_YKR_grid_EurefFIN.shp"
    grid = gpd.read_file(fpgrid)

    #iterate over filepaths
    for i, fp in enumerate(filepaths):

        #read in the file
        data = pd.read_csv(fp, sep=";", usecols=["from_id", "bike_f_t", "bike_s_t", "pt_r_t", "pt_m_t", "car_r_t",
                                                "car_m_t", "walk_t", "car_sl_t", "pt_m_tt", "pt_r_tt"])
        #get the cell number
        cell_ID = fp.split("_")[-1][:-4]
        #create new names for each added columns by the number of the file under processing (i)
        new_names = {"from_id": "YKR_ID", "bike_f_t": "bike_f_t_" + str(i), "bike_s_t": "bike_s_t_" + str(i), 
                     "pt_r_t": "pt_r_t_" + str(i), "pt_m_t": "pt_m_t_" + str(i), "pt_m_tt": "pt_m_tt_" + str(i), "car_m_t": 
                     "car_m_t_" + str(i),"car_r_t": "car_r_t_" + str(i), "car_sl_t": "car_sl_t_" + str(i) ,"walk_t": "walk_t_" + 
                     str(i), "pt_r_tt": "pt_r_tt_" + str(i)}
        data= data.rename(columns=new_names)
        
        #merge the data    
        grid = grid.merge(data, on="YKR_ID")

    #initialise empty columns for minimum travel times
    grid["min_t_bike_f"] = None
    grid["min_t_bike_s"] = None
    grid["min_t_car_r"] = None
    grid["min_t_car_m"] = None
    grid["min_t_car_sl"] = None
    grid["min_t_pt_r_t"] = None
    grid["min_t_pt_r_tt"] = None
    grid["min_t_pt_m_t"] = None
    grid["min_t_pt_m_tt"] = None
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
        
        carsl_cols = [col for col in grid if col.startswith("car_sl")]
        grid["min_t_car_sl"] = grid[carsl_cols].apply(min, axis=1)
        
        ptrt_cols = [col for col in grid if col.startswith("pt_r_t")]
        grid["min_t_pt_r_t"] = grid[ptrt_cols].apply(min, axis=1)
        
        ptrtt_cols = [col for col in grid if col.startswith("pt_r_tt")]
        grid["min_t_pt_r_tt"] = grid[ptrtt_cols].apply(min, axis=1)
        
        ptm_cols = [col for col in grid if col.startswith("pt_m_t_")]
        grid["min_t_pt_m_t"] = grid[ptm_cols].apply(min, axis=1)
        
        pttt_cols = [col for col in grid if col.startswith("pt_m_tt_")]
        grid["min_t_pt_m_tt"] = grid[pttt_cols].apply(min, axis=1)
        
        walk_cols = [col for col in grid if col.startswith("walk")]
        grid["min_t_walk"] = grid[walk_cols].apply(min, axis=1)
        
    return grid

## if geocube has not been installed before use "conda install -c conda-forge geocube" in terminal
    
def GeodataframeToTiff(geodata, lipastype, lipasname):
    """
    This function turns values of already defined attributes from geodataframe grid into TIFF-rasters.
    Function takes geodataframe as geodata, and sport facility code as lipastype and name as lipasname.
    Geodataframe has to have minimum travel times to sport facility in columns specified in attr_list.
    Function has been designed for spatial resolution of 250m x 250m (MetropAccess_YKR_grid).
    """
    # defining attributes that will be tranformed into TIFF-files
    attr_list = ["min_t_bike_f", "min_t_bike_s","min_t_pt_r_t", "min_t_pt_r_tt","min_t_pt_m_t","min_t_car_r","min_t_car_m", "min_t_walk", "min_t_car_sl", "min_t_pt_m_tt"]
    
    # creating a raster cube from geodataframe and selected attribute values
    cube = make_geocube(vector_data=geodata, measurements= attr_list, resolution=(250, -250))
    
        
    # writing all 
    cube.min_t_bike_f.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_bike_f_t.tiff")
    cube.min_t_pt_r_t.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_r_t.tiff")
    cube.min_t_car_r.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_car_r_t.tiff")
    cube.min_t_pt_r_tt.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_r_tt.tiff")
    cube.min_t_bike_s.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_bike_s_t.tiff")
    cube.min_t_pt_m_t.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_m_t.tiff")
    cube.min_t_pt_m_tt.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_pt_m_tt.tiff")
    cube.min_t_car_sl.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_car_sl_t.tiff")
    cube.min_t_car_m.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_car_m_t.tiff")
    cube.min_t_walk.rio.to_raster("outputs/"+lipastype + "_"+lipasname+"_walk_f_t.tiff")
    print("Files saved.")


def Visualiser(geodata, column_name, lipasname):
    """
    This function visualises the travel times on map. Takes geodataframe containing minimum travel times and column name 
    of the column you want to visualise as inputs.
    """
    #remove nodata values for visualising
    geodata = geodata.copy()
    geodata.replace(to_replace=-1, value=np.nan, inplace=True)
    geodata = geodata.dropna()
    
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
    ax.set_title("Travel times to " + lipasname + " by " + travel_method , fontsize=24)

    #save and return fig
    output_fig = "outputs/traveltimes" + column_name + ".png"
    plt.savefig(output_fig)
    return output_fig


def InteractiveMap(geodata, column_name):
    """
    Creates an interactive map of the column that you want to visualise using folium. Takes geodataframe and
    the column name as parameters. 
    """
    #remove noData values for visualising
    geodata = geodata.copy()
    geodata.replace(to_replace=-1, value=np.nan, inplace=True)
    geodata = geodata.dropna()
    
    #add a basemap
    m = folium.Map(location=[60.25, 24.8], tiles = 'cartodbpositron', zoom_start=10, control_scale=True,
                           attribution = "Data: Helsinki Travel Time Matrix")

    #define class breaks to array seen below 
    bins = [0,5,10,15,20,25,30,40,50,60, 200]
    
    travel_method = column_name.split("_")[2]
    
    #add the choropleth
    folium.Choropleth(
    geo_data=geodata,
    name="Travel times by " + travel_method,
    data=geodata,
    columns=["YKR_ID", column_name],
    key_on="feature.properties.YKR_ID",
    bins = bins,
    fill_color="RdYlBu",
    fill_opacity=0.7,
    line_opacity=0.2,
    line_color="white",
    line_weight=0,
    highlight=True,
    legend_name="Travel times by " + travel_method + ", in minutes",
    ).add_to(m)

    #add tooltips (info when hovering over) as geoJson
    folium.GeoJson(geodata, name="travel time", smooth_factor=2,
    style_function=lambda x: {'weight':0.01,'color':'#807e7e', 'fillOpacity':0},
    highlight_function=lambda x: {'weight':1.5, 'color':'black'},
    tooltip=folium.GeoJsonTooltip(fields=[column_name],labels=True, sticky=False)).add_to(m)

            
    #display layer control
    folium.LayerControl().add_to(m)

    #save and return the map
    outfp= "outputs/traveltimes" + column_name + ".html"
    m.save(outfp)

    return m
        
    

    

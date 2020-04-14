# GIS project course 2020

## Toolpack for mapping accessibility of sports facilities

### Aim of the project

* Combine LIPAS database of sports facilities with Helsinki Travel Time Matrix
* Produce raster files measuring the accessibility of different types of sports facilities in Helsinki Metropolitan area for further GIS analysis
* Visualise the accessibility of sports places with Python to have an idea of the results

### Input data: 

- [Helsinki Travel Time Matrix 2018](https://blogs.helsinki.fi/accessibility/helsinki-region-travel-time-matrix-2018/), 
- YKR grid 2018 (can be downloaded from the link above, make sure to use all 7 files that the shapefile consists of), 
- [LIPAS data](https://www.lipas.fi/liikuntapaikat) for sports facilities, fetched using WFS

### Instructions for usage:

You can test and run the code with limited example files in GitHub. Due to the size of input files, for full access to the data you need to download the data. Download the Travel Time Matrix and YKR grid data by clicking *Travel Time Matrix link*. Create a folder called "data" under the same folder where you are working. Place the YKR grid in the "data" folder and move the entire folder called "HelsinkiTravelTimeMatrix2018" under the data folder as well. Do not alter the files or filepaths inside HelsinkiTravelTimeMatrix2018.

### Analysis process and the functions

1. Define which types of sports facilities are you interested in and fetch the LIPAS data 
      1. `data/Codes_LIPAS.csv`
      2. `GetLipasData()` or `GetLipasUserFriendly()`
2. Locate in which YKR grid cells the sports facilities are and find the right travel time files for those grid cells
      1. `CreateYkrList()`
      2. `FileFinder()`
3. Combine sport facility data to travel time matrix data and calculate the minimum travel times to closest facility from each cell with every transport method
      1. `TableJoiner()`
4. Save minimum travel times of each travel method into raster files for further use in GIS softwares
      1. `GeodataframeToTiff()`
5. Visualise the accessibility of sport facilities by chosen travel method by making a static or an interactive map
      1. `Visualiser()`
      2. `InteractiveMap()`

Here is a example of a map made with Visualiser:
![](outputs/traveltimesmin_t_car_m.png)

# GIS-project-course

# Toolpack for mapping accessibility of sports facilities

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

### Analysis process and steps to reproduce

1. Define which types of sports places are you interested in and fetch the LIPAS data 
2. Locate in which YKR grid cells the sports facilities are and get the travel time info to those cells
3. Calculate the minimum travel time to closest facility from each cell with different transport methods
4. Define which travel methods you want to save as raster file
5. Visualise the accessibility by different travel methods by making maps and interactive maps

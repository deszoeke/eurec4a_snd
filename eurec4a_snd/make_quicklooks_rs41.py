"""
Script to produce quicklooks of radiosonde type RS41, read from netcdf-files converted using L1-rs41.py

Created by: Sabrina Schnitt
tested on python 2.7
"""

__author__ = "Sabrina Schnitt"
__date__ = "$Oct 2, 19$"

import glob, sys, getopt, os
import netCDF4 as nc
from matplotlib.ticker import AutoMinorLocator
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
import math

def read_ncfile(ncfile):
    '''
    routine reads variables and attributes of ncfile generated by L1-rs41.py. 
    INPUT: path+filename of netcdf-file
    OUTPUT: dictionnary with all variables and attributes.
    '''
    
    data = {}
    
    ncf = nc.Dataset(ncfile)
    
    for k in ncf.variables.keys():
        data[k] = ncf.variables[k][:]
    
    for a in ncf.ncattrs():
        data[a] = ncf.getncattr(a)
    
    specs = {}
    keys = ['rs', 'type', 'location', 'motion', 'tempres', 'date']
    for kk,key in enumerate(keys):
        specs[key] = ncfile.split('/')[-1].split('__')[kk]
    
    specs['rs'] = specs['rs']
    specs['date'] = specs['date'][:-3]
    
    return data, specs



def plot_ptrh(data,specs, outputpath):
    '''
    routine plots vertical profiles of temperature, pressure, rel humidity and saves plot as .png
    INPUT: 
        - data: dictionnary with data (eg filled by read_ncfile())
        - specs: dictionnary with filename specifications (filled by read_ncfile())
        - outputpath: path where png will be stored in.
    OUTPUT: .png file stored in outputpath
    '''
    print('now plotting pressure, temperature, rel humidity sounding.........')
    
    #define outputname of .png-file:
    outputname = '%s__%s__%s__%s__%s__%s_ptrelh.png'%(specs['rs'], specs['type'], specs['location'], specs['motion'], specs['tempres'], specs['date'])
    
    
    fig, ax = plt.subplots(1,3, sharey = True, figsize=(8,6))
    
    #plot temperature, pressure, humidity in three panels:
    ax[0].plot(data['temperature'], data['altitude'],'.-k', markersize=1)
    ax[1].plot(data['pressure'], data['altitude'], '.-k', markersize=1)
    ax[2].plot(data['humidity'], data['altitude'],'.-k', markersize=1)
    
    #do some cosmetics regarding the layout, axislabels, etc.:
    for i in range(3):
        #switch off some spines:
        ax[i].spines['top'].set_visible(False)
        ax[i].spines['right'].set_visible(False)
        ax[i].spines['left'].set_visible(False)
        ax[i].grid(axis='y', linestyle = '-', color='gray')
        
        #set height axis to start at 0m:
        ax[i].set_ylim(0,ax[i].get_ylim()[-1])
        #major minor ticks:
        ax[i].xaxis.set_minor_locator(AutoMinorLocator())
        ax[i].yaxis.set_minor_locator(AutoMinorLocator())
        ax[i].xaxis.set_major_locator(plt.MaxNLocator(4))
        #switch off major ticks top and right axis:
        ax[i].tick_params(top=False, right=False)
        #switch off minor ticks for top axis:
        ax[i].tick_params(axis='x',which='minor', top = False)
        #make labels larger for all ticks:
        ax[i].tick_params(axis='both',labelsize=14)
    
    
    ax[0].spines['left'].set_visible(True)
    ax[0].tick_params(axis = 'y',right=False,which='minor')
    ax[1].tick_params(left=False)
    ax[1].tick_params(axis = 'y',right=False, left=False,which='minor')
    ax[2].tick_params(left=False)
    ax[2].spines['right'].set_visible(True)
    ax[2].yaxis.set_ticks_position('right')
    ax[2].yaxis.set_label_position('right')
    
    #set the relh panel always to values between 0 and 100:
    ax[2].set_xlim(0,100)
    #and the pressure to max 1100 hPa:
    ax[1].set_xlim(ax[1].get_xlim()[0],1100)
    
    #axis labels:
    ax[0].set_ylabel('Altitude [m]',fontsize=14)
    ax[2].set_ylabel('Altitude [m]',fontsize=14)
    
    ax[0].set_xlabel('Temperature [$^\circ$C]',fontsize=14)
    ax[1].set_xlabel('Pressure [hPa]',fontsize=14)
    ax[2].set_xlabel('Rel Humidity [%]',fontsize=14)
    
    plt.subplots_adjust(top=0.9, right = 0.85, left=0.15)
    
    fig.suptitle('%s, %s %sUTC'%(specs['location'], specs['date'][:-2], data['time_of_launch_HHmmss'][:-2]),fontsize=18)
    
    fig.savefig(outputpath+outputname)
    
    return 



def plot_wind(data,specs, outputpath):
    '''
    routine plots vertical profiles of wind speed and direction and saves plot as .png
    INPUT: 
        - data: dictionnary with data (eg filled by read_ncfile())
        - specs: dictionnary with filename specifications (filled by read_ncfile())
        - outputpath: path where png will be stored in.
    OUTPUT: .png file stored in outputpath
    '''
    print('now plotting wind speed and direction sounding.........')
    #define outputname of .png-file:
    outputname = '%s__%s__%s__%s__%s__%s_wind.png'%(specs['rs'], specs['type'], specs['location'], specs['motion'], specs['tempres'], specs['date'])
    
    
    fig, ax = plt.subplots(1,2, sharey = True, figsize=(8,6))
    
    #plot the data into subpanels:
    ax[0].plot(data['windSpeed'], data['altitude'],'.-k', markersize=1)
    ax[1].plot(data['windDirection'], data['altitude'], '.-k', markersize=1)
    
    #general cosmetics:
    for i in range(2):
        ax[i].spines['top'].set_visible(False)
        ax[i].spines['right'].set_visible(False)
        ax[i].spines['left'].set_visible(False)
        ax[i].grid(axis='y', linestyle = '-', color = 'gray')
        ax[i].set_ylim(0,ax[i].get_ylim()[-1])
        ax[i].xaxis.set_minor_locator(AutoMinorLocator())
        ax[i].yaxis.set_minor_locator(AutoMinorLocator())
        ax[i].xaxis.set_major_locator(plt.MaxNLocator(4))
        ax[i].tick_params(top=False, right = False)
        #axis labels:
        ax[i].set_ylabel('Altitude [m]',fontsize=14)
        #switch off minor ticks for top axis:
        ax[i].tick_params(axis='x',which='minor', top = False)
        #make labels larger for all ticks:
        ax[i].tick_params(axis='both',labelsize=14)
    
    #switch off some ticks and labels and spines manually.
    ax[0].spines['left'].set_visible(True)
    ax[1].tick_params(left=False)
    ax[0].tick_params(right=False, which='minor',axis='y')
    
    ax[1].spines['right'].set_visible(True)
    ax[1].yaxis.set_ticks_position('right')
    ax[1].yaxis.set_label_position('right')
    
    #set wind direction axis to valid range:
    ax[1].set_xlim(0,360)
    
    ax[0].set_xlabel('Wind Speed [m s$^{-1}$]',fontsize=14)
    ax[1].set_xlabel('Wind Direction [$^\circ$]',fontsize=14)

    
    plt.subplots_adjust(top=0.9, right = 0.85, left=0.15)
    fig.suptitle('%s, %s %sUTC'%(specs['location'], specs['date'][:-2], data['time_of_launch_HHmmss'][:-2]),fontsize=18)
    
    fig.savefig(outputpath+outputname)
    
    return 


def plot_map(data,specs, outputpath):
    '''
    routine plots balloon flight on a map.
    INPUT: 
        - data: dictionnary with data (eg filled by read_ncfile())
        - specs: dictionnary with filename specifications (filled by read_ncfile())
        - outputpath: path where png will be stored in.
    OUTPUT: .png file stored in outputpath.
    REQUIRES: basemap-data-hires package to be installed.
    '''
    print('now plotting map of sounding.........')
    #define outputname of .png-file:
    outputname = '%s__%s__%s__%s__%s__%s_map.png'%(specs['rs'], specs['type'], specs['location'], specs['motion'], specs['tempres'], specs['date'])
    
    fig = plt.figure(figsize=(8,6))

    #determine the boundaries of the map from sounding lon and lat:
    maxlon = math.ceil(np.max(data['longitude'])/0.5)*0.5
    minlon = math.floor(np.min(data['longitude'])/0.5)*0.5
    
    maxlat = math.ceil(np.max(data['latitude'])/0.5)*0.5
    minlat = math.floor(np.min(data['latitude'])/0.5)*0.5
    
    #set up basemap projection
    m = Basemap(projection='cyl', resolution='h', llcrnrlat = minlat, urcrnrlat=maxlat, llcrnrlon = minlon, urcrnrlon=maxlon, area_thresh=1)
    #plot a topography on top:
    m.etopo( alpha=0.4)
    
    
    #coastlines, countries, boundary, background-color, gridlines
    m.drawcoastlines()
    m.drawcountries()
    m.drawmapboundary()
    m.shadedrelief()
    m.fillcontinents(color='#00a500')
    m.drawparallels(np.arange(10,70,0.25),labels=[1,1,0,0])
    m.drawmeridians(np.arange(-100,0,0.25),labels=[0,0,0,1])
    
    #plot balloon path:
    x,y = m(data['longitude'],data['latitude'])
    m.plot(x,y,'-k')
    
    #plot launch position as red square:
    m.plot(float(data['Longitude_of_launch_location'][:5])*-1, float(data['Latitude_of_launch_location'][:5]),'sr',markersize=5)
    
    #and the figure title:
    plt.title('%s, %s %sUTC'%(specs['location'], specs['date'][:-2], data['time_of_launch_HHmmss'][:-2]))
    
    fig.savefig(outputpath+outputname)
    
    print('done.')
    return


#options for the skript: date (yymmddhh); inputfilename; outputpath; inputpath (needs to be specified if date is used); 
#defaults: outputpath: './'; inputpath: './'
#either date+inputpath or inputfilename incl path need to be specified. everything else is optional.

inputfile = ''
date = ''
outputpath = './' #default setting
inputpath = './' #default setting

try:
    opts, args = getopt.getopt(sys.argv[1:],'d:n:o:i:h',['date=','inputncfile=','outputpath=','inputpath=','help'])
    
except getopt.GetoptError:
    print('usage: python make_quicklooks_rs41.py -i <inputpath> -d <yymmddhh> -n <inputncfile> -o <outputpath> ')
    sys.exit(2)

for opt, arg in opts:
    if opt in ('-h',"--help"): #help option
        print('usage: python make_quicklooks_rs41.py -i <inputpath> -d <yymmddhh> -n <inputncfile> -o <outputpath>')
        print('specify either complete input netcdf filename (-n) or date (-d) of sounding from which file be searched in -i inputpath. ')
        print('default inputpath: current directory. specify with -i option if different. if used together with -d, make sure -i is given first in call.')
        print('default outputpath: current directory. if -o is specified, outputpath is created if not yet existant.')
        sys.exit()
    
    elif opt in ("-i", "--inputpath"):
        
        inputpath = arg
    
    elif opt in ("-d", "--date"):
        
        try:
            ncfile = glob.glob(inputpath + '*%s*.nc'%arg)[0]
        except IndexError:
            print('couldnt find your specified input: check date or/and inputpath selection.')
            sys.exit()
    
    elif opt in ("-n","--inputncfile"):
        ncfile = arg
        if not os.isfile(ncfile):
            print('couldnt find your specified inputfile.')
            sys.exit()
    
    elif opt in ("-o","--outputpath"):
        outputpath = arg
        #check if there's a backslash after the outputpath-argument:
        if outputpath[-1] != '/':
            outputpath = outputpath+'/'
        if not os.path.isdir(outputpath):
            os.mkdir(outputpath)
    
print('plotting sounding file %s'%ncfile)

#read netcdf-variables into dictionnary:
data, specs = read_ncfile(ncfile)

#make first quicklook: p, relh, T- profiles.
plot_ptrh(data, specs, outputpath)

#now also plot wind speed and direction:
plot_wind(data, specs, outputpath)

#also plot the sounding onto a map: REQUIRES BASEMAP-DATA-HIRES package to be installed (eg through conda install -c conda-forge basemap-data-hires)

plot_map(data, specs, outputpath)


















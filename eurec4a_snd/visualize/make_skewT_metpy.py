#!/bin/env python

"""
Plot skew-T diagram of converted soundings
"""
import sys
import os.path
import argparse
import logging
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import numpy as np
import metpy.calc as mpcalc
from metpy.cbook import get_test_data
from metpy.plots import add_metpy_logo, Hodograph, SkewT
from metpy.units import units
import xarray as xr


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", metavar="INPUT_FILE",
                        help="Converted sounding file (netCDF)", default=None,
                        required=True)

    parser.add_argument("-o", "--outputfile", metavar="/some/example/path/filename.pdf",
                        help="Output filename for skewT diagram (all file endings"\
                             " of matplotlib are supported",
                        default=None,
                        required=False)

    parser.add_argument('-v', '--verbose', metavar="DEBUG",
                        help='Set the level of verbosity [DEBUG, INFO,'
                        ' WARNING, ERROR]',
                        required=False, default="INFO")

    parsed_args = vars(parser.parse_args())

    return parsed_args


def setup_logging(verbose):
    assert verbose in ["DEBUG", "INFO", "WARNING", "ERROR"]
    logging.basicConfig(
        level=logging.getLevelName(verbose),
        format="%(levelname)s - %(name)s - %(funcName)s - %(message)s",
        handlers=[
            logging.FileHandler("{}.log".format(__file__)),
            logging.StreamHandler()
        ])


def main():
    args = get_args()
    setup_logging(args['verbose'])

    # Define input file
    file = args['inputfile']
    output = args['outputfile']

    ds = xr.open_dataset(file)

    ds_sel = ds.isel({'sounding': 0})
    ds_sel = ds_sel.sortby(ds_sel.pressure, ascending=False)

    p = ds_sel.pressure.values
    T = ds_sel.temperature.values
    Td = ds_sel.dewPoint.values
    wind_speed = ds_sel.windSpeed.values
    wind_dir = ds_sel.windDirection.values

    # Filter nans
    idx = np.where((np.isnan(T)+np.isnan(Td)+np.isnan(p)+
                    np.isnan(wind_speed)+np.isnan(wind_dir)) == False, True, False)
    p = p[idx]
    T = T[idx]
    Td = Td[idx]
    wind_speed = wind_speed[idx]
    wind_dir = wind_dir[idx]

    # Add units
    p = p * units.hPa
    T = T * units.degC
    Td = Td * units.degC
    wind_speed = wind_speed * (units.meter/units.second)
    wind_dir = wind_dir * units.degrees

    u, v = mpcalc.wind_components(wind_speed, wind_dir)

    lcl_pressure, lcl_temperature = mpcalc.lcl(p[0], T[0], Td[0])

    parcel_prof = mpcalc.parcel_profile(p, T[0], Td[0]).to('degC')

    # Create a new figure. The dimensions here give a good aspect ratio
    fig = plt.figure(figsize=(9, 9))
    skew = SkewT(fig, rotation=30)

    # Plot the data using normal plotting functions, in this case using
    # log scaling in Y, as dictated by the typical meteorological plot
    skew.plot(p, T, 'r')
    skew.plot(p, Td, 'g')
    # Plot only specific barbs to increase visibility
    pressure_levels_barbs = np.logspace(0.1, 1, 50)*100

    def find_nearest(array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]

    # Search for levels by providing pressures
    # (levels is the coordinate not pressure)
    pres_vals = ds_sel.pressure.values[idx]
    closest_pressure_levels = np.unique([find_nearest(pres_vals, p_) for p_ in pressure_levels_barbs])
    _, closest_pressure_levels_idx, _ = np.intersect1d(pres_vals, closest_pressure_levels, return_indices=True)

    p_barbs = ds_sel.pressure.isel({'levels': closest_pressure_levels_idx}).values * units.hPa
    wind_speed_barbs = ds_sel.windSpeed.isel({'levels': closest_pressure_levels_idx}).values * (units.meter/units.second)
    wind_dir_barbs = ds_sel.windDirection.isel({'levels': closest_pressure_levels_idx}).values * units.degrees
    u_barbs, v_barbs = mpcalc.wind_components(wind_speed_barbs, wind_dir_barbs)

    # Find nans in pressure
    # p_non_nan_idx = np.where(~np.isnan(pres_vals))
    skew.plot_barbs(p_barbs, u_barbs, v_barbs)

    skew.ax.set_ylim(1020, 100)
    skew.ax.set_xlim(-50, 40)

    # Plot LCL as black dot
    skew.plot(lcl_pressure, lcl_temperature, 'ko', markerfacecolor='black')

    # Plot the parcel profile as a black line
    skew.plot(pres_vals, parcel_prof, 'k', linewidth=2)

    # Shade areas of CAPE and CIN
    skew.shade_cin(pres_vals, T, parcel_prof)
    skew.shade_cape(pres_vals, T, parcel_prof)

    # Plot a zero degree isotherm
    skew.ax.axvline(0, color='c', linestyle='--', linewidth=2)

    # Add the relevant special lines
    skew.plot_dry_adiabats()
    skew.plot_moist_adiabats()
    skew.plot_mixing_lines()

    # Create a hodograph
    # Create an inset axes object that is 40% width and height of the
    # figure and put it in the upper right hand corner.
    ax_hod = inset_axes(skew.ax, '40%', '40%', loc=1)
    h = Hodograph(ax_hod, component_range=80.)
    h.add_grid(increment=20)
    h.plot_colormapped(u, v, wind_speed)  # Plot a line colored by wind speed

    # Set title
    sounding_name = ds_sel.sounding.values
    sounding_name_str = str(sounding_name.astype('str'))
    skew.ax.set_title('{sounding}'.format(
        sounding=sounding_name_str))

    if output is None:
        output = str(os.path.basename(file).split('.')[0])+'.pdf'
    logging.info('Write output to {}'.format(output))
    plt.savefig(output)


if __name__ == '__main__':
    main()

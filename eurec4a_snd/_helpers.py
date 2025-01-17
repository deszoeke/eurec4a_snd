"""
Helper functions for bufr import
"""
import tempfile
import os
import json
import datetime as dt
import numpy as np


class UnitChangedError(Exception):
    pass


class UnexpectedUnit(Exception):
    pass


def convert_bufr_to_json(bufr_fn, logger=None):
    """
    Convert bufr file to json with ecCodes
    software
    """
    tmp_folder = tempfile.mkdtemp()
    tmp_output_json_fn = os.path.join(tmp_folder, 'tmp_bufr.json')
    r = os.system("bufr_dump -j s {} > {}".format(bufr_fn, tmp_output_json_fn))
    if logger is None:
        print("Converted {} to {}".format(bufr_fn, tmp_output_json_fn))
    else:
        logger.debug("Converted {} to {}".format(bufr_fn, tmp_output_json_fn))
    return tmp_output_json_fn


def flatten_json(y):
    """
    Flatten structured json array
    
    Input
    -----
    y : list or dict

    Return
    ------
    list : list
        list containing dicts for each key value pair
    """
    global r
    out = {}
    r = 0

    def flatten(x, name='', number=0):
        """helper function"""
        global r
        if type(x) is dict:
            for a in x:
                flatten(x[a], a)
        elif type(x) is list:
            i = 0
            for a in x:
                number = flatten(a)
                i += 1
                r += 1
        else:
            out['{:07g}_{}'.format(r, name)] = x

    flatten(y)
    return out


def read_json(json_fn):
    """
    Read and flatten json
    """
    with open(json_fn) as file:
        struct_json = json.load(file)

    bfr_json_flat = flatten_json(struct_json)
    keys = bfr_json_flat.keys()
    key_keys = []
    for key in keys:
        if 'key' in key:
            key_keys.append(key[:-4])

    return bfr_json_flat, key_keys


def convert_json_to_arrays(json_flat, key_keys):
    """
    Convert json data to array
    """
    class Sounding:
        """
        Class containing sounding data
        """
        def __init__(self):
            self.station_lat = None
            self.station_lon = None
            self.sounding_start_time = None
            self.time = []
            self.time_unit = None
            self.pressure = []
            self.pressure_unit = None
            self.temperature = []
            self.temperature_unit = None
            self.dewpoint = []
            self.dewpoint_unit = None
            self.windspeed = []
            self.windspeed_unit = None
            self.winddirection = []
            self.winddirection_unit = None
            self.gpm = []
            self.gpm_unit = None
            self.displacement_lat = []
            self.displacement_lat_unit = None
            self.displacement_lon = []
            self.displacement_lon_unit = None
            self.meta_data = {}

    def _ensure_measurement_integrity(self):
        """
        Test integrity of each measurement unit

        Measurements of the sonde in the bufr file
        contain usually:
            - time since launch
            - pressure
            - gpm
            - location displacement
            - temperature
            - dewpoint
            - wind direction
            - wind speed

        This is a complete unit. However, there are,
        dependining on the bufr format additional
        measurements, which might not consist of
        a complete measurement set. This is for ex.
        the case for the entry which contains the
        "absoluteWindShearIn1KmLayerBelow"

        Here the completeness of the measurement
        is checked and corrected otherwise by
        adding nan values to the not measured
        values.
        """
        if len(self.time) > len(self.temperature):
            self.temperature.append(np.nan)
        if len(self.time) > len(self.gpm):
            self.gpm.append(np.nan)
        if len(self.time) > len(self.dewpoint):
            self.dewpoint.append(np.nan)
        if len(self.time) > len(self.pressure):
            self.pressure.append(np.nan)
        if len(self.time) > len(self.windspeed):
            self.windspeed.append(np.nan)
        if len(self.time) > len(self.winddirection):
            self.winddirection.append(np.nan)
        if len(self.time) > len(self.displacement_lat):
            self.displacement_lat.append(np.nan)
        return

    s = Sounding()

    for key_key in key_keys:
        if json_flat[key_key+'_key'] == 'latitude':
            s.station_lat = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'longitude':
            s.station_lon = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'pressure':
            s.pressure.append(json_flat[key_key+'_value'])
            if s.pressure_unit is None:
                s.pressure_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.pressure_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.pressure_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'windSpeed':
            s.windspeed.append(json_flat[key_key+'_value'])
            if s.windspeed_unit is None:
                s.windspeed_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.windspeed_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.windspeed_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'windDirection':
            s.winddirection.append(json_flat[key_key+'_value'])
            if s.winddirection_unit is None:
                s.winddirection_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.winddirection_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.winddirection_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'nonCoordinateGeopotentialHeight':
            s.gpm.append(json_flat[key_key+'_value'])
            if s.gpm_unit is None:
                s.gpm_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.gpm_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.gpm_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'airTemperature':
            s.temperature.append(json_flat[key_key+'_value'])
            if s.temperature_unit is None:
                s.temperature_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.temperature_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.temperature_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'dewpointTemperature':
            s.dewpoint.append(json_flat[key_key+'_value'])
            if s.dewpoint_unit is None:
                s.dewpoint_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.dewpoint_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.dewpoint_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'latitudeDisplacement':
            s.displacement_lat.append(json_flat[key_key+'_value'])
            if s.displacement_lat_unit is None:
                s.displacement_lat_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.displacement_lat_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.displacement_lat_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'longitudeDisplacement':
            s.displacement_lon.append(json_flat[key_key+'_value'])
            if s.displacement_lon_unit is None:
                s.displacement_lon_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.displacement_lon_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.displacement_lon_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'timePeriod':
            # Check conistency of data
            _ensure_measurement_integrity(s)
            s.time.append(json_flat[key_key+'_value'])

            if s.time_unit is None:
                s.time_unit = json_flat[key_key+'_units']
            # Unit consistency test
            elif s.time_unit != json_flat[key_key+'_units']:
                raise UnitChangedError('{} and {} are not same unit'.format(s.time_unit,
                                                                            json_flat[key_key+'_units']))
        elif json_flat[key_key+'_key'] == 'year':
            year = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'month':
            month = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'day':
            day = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'hour':
            hour = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'minute':
            minute = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'second':
            second = json_flat[key_key+'_value']

        # Meta data
        elif json_flat[key_key+'_key'] == 'radiosondeSerialNumber':
            s.meta_data['sonde_serial_number'] = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'softwareVersionNumber':
            s.meta_data['softwareVersionNumber'] = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'radiosondeType':
            s.meta_data['radiosondeType'] = json_flat[key_key+'_value']
        elif json_flat[key_key+'_key'] == 'unexpandedDescriptors':
            try:
                s.meta_data['bufr_msg'] = json_flat[key_key+'_value']
            except KeyError:
                # Error probably caused, because there are several
                # unexpandedDescriptors
                # which seems to be only the case for dropsondes?!
                s.meta_data['bufr_msg'] = 309053
        elif json_flat[key_key+'_key'] == 'radiosondeOperatingFrequency':
            s.meta_data['sonde_frequency'] = str(json_flat[key_key+'_value']) + json_flat[key_key+'_units']

    _ensure_measurement_integrity(s)

    s.sounding_start_time = dt.datetime(year,
                                        month,
                                        day,
                                        hour,
                                        minute,
                                        second)

    return s


def replace_missing_data(sounding):
    """
    Removing Nones from sounding measurements
    """
    def replace_none(entry):
        """
        Replace None with NaN
        """
        if entry == None:
            return np.nan
        else:
            return entry

    variables = ['displacement_lat', 'displacement_lon', 'pressure', 'windspeed',
                 'winddirection', 'temperature', 'dewpoint', 'gpm', 'time']

    for var in variables:
        sounding.__dict__[var] = list(map(replace_none, sounding.__dict__[var]))

    return sounding


def convert_list_to_array(sounding):
    """
    Convert datatype of sounding
    """
    variables = ['displacement_lat', 'displacement_lon', 'pressure', 'windspeed',
                 'winddirection', 'temperature', 'dewpoint', 'gpm', 'time']

    for var in variables:
        sounding.__dict__[var] = np.array(sounding.__dict__[var])

    return sounding


def calculate_coordinates(origin, offset):
    """
    Calculate positon of measurement

    Input
    -----
    origin : float
        latitude or longitude of launch position
    offset : float
        latitudinal or longitudinal displacement
        since launch from origin

    Return
    ------
    float : position of measurement
    """
    return origin + offset


def calc_ascentrate(sounding):
    """
    Calculate the ascent rate

    Input
    -----
    sounding : obj
        sounding class containing gpm
        and flight time

    Return
    ------
    soundning : obj
        sounding including the ascent rate
    """
    ascent_rate = np.diff(sounding.gpm)/(np.diff(sounding.time))
    ascent_rate = np.ma.concatenate(([0], ascent_rate))  # 0 at first measurement
    sounding.ascentrate = ascent_rate

    return sounding


def calc_temporal_resolution(sounding):
    """
    Calculate temporal resolution of sounding

    Returns the most common temporal resolution
    by calculating the temporal differences
    and returning the most common difference.

    Input
    -----
    sounding : obj
        sounding class containing flight time
        information

    Return
    ------
    temporal_resolution : float
        temporal resolution
    """
    time_differences = np.abs(np.diff(np.ma.compressed(sounding.time)))
    time_differences_counts = np.bincount(time_differences.astype(int))
    most_common_diff = time_differences[np.argmax(time_differences_counts)]
    temporal_resolution = most_common_diff
    return temporal_resolution


def bufr_specific_handling(sounding):
    """
    Apply bufr message specific functions

    Depending on the BUFR format, that data
    has to be prepared differently

    BUFR309053 (dropsonde)
    BUFR309056 (radiosonde descent)
    BUFR309057 (radiosonde ascent)
    - Remove last entries of time, latitude, longitude because those
        belong to the 'absoluteWindShearIn1KmLayerAbove'/
        'absoluteWindShearIn1KmLayerBelow' entries

    """
    variables = ['latitude', 'longitude', 'pressure', 'windspeed',
                 'winddirection', 'temperature', 'dewpoint', 'gpm', 'time']

    if sounding.meta_data['bufr_msg'] == 309053:
        # Nothing to do so far
        pass
    elif sounding.meta_data['bufr_msg'] == 309056:
        # Nothing to do so far
        pass
    elif sounding.meta_data['bufr_msg'] == 309057:
        # Nothing to do so far
        pass
    return sounding


def get_sounding_direction(bufr_msg):
    """
    Get direction of sounding

    1: upward
    -1: downward
    """

    if str(bufr_msg) == '309053':
        return -1
    elif str(bufr_msg) == '309056':
        return -1
    elif str(bufr_msg) == '309057':
        return 1
    else:
        raise NotImplementedError('The bufr message format {} is not implemented'.format(bufr_msg))


def kelvin_to_celsius(kelvin):
    """
    Convert Kelvin to Celsius
    """
    return kelvin - 273.15


def pascal_to_hectoPascal(pascal):
    """
    Convert Pa to hPa
    """
    return pascal/100.


converter_dict = {'K-->C': kelvin_to_celsius,
                  'K-->degC': kelvin_to_celsius,
                  'Pa-->hPa': pascal_to_hectoPascal
                  }


def calc_relative_humidity(sounding):
    """
    Calculate relative humidity
    """
    relative_humidity = 100*(np.exp((17.625*sounding.dewpoint)/
        (243.04+sounding.dewpoint))/np.exp((17.625*sounding.temperature)/
        (243.04+sounding.temperature)))
    return relative_humidity


def calc_vapor_pressure(sounding):
    """
    Calculate water vapor pressure
    """
    vapor_pressure = (sounding.relativehumidity/100.) * (611.2 * np.exp((17.62 * (sounding.temperature))/(243.12 + sounding.temperature)))
    return vapor_pressure


def calc_wv_mixing_ratio(sounding, vapor_pressure):
    """
    Calculate water vapor mixing ratio
    """
    wv_mix_ratio = 1000.*((0.622*vapor_pressure)/(100.*sounding.pressure - vapor_pressure))
    return wv_mix_ratio


def expected_unit_check(sounding):
    """
    Check if units are as expected
    and try to convert accordingly
    """

    variables = ['displacement_lat', 'displacement_lon', 'pressure', 'windspeed',
                 'winddirection', 'temperature', 'dewpoint', 'gpm', 'time']

    expected_bufr_units = ['deg', 'deg', 'Pa', 'm/s', 'deg', 'K', 'K', 'gpm', 's']
    expected_output_units = ['deg', 'deg', 'hPa', 'm/s', 'deg', 'degC', 'degC', 'gpm', 's']

    for v, var in enumerate(variables):
        if (sounding.__dict__[var+'_unit'] != expected_output_units[v]):
            # Convert data to expected unit
            ## Find converter function
            try:
                func = converter_dict['-->'.join([sounding.__dict__[var+'_unit'], expected_output_units[v]])]
            except KeyError:
                raise UnexpectedUnit('Unit {} was expected, but got {}. Conversion was not successful'.format(expected_bufr_units[v],
                                                                           sounding.__dict__[var+'_unit']))
            else:
                sounding.__dict__[var] = func(sounding.__dict__[var])
                sounding.__dict__[var+'_unit'] = expected_output_units[v]
        else:
            pass

    return sounding


def nan_argsort(array, direction=1):
    """
    Sorting with handeling nan values
    depending on the sounding direction

    Input
    -----
    array : array-like
        data to sort
    direction : int
        integer (-1, 1) to indicate on which end
        of the sorted array nan values should be
        saved.

    Result
    ------
    indices : array
        Indices that would sort the input array
    """
    tmp = array.copy().astype('float')
    tmp[np.isnan(array)] = -np.inf*direction
    return np.argsort(tmp)


def sort_sounding_by_time(sounding):
    """
    Sort sounding by altitude
    """
    sorter = nan_argsort(sounding.time, sounding.direction)
    sounding.time = sounding.time[sorter]
    sounding.ascentrate = sounding.ascentrate[sorter]
    sounding.gpm = sounding.gpm[sorter]
    sounding.pressure = sounding.pressure[sorter]
    sounding.temperature = sounding.temperature[sorter]
    sounding.relativehumidity = sounding.relativehumidity[sorter]
    sounding.dewpoint = sounding.dewpoint[sorter]
    sounding.mixingratio = sounding.mixingratio[sorter]
    sounding.windspeed = sounding.windspeed[sorter]
    sounding.winddirection = sounding.winddirection[sorter]
    sounding.latitude = sounding.latitude[sorter]
    sounding.longitude = sounding.longitude[sorter]

    return sounding


def exclude_1000hPa_gpm(sounding):
    """
    BUFR files include values calculated for 1000 hPa
    even when the sounding starts at an higher
    elevation.

    These values are those, where time contain
    a missing value.

    This function returns the sounding
    without the missing data in the time
    dimension.
    """
    nan_mask = ~np.isnan(sounding.time)
    sounding.time = sounding.time[nan_mask]
    sounding.ascentrate = sounding.ascentrate[nan_mask]
    sounding.gpm = sounding.gpm[nan_mask]
    sounding.pressure = sounding.pressure[nan_mask]
    sounding.temperature = sounding.temperature[nan_mask]
    sounding.relativehumidity = sounding.relativehumidity[nan_mask]
    sounding.dewpoint = sounding.dewpoint[nan_mask]
    sounding.mixingratio = sounding.mixingratio[nan_mask]
    sounding.windspeed = sounding.windspeed[nan_mask]
    sounding.winddirection = sounding.winddirection[nan_mask]
    sounding.latitude = sounding.latitude[nan_mask]
    sounding.longitude = sounding.longitude[nan_mask]
    return sounding

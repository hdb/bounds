#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import shapefile
from shapely.geometry import Point
from shapely.geometry import shape
import geocoder
import folium
import argparse
import argcomplete
import inquirer
from termcolor import colored
import json
import sys
import os
from pathlib import Path
import webbrowser

def parse():

    global config_dir
    config_dir = str(Path.home())+ '/.config/bounds/'


    global default_config
    default_config = config_dir + 'bounds.json'

    global all_configs
    all_configs = [f for f in os.listdir(config_dir)]

    parser = argparse.ArgumentParser(
        prog='bounds',
        description='query address against shapefile boundaries',
        )

    #TODO add option to send map
    parser.add_argument('input', nargs='?', default=None, help='address to query against configured shp files')
    parser.add_argument('-a', '--add', default=None, help='add shapefile path to config')
    parser.add_argument('-c', '--config-file', default=default_config, help='specify config file to use').completer = ret_all_configs
    parser.add_argument('-v', '--visualize', nargs='?', default='', help='visualize map with folium and save to file. if no file is specified, a temporary map file will be created')
    parser.add_argument('-L', '--default-location', nargs='?', default='', help='configure default location (city, state, country, etc.) to append to searches. if no location is specified, will attempt to grab location from default bounds.config file')
    parser.add_argument('-G', '--google-api', nargs='?', default='', help='add Google Maps API key to configuration. if no key is specified, will attempt to grab key from default bounds.config file')

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args

def ret_all_configs(prefix, parsed_args, **kwargs):
    return (all_configs)
    
def loadConfig(configfile):

    try:
        with open(configfile, 'r') as f:
            config = json.load(f)
    except:
        config = {}

    return config

def in_config(configfile):

    try:
        with open(configfile, 'r') as f:
            config = json.load(f)
    except:
        return [[], [], []]

    ret = {}
    for x in ['include','exclude','data']:
        if x in config:
            ret[x]=config[x].copy()
        else:
            ret[x]={}
    return ret

def setConfigOpt(key, value, configfile):

    try:
        with open(configfile, 'r') as f:
            config = json.load(f)
    except:
        config = {}

    config[key] = value

    #write it back to the file
    with open(configfile, 'w') as f:
        json.dump(config, f)

    return config

def queryNewSHP(path):
    shp = shapefile.Reader(path)
    fields_exs = []
    for i, f in enumerate(shp.fields[1:]):
        if '\x00' not in str(shp.records()[0][i]):
            example = [f[0], shp.records()[0][i]]
            if len(shp.records()) > 1:
                example.append(shp.records()[1][i])
            fields_exs.append(example)
    fields_exs_formatted = [ f[0] + ' (' + str(f[1:])[1:-1] + '...)' for f in fields_exs]

    questions = [
        inquirer.List('field',
            message="Which field?:",
            choices=fields_exs_formatted,
        ),
    ]

    answers = inquirer.prompt(questions)

    input_field = fields_exs[fields_exs_formatted.index(answers["field"])][0]

    input_name = input("What should the field name be?: " )

    input_dowhat = input("Should the point be (i)nside or (o)utside? (press return to skip if only querying for data): ")

    if input_dowhat.startswith('i'):
        dowhat = 'include'
    elif input_dowhat.startswith('o'):
        dowhat = 'exclude'
    elif input_dowhat == 'q':
        exit()
    else:
        print('defaulting to reading shapefile for data')
        print()
        dowhat = 'data'

    return [dowhat, input_name, path, input_field]

def addNewSHP(dowhat, name, path, field, configfile):

    try:
        with open(configfile, 'r') as f:
            config = json.load(f)
    except:
        config = {}

    if dowhat not in config: config[dowhat] = {}

    config[dowhat][name] = {"path": os.path.realpath(path), "field": field}

    #write it back to the file
    with open(configfile, 'w') as f:
        json.dump(config, f)

    return config

def check_area(path, index, include):
    shp = shapefile.Reader(path)
    all_shapes = shp.shapes()
    all_records = shp.records()

    for i, boundary in enumerate(all_shapes):
        if point.within(shape(boundary)):

            return include, all_records[i][index]

    return not include, None

def validate_all(inclusion, exclusion, data):

    not_failed = True

    for sf in data:
        data_result = check_area(data[sf]['path'], data[sf]['field'], True)
        print(sf + ': ' + str(data_result[1]) )

    for sf in inclusion:
        in_result = check_area(inclusion[sf]['path'],inclusion[sf]['field'], True)
        if not in_result[0]:
            print(address, 'not in', sf)
            not_failed = False

    for sf in exclusion:
        out_result = check_area(exclusion[sf]['path'],exclusion[sf]['field'], False)
        if not out_result[0]:
            #if len(out_result[1]) > 0: 
            # create some way of ignoring field names when meaningless, e.g., shapefile with no attributes besides a default id=123
            print(address, 'in', out_result[1], '(' + sf + ')')
            #else:
            #     print(address, 'in', sf)
            not_failed = False

    return not_failed

def shape2json(inputfile, outfile):
    reader = shapefile.Reader(inputfile)
    fields = reader.fields[1:]
    field_names = [field[0] for field in fields]
    buffer = []
    for sr in reader.shapeRecords():
        atr = dict(zip(field_names, sr.record))
        geom = sr.shape.__geo_interface__
        buffer.append(dict(type="Feature", \
            geometry=geom, properties=atr))

    geojson = open(outfile, "w")
    geojson.write(json.dumps({"type": "FeatureCollection", "features": buffer}, indent=2, sort_keys=True, default=str) + "\n")
    geojson.close()

def display(inclusion, exclusion, data, coordinates, folium_output):
    
    m = folium.Map(location=coordinates,
        tiles='Stamen Toner', # TODO add folium config to command line? or json file?
        zoom_start=15
    )

    folium.Marker(coordinates, tooltip=address).add_to(m)

    colorstyles = { # TODO create a range of colors to use for different shapefiles?
        'data':{
            'fillColor': None,
            'color' : 'slateblue',
            'weight' : 2.5,
        },
        'inclusion':{
            'fillColor': 'green',
            'color' : None,
            'fillOpacity' : 0.3,
        },
        'exclusion':{
            'fillColor': 'red',
            'color' : None,
            'fillOpacity' : 0.6,
        },
    }

    tempdir = '/tmp/geojsons/'

    if not os.path.exists(tempdir): os.mkdir(tempdir)

    # TODO: currently creates overlays for each inclusion shapefile when it should actually be grabbing an intersection
    for sf in inclusion:

        geojsonfile = tempdir+os.path.splitext(os.path.basename(inclusion[sf]['path']))[0]
        shape2json(inclusion[sf]['path'],geojsonfile)

        geojson = folium.GeoJson(
            geojsonfile,
            name=sf,
            style_function=lambda feature: colorstyles['inclusion']
        )

        folium.Tooltip(sf).add_to(geojson)

        geojson.add_to(m)

    for sf in exclusion:

        geojsonfile = tempdir+os.path.splitext(os.path.basename(exclusion[sf]['path']))[0]
        shape2json(exclusion[sf]['path'],geojsonfile)

        geojson = folium.GeoJson(
            geojsonfile,
            name=exclusion[sf]['path'],
            style_function=lambda feature: colorstyles['exclusion']
        )

        folium.Tooltip(sf).add_to(geojson)

        geojson.add_to(m)

    # TODO displaying data maps is not useful unless individual popups are created per feature - might require separate geojsons per feature
    '''
    for sf in data:

        geojsonfile = tempdir+os.path.splitext(os.path.basename(data[sf]['path']))[0]
        shape2json(data[sf]['path'],geojsonfile)

        geojson = folium.GeoJson(
            geojsonfile,
            name=sf,
            style_function=lambda feature: colorstyles['data']
        )

        folium.Tooltip(sf).add_to(geojson)

        geojson.add_to(m)
    '''

    m.save(folium_output)
    webbrowser.open('file://' + os.path.realpath(folium_output))

def copyDefaultConfig(key, config):
    try:
        value = loadConfig(default_config)[key]
        setConfigOpt(key, value, config)
        if key == 'api_token':
            print('copied api_token to', os.path.basename(config))
        else:
            print('set', os.path.basename(config), key, 'to', value)
    except:
        print(colored(key + ' not found in ' + default_config,'red'))
        exit()


def main():

    args = parse()

    config_dir = str(Path.home())+ '/.config/bounds/'

    if args.config_file is None:
        config_file = default_config
    else:
        config_file = config_dir + args.config_file

    if args.google_api != '':

        if args.google_api is None and args.config_file != default_config:
            
            copyDefaultConfig('api_token', config_file)

        elif args.google_api is None:
            print('no token or config file specified.')
            print('add api token with `-G [TOKEN]`, or use `-c [CONFIG] -G` to copy api token from default config.')
        
        else:
            setConfigOpt('api_token', args.google_api, config_file)

    if args.add is not None:
        shpconfigdata = queryNewSHP(args.add) + [config_file]
        addNewSHP(*shpconfigdata)
    
    if args.default_location != '':

        if args.default_location is None and args.config_file != default_config:
            
            copyDefaultConfig('location', config_file)

        elif args.default_location is None:
            print('no location or config file specified.')
            print('add location with `-L [LOCATION]`, or use `-c [CONFIG] -L` to copy location from default config.')
        
        else:
            setConfigOpt('location', args.default_location, config_file)
    
    else:
        config = loadConfig(config_file)

    if args.input is None:
        exit()

    global address
    address = args.input

    try:
        search = address + ", " + config['location']
    except:
        search = address

    try:
        g = geocoder.google(search, key=config['api_token'])
    except:
        print('using OSM... (set Google Maps API token using -G [TOKEN] -c [CONFIG_FILE])')
        g = geocoder.osm(search)

    address_coordinates = g.latlng

    global point
    point = Point(address_coordinates[1],address_coordinates[0]) # an x,y tuple

    config_params = in_config(config_file)

    ret_value = validate_all(*[config_params[x] for x in config_params])

    if len(config_params['include']) + len(config_params['exclude']) > 0:

        if ret_value:
            print(colored('Bounded.','green'))
        else:
            print(colored('Not bounded', 'red'))

    if args.visualize != '':
        if args.visualize is None:
            folium_output = '/tmp/folium.html'
        else:
            folium_output = args.visualize
        
        display(*[config_params[x] for x in config_params], address_coordinates, folium_output)

if __name__ == '__main__':
    main()
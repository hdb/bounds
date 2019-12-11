# bounds

**bounds** is a command-line GIS tool to quickly determine whether a street address falls within or outside a particular set of boundaries.

## Requirements

- Python 3

## Installation

```
git clone git@github.com/hdbhdb/bounds.git
cd bounds
pip install -r requirements.txt
sudo ln bounds.py /usr/local/bin/bounds
```

## Usage

```
bounds [-h] [-a ADD] [-c CONFIG_FILE] [-v [VISUALIZE]] [-L [DEFAULT_LOCATION]]
              [-G [GOOGLE_API]]
              [input]

query address against shapefile boundaries

positional arguments:
  input                 address to query against configured shp files

optional arguments:
  -h, --help            show this help message and exit
  -a ADD, --add ADD     add shapefile path to config
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        specify config file to use
  -v [VISUALIZE], --visualize [VISUALIZE]
                        visualize map with folium and save to file. if no file is specified, a
                        temporary map file will be created
  -L [DEFAULT_LOCATION], --default-location [DEFAULT_LOCATION]
                        configure default location (city, state, country, etc.) to append to
                        searches. if no location is specified, will attempt to grab location from
                        default bounds.config file
  -G [GOOGLE_API], --google-api [GOOGLE_API]
                        add Google Maps API key to configuration. if no key is specified, will
                        attempt to grab key from default bounds.config file
```

### Adding shapefiles

Boundaries are defined by ESRI shapefiles. To add a new shapefile to the configuration, call `bounds -a shapefile.shp` which will initiate an interactive dialog:

```
[?] Which field?:: zone_class ('C2-3', 'B1-1'...)
   date_creat (datetime.date(2002, 8, 14), datetime.date(2002, 8, 29)...)
   time_creat ('00:00:00.000', '00:00:00.000'...)
   date_edit_ (datetime.date(1899, 11, 30), datetime.date(1899, 11, 30)...)
   time_edit_ ('00:00:00.000', '00:00:00.000'...)
   edit_statu ('ACTIVE', 'ACTIVE'...)
   date_ordin (datetime.date(1899, 11, 30), datetime.date(1899, 11, 30)...)
   time_ordin ('00:00:00.000', '00:00:00.000'...)
   pd_num (0.0, 0.0...)
   shape_area (41101.3463588, 3981.02012211...)
   shape_len (817.327179297, 380.062184507...)
 > zone_class ('C2-3', 'B1-1'...)
   zone_type (2.0, 1.0...)
   zoning_id (2488.0, 4088.0...)

What shold the Name be?: zone_class
Should the point be (i)nside or (o)utside? (press return to skip if only querying for data):
defaulting to reading shapefile for data
```

shapefiles can be queried for inclusion, exclusion or neither, in which case bounds will simply output the specified field of the intersecting feature.

At the moment, bounds is limited to simple **AND** logic: bounds only returns whether the address is both within all inclusion zones and outside of all exclusion zones. Pull requests / issues are welcome for supporting more complex logical relations.

### Managing Multiple Config Files

bounds allows multiple configurations which are callable with `-c`. Use `bounds -c alternate-config.json -a wetlands-swamps-us-2016.shp` to set boundaries and `bounds -c alternate-config.json '1600 Pennsylvania Ave NW, Washington, DC'` to query the address.

If you have set a Google Maps API token or location in your default configuration, you can export to other config files using `bounds -c new-config.json -G` or `bounds -c new-config.json -L` without arguments.

`bounds -c [TAB]` supports autocompletion for config files in the configuration directory (`~/.config/bounds/`). To set-up autocomplete run `echo 'eval "$(register-python-argcomplete bounds)"' >> ~/.bash_profile` and open a new terminal instance. 


### Visualizations

bounds uses [folium](https://python-visualization.github.io/folium/index.html) to display maps and defaults to using the excellent [Stamen Toner](http://maps.stamen.com/toner/) tile set. See the [quick start guide](https://python-visualization.github.io/folium/quickstart.html) for more details on configuring folium options.
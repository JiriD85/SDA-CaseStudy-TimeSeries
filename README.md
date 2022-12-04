# SDA-CaseStudy-TimeSeries

## Usage of TimeSeriesHandler.py
```
usage: TimeSeriesHandler.py [-h] [--input <filename>] [--output <filename>] [--plot] [--drop] [--iqr] [--std <std>]

optional arguments:
  -h, --help           show this help message and exit
  --input <filename>   specify the path to the input-file
  --output <filename>  specify the path to the output-file
  --plot               Show Plot (default: disabled)
  --drop               Drop outliers (default: disabled)
  --iqr                Use IQR for outlier removal (default: disabled -> Standard deviation)
  --std <std>          Standard deviations for outlier detection (default: 3)
```

## Examples
1. Example how to start TimeSeriesHandler.py with Input-file `input.log`, Output-file `output.log`, deactivated plot (plot.png will be saved in the same directory), activated Interquartile range `--iqr` for outlier removal:
`python.exe TimeSeriesHandler.py --input input.log --output output.log --iqr`

2. Example how to start TimeSeriesHandler.py with Input-file `input.log`, Output-file `output.log`, activated plot (plot.png will also be saved in the same directory), activated Standard deviation with 2 Standard deviations `--std 2`:
`python.exe TimeSeriesHandler.py --input input.log --output output.log --plot --iqr`

## Overview Methods
1. 	open_file(): Creates Dataframe from the csv- or log-file in the specified path.
2.  rename_columns(): Renames the columns in the dataframe.
3.  create_datetime(): Creates pandas Datetime in new column. Drops columns Date and Time.
4.  get_first_valid_timestamp(): Gets the first valid timestamp of the Dataframe.
5.  get_last_valid_timestamp(): Gets the last valid timestamp of the Dataframe.
6.  calculate_mean_timegap(): Calculates the mean timegap between timestamps.
7.  check_valid_date(): Checks if dates are valid. Changes invalid dates to NaT.
8.  replace_nat(): Replaces all NaT / invalid timestamps. Uses the mean timegap for calculations.
9.  format_data_columns(): Replacing Strings in Temp and Hum. Drops column TO. Converts values to float. Replaces empty string with np.nan. Creates NaN Index.
10. check_valid_value(): Checks if the values of Temp and Hum are in a valid range. Invalid values are replaced with NaN.
11. interpolate_nan(): 
12. remove_outliers()
13. plot_data()
14. export_file()
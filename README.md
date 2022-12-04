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

## Statistical Background IQR, SD and Z-Score

Boxplot (with an interquartile range) and a probability density function (pdf) of a Normal N(0,σ2) Population:
![Boxplot IQR and SD](Boxplot_IQR_SD.png)

1. **Interquartile Range:** In descriptive statistics, the interquartile range (IQR) is a measure of statistical dispersion, which is the spread of the data. It is defined as the difference between the 75th and 25th percentiles of the data. These quartiles are denoted by Q1 (also called the lower quartile), Q2 (the median), and Q3 (also called the upper quartile). The lower quartile corresponds with the 25th percentile and the upper quartile corresponds with the 75th percentile, so IQR = Q3 −  Q1. Following steps have to be followed:

- Find the first quartile, `Q1`.
- Find the third quartile, `Q3`.
- Calculate the IQR. `IQR = Q3 - Q1`.
- Define the normal data range with lower limit as `Q1 – 1.5 * IQR` and upper limit as `Q3 + 1.5 * IQR`.
- Any data point outside this range is considered as outlier and should be removed for further analysis.
- In boxplot, this IQR method is implemented to detect any extreme data points where the maximum point (the end of high whisker) is `Q3 + 1.5 * IQR` and the minimum point (the start of low whisker) is `Q1 – 1.5 * IQR`.

2. **Standard deviation:** Standard deviation method is similar to IQR procedure. Depending on the set limit either at 2 times stdev or 3 times stdev, we can detect and remove outliers from the dataset:

$$ Upper_limit = { mean + 3 * stdev } $$

$$ Lower_limit = { mean - 3 * stdev } $$

3. **Z-Score:** Z-score is just another form of standard deviation procedure. Z-score is used to convert the data into another dataset with mean = 0.

Here, $\bar x$ is the mean value and $s$ is standard deviation. Once the data is converted, the center becomes 0 and the z-score corresponding to each data point represents the distance from the center in terms of standard deviation. For example, a z-score of 2.5 indicates that the data point is 2.5 standard deviation away from the mean. Usually z-score = 3 is considered as a cut-off value to set the limit. Therefore, any z-score greater than +3 or less than -3 is considered as outlier which is pretty much similar to standard deviation method:

$$ Z = {x_{i} - \bar x \over s} $$
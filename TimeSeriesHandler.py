##############################################################################
# 						SENSOR DATA PREPROCESSING							 #
##############################################################################
"""
Name:		TimeSeriesHandler.py
Version:	1.0
Author:		Jiri Dockal
Date:		04.12.2022

This script is modifiying the content of a time-series input-file (e.g. input.log). 
The input-file MUST have this certain structure:
- Column 1 = Date
- Column 2 = Time
- Column 3 = Temperature value beginning with string "T="
- Column 4 = Humidity value beginning with string "H="
- Column 5 = TO value beginning with string "TO="

The first line of the input-file MUST contain all five columns!

Procedure:
- Creating a Dataframe from input-file
- Renaming columns of Dataframe
- Removing duplicates
- Creating Datetime columns from Date and Time
- Dropping Date and Time columns
- Checking if the Datetime values are valid, if not the values are changed to NaT
- Replacing NaT values in column Datetime
- Formating Data value columns (Replacing Strings in Temp and Hum. Dropping column TO. Converting values to float. Replacing empty string with np.nan. Creating NaN Index.)
- Checking if Temp and Hum values are in a valid range (Invalid values are replaced with NaN)
- Interpolating NaN values of Temp and Hum columns.
- Identifiyng and removing/replacing outliers (Standard deviation or Interquatrile Range)
- Creating Boxplots and Lineplots for Temp and Hum.
- Exporting Dataframe to output-file

"""

####### Import ########
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import datetime
from datetime import datetime
import warnings
warnings.filterwarnings(action='ignore')
import argparse, sys
import pathlib, os
import statistics
parent = pathlib.Path(os.path.abspath(os.path.dirname(__file__))).parent.parent
sys.path.append(f'{parent}')
from rich.console import Console

###### FileHandler ######
class FileHandler(object):

	def __init__(self, args:argparse.Namespace) -> None:
		"""
		Constructor for the FileHandler class.
		"""
		# Assume a couple of meaningful defaults here
		self.inputfile = args.inputfile,
		self.outputfile = args.outputfile,
		self.plot = args.plot,
		self.iqr = args.iqr,
		self.std = args.std,
		self.no = args.no,
		self.outlier = args.outlier,
		self.log = args.log,
		self.s = args.s,
		self.dataframe = pd.DataFrame(),
		self.first_index = 0,
		self.last_index = 0,
		self.start_time = 0,
		self.end_time = 0,
		self.mean_timegap = 0

	def open_file(self) -> None:
		"""
		Creates Dataframe from the csv- or log-file in the specified path.
		"""
		try:
			data_url = args.inputfile
			self.dataframe = pd.read_csv(data_url, sep=" ", header=None, index_col=None, on_bad_lines='skip', usecols=[0,1,2,3,4], skip_blank_lines=True)
			console.print(f'[{messageColor}]Input-file processed: {args.inputfile}')
			if bool(self.log[0]):
				self.dataframe.info()
		except OSError:
			console.print(f'[{errorColor}]OPEN FILE EXCEPTION - Cannot open Input-file: {args.inputfile}')
		except Exception as e:
			console.print(f'[{errorColor}]OPEN FILE EXCEPTION - Something strange is going on: {type(e)}')

	def export_file(self) -> None:
		"""
		Exports Dateframe to File in the specified path.
		"""
		try:
			data_url = args.outputfile
			self.dataframe.to_csv(data_url, index=False)
			console.print(f'[{messageColor}]Output-file processed: {args.outputfile}')
			if bool(self.log[0]):
				self.dataframe.info()
		except OSError:
			console.print(f'[{errorColor}]EXPORT_FILE EXCEPTION - Cannot export Output-file: {args.outputfile}')
		except Exception as e:
			console.print(f'[{errorColor}]EXPORT_FILE EXCEPTION - Something strange is going on: {type(e)}')

	def rename_columns(self) -> None:
		"""
		Renames the columns in the dataframe.
		"""
		try:
			columns = ['Date', 'Time', 'Temp', 'Hum', 'TO']
			self.dataframe.columns = columns
			console.print(f'[{messageColor}]Columns renamed: {str(columns)}')
		except Exception as e:
			console.print(f'[{errorColor}]RENAME_COLUMNS EXCEPTION - Something strange is going on: {type(e)}')

	def create_datetime(self) -> None:
		"""
		Creates pandas Datetime in new column. Drops columns Date and Time.
		"""
		try:
			# Converting colums Date + Time to new column with pd.timestamp 'Datetime'
			self.dataframe['Datetime'] = pd.to_datetime(self.dataframe['Date'] + ' ' + self.dataframe['Time'], errors="coerce")
			# Dropping Columns Date and Time
			drop = ['Date', 'Time']
			self.dataframe = self.dataframe.drop(columns=drop)
			console.print(f'[{messageColor}]Datetime created. Columns dropped: {str(drop)}')
		except Exception as e:
			console.print(f'[{errorColor}]CREATE_DATETIME EXCEPTION - Something strange is going on: {type(e)}')

	def get_first_valid_timestamp(self) -> None:
		"""
		Gets the first valid timestamp of the Dataframe.
		"""
		try:
			first_index = 0
			# looking for first valid timestamp
			for index in self.dataframe.index:
				start_time = self.dataframe['Datetime'][first_index]
				if np.isnat(np.datetime64(str(start_time))):
					first_index+=1
				else:
					first_index = first_index
			self.first_index = first_index
			self.start_time = start_time
			console.print(f'[{messageColor}]First valid Timestamp: {start_time}, index: {first_index}')
		except Exception as e:
			console.print(f'[{errorColor}]GET_FIRST_VALID_TIMESTAMP EXCEPTION - Something strange is going on: {type(e)}')

	def get_last_valid_timestamp(self) -> None:
		"""
		Gets the last valid timestamp of the Dataframe.
		"""
		try:
			last_index = len(self.dataframe['Datetime'])-1
			end_time = self.dataframe['Datetime'][last_index]

			# looking for last valid timestamp
			for index in self.dataframe.index:
				end_time = self.dataframe['Datetime'][last_index]
				if np.isnat(np.datetime64(str(end_time))):
					last_index-=1
				else:
					last_index = last_index
			self.last_index = last_index
			self.end_time = end_time
			console.print(f'[{messageColor}]Last valid Timestamp: {end_time}, index: {last_index}')
		except Exception as e:
			console.print(f'[{errorColor}]GET_LAST_VALID_TIMESTAMP EXCEPTION - Something strange is going on: {type(e)}')

	def calculate_mean_timegap(self):
		"""
		Calculates the mean timegap between timestamps.
		"""
		try:
			# calculating mean timegap between timestamps
			datetimes = self.dataframe['Datetime']
			# subtracting datetimes gives timedeltas
			timedeltas = [datetimes[i]-datetimes[i-1] for i in range(1, len(datetimes))]
			self.mean_timegap = statistics.median(timedeltas)

			console.print(f'[{messageColor}]Median Timegap between Timestamps: {self.mean_timegap}')
		except Exception as e:
			console.print(f'[{errorColor}]CALCULATE_MEAN_TIMEGAP EXCEPTION - Something strange is going on: {type(e)}')

	def check_valid_date(self):
		""" check_valid_date(self)
		Checks if the date is valid and replaces invalid dates with NaT. Calls replace_nat function to replace NaT with calculated Timestamp. 
		""" 
		now = datetime.today()
		start_time = self.start_time
		last_index = self.last_index

		try:
			# Checking for valid dates and replacing invalid dates with NaT
			if bool(self.log[0]):
				print("Change invalid Datetime to NaT...")
			for index in self.dataframe.index:

				if self.first_index >= index:
					previous_date = (self.dataframe['Datetime'][self.first_index])
				elif self.first_index == 0:
					previous_date = 0
				else: 
					previous_date = (self.dataframe['Datetime'][index-1])

				actual_date = (self.dataframe['Datetime'][index])

				if last_index > index:
					next_date = (self.dataframe['Datetime'][index+1])
				elif len(self.dataframe.index) > last_index:
					next_date = now
				else:
					print("Last valid date? --> Check file!")

				last_nat = np.isnat(np.datetime64(str(self.dataframe['Datetime'][last_index])))
				
				# Checking if Datetime is allready NaT
				if np.isnat(np.datetime64(str(self.dataframe['Datetime'][index]))):
					is_nat = True
				else:
					is_nat = False           
			
				# Change Datetime to NaT if (start_time <= datecheck <= now), if actual_date >= next_date, if duplicate

				if not is_nat:
					if not last_nat:
						if (not (start_time <= actual_date <= now)) or (actual_date >= next_date) or (previous_date >= actual_date):
							if bool(self.log[0]):
								print("df[" + str(index) + "]['Datetime']=" + str(self.dataframe['Datetime'][index]) + " is not valid! Changing invalid Date to NaT.")
							# Changing invalid Date to NaT
							self.dataframe['Datetime'][index] = str("NaT")
							#self.dataframe.loc[self.dataframe.Datetime == index] = str("NaT")
			console.print(f'[{messageColor}]Invalid Datetime replaced with NaT.')
		except Exception as e:
			console.print(f'[{errorColor}]CHECK_VALID_DATE EXCEPTION - Something strange is going on: {type(e)}, Index: {index}')

	def replace_nat(self) -> None:
		""" replace_nat(self)
		Checks the dataframe for NaT. Replaces all NaT / invalid timestamps. Uses the mean timegap for calculations.
		"""    
		try:
			nat_index = []
			mean_timegap = self.mean_timegap
			first_index = self.first_index
			self.dataframe.head(32)

			# Checking for NaT
			if bool(self.log[0]):
				print("Checking for NaT...")
			for index in self.dataframe.index:
				if np.isnat(np.datetime64(str(self.dataframe['Datetime'][index]))):
					if bool(self.log[0]):
						print("df[" + str(index) + "]['Datetime']=" + str(self.dataframe['Datetime'][index]) + ": " + str(np.isnat(np.datetime64(str(self.dataframe['Datetime'][index])))))
					nat_index.append(index)
			if bool(self.log[0]):
				print(f"Indices with NaT: {nat_index}")
				
			# #replacing NaT with calculated Timestamps
			if bool(self.log[0]):
				print("Replacing NaT with calculated Timestamps...")
			# for nat in reversed(nat_index):
			for nat in nat_index[::-1]:
				if (first_index < nat):
					if not np.isnat(np.datetime64(str(self.dataframe['Datetime'][nat - 1]))):
						self.dataframe['Datetime'][nat] = self.dataframe['Datetime'][nat - 1] + mean_timegap
					else: 
						self.dataframe['Datetime'][nat] = self.dataframe['Datetime'][nat + 1] - mean_timegap
				elif (first_index >= nat):
					self.dataframe['Datetime'][nat] = self.dataframe['Datetime'][first_index+1] - mean_timegap
					if first_index >= 1:
						first_index-=1
				else: 
					self.dataframe['Datetime'][nat] = self.dataframe['Datetime'][first_index] - mean_timegap
			
				if bool(self.log[0]):
					print("Calculated Timestamp for: df[" + str(nat) + "]['Datetime']=" + str(self.dataframe['Datetime'][nat]))
			console.print(f'[{messageColor}]NaT replaced with calculated Timestamps. Indices: {nat_index}')
		except Exception as e:
			console.print(f'[{errorColor}]REPLACE_NAT EXCEPTION - Something strange is going on: {type(e)}, Index: {index}')
			
	def format_data_columns(self) -> None:
		"""
		Replacing Strings in Temp and Hum. Drops column TO. Converts values to float. Replaces empty string with np.nan. Creates NaN Index.
		"""
		try:
			# Replacing Strings in Temp and Hum
			self.dataframe['Temp'] = self.dataframe['Temp'].str.replace('T=', '')
			self.dataframe['Hum'] = self.dataframe['Hum'].str.replace('H=', '')
			# Droping Column "TO"
			self.dataframe = self.dataframe.drop(columns=['TO'])
			# Convert each value of the column to float
			self.dataframe['Temp'] = pd.to_numeric(self.dataframe['Temp'], errors='coerce')
			self.dataframe['Hum'] = pd.to_numeric(self.dataframe['Hum'], errors='coerce')
			# Replace empty string ('') with np.nan
			self.dataframe['Temp'] = self.dataframe['Temp'].replace(r'^\s*$', np.nan, regex=True)
			self.dataframe['Hum'] = self.dataframe['Hum'].replace(r'^\s*$', np.nan, regex=True)
			# Check for NaN Index
			df_nan = self.dataframe.isna()
			nan_index = []
			for index in df_nan.index:
				if (df_nan['Temp'][index]) or (df_nan['Hum'][index]):
					nan_index.append(index)

			console.print(f'[{messageColor}]Data columns formated. Empty values replaced with NaN. Indices: {nan_index}')
		except Exception as e:
			console.print(f'[{errorColor}]FORMAT_DATA_COLUMNS EXCEPTION - Something strange is going on: {type(e)}')
	
	def check_valid_value(self) -> None:
		"""
		Checks if the values of Temp and Hum are in a valid range. Invalid values are replaced with NaN.
		"""
		valid_temp = [0, 50]  # Valid range for temperature values
		valid_hum = [0, 100]  # Valid range for humidity values
		try:
			# Create copy of the dataframe for visualization
			global df_before_check_valid_value
			df_before_check_valid_value = self.dataframe.copy(deep=True)
			# Check for valid values and remove values that not match the valid range
			nan_index = []
			for index in self.dataframe.index:
				if (self.dataframe['Temp'][index] < valid_temp[0]) or (self.dataframe['Temp'][index] > valid_temp[1]):
					self.dataframe['Temp'][index] = np.nan
					nan_index.append(index)
				if (self.dataframe['Hum'][index] < valid_hum[0]) or (self.dataframe['Hum'][index] > valid_hum[1]):
					self.dataframe['Hum'][index] = np.nan
					nan_index.append(index)

			console.print(f'[{messageColor}]Values checked. Invalid values replaced with NaN. Indices: {nan_index}')
		except Exception as e:
			console.print(f'[{errorColor}]FORMAT_DATA_COLUMNS EXCEPTION - Something strange is going on: {type(e)}')
	
	def interpolate_nan(self) -> None:
		"""
		Interpolates NaN values of Temp and Hum.
		"""
		try:
			# Interpolate NaN
			self.dataframe['Temp'] = self.dataframe['Temp'].interpolate(method='linear')
			self.dataframe['Hum'] = self.dataframe['Hum'].interpolate(method='linear')
			console.print(f'[{messageColor}]Interpolation of NaN values accomplished.')
		except Exception as e:
			console.print(f'[{errorColor}]FORMAT_DATA_COLUMNS EXCEPTION - Something strange is going on: {type(e)}')
	
	def remove_outliers(self) -> None:
		"""
		Identifies and removes/replaces outliers. Works for Standard deviation (Z-Score) and for Interquatrile Range.
		Replacement controlled via args: choices = ['remove', 'mean', 'median', 'limit', 'mode']
		"""
		# Create copy of the dataframe for visualization
		global df_before_outliers
		df_before_outliers = self.dataframe.copy(deep=True)
		try:
			outlier_temp = []
			outlier_hum = []
			mean_temp = self.dataframe['Temp'].mean()
			sd_temp = self.dataframe['Temp'].std()
			mean_hum = self.dataframe['Hum'].mean()
			sd_hum = self.dataframe['Hum'].std()
			# if arg iqr = True --> Identify outliers with Interquartile Range
			if bool(self.iqr[0]):
				# iqr
				if bool(self.log[0]):
					print(f'Removing outliers with IQR...')
				q1_temp = self.dataframe['Temp'].quantile(0.25)
				q3_temp = self.dataframe['Temp'].quantile(0.75)
				iqr_temp = q3_temp - q1_temp
				lower_limit_temp = q1_temp - 1.5 * iqr_temp
				upper_limit_temp = q3_temp + 1.5 * iqr_temp
				q1_hum = self.dataframe['Hum'].quantile(0.25)
				q3_hum = self.dataframe['Hum'].quantile(0.75)
				iqr_hum = q3_hum - q1_hum
				lower_limit_hum = q1_hum - 1.5 * iqr_hum
				upper_limit_hum = q3_hum + 1.5 * iqr_hum
				# Find outliers
				for hum in self.dataframe['Hum']:
					if (hum > upper_limit_hum) or (hum < lower_limit_hum) :
						outlier_hum.append(hum)
				for temp in self.dataframe['Temp']:
					if (temp > upper_limit_temp) or (temp < lower_limit_temp) :
						outlier_temp.append(temp)

				# Handling with outliers
				# Trimming outliers (removing)
				if (self.outlier[0] == "remove"):
					self.dataframe = self.dataframe[~((self.dataframe['Temp'] < (lower_limit_temp)) | (self.dataframe['Temp'] > (upper_limit_temp)))]
					self.dataframe = self.dataframe[~((self.dataframe['Hum'] < (lower_limit_hum)) | (self.dataframe['Hum'] > (upper_limit_hum)))]
				
				# Capping outliers (Replacing with Median)
				if (self.outlier[0] == "median"):
					self.dataframe['Temp'] = np.where(self.dataframe['Temp'] > upper_limit_temp, self.dataframe['Temp'].median(),
											np.where(self.dataframe['Temp'] < lower_limit_temp, self.dataframe['Temp'].median(), self.dataframe['Temp']))
					self.dataframe['Hum'] = np.where(self.dataframe['Hum'] > upper_limit_hum, self.dataframe['Hum'].median(),
											np.where(self.dataframe['Hum'] < lower_limit_hum, self.dataframe['Hum'].median(), self.dataframe['Hum']))
				
				# Capping outliers (Replacing with Mean)
				if (self.outlier[0] == "mean"):
					self.dataframe['Temp'] = np.where(self.dataframe['Temp'] > upper_limit_temp, self.dataframe['Temp'].mean(),
											np.where(self.dataframe['Temp'] < lower_limit_temp, self.dataframe['Temp'].mean(), self.dataframe['Temp']))
					self.dataframe['Hum'] = np.where(self.dataframe['Hum'] > upper_limit_hum, self.dataframe['Hum'].mean(),
											np.where(self.dataframe['Hum'] < lower_limit_hum, self.dataframe['Hum'].mean(), self.dataframe['Hum']))

				# Capping outliers (Replacing with Mode)
				if (self.outlier[0] == "mode"):
					self.dataframe['Temp'] = np.where(self.dataframe['Temp'] > upper_limit_temp, self.dataframe['Temp'].mode(),
											np.where(self.dataframe['Temp'] < lower_limit_temp, self.dataframe['Temp'].mode(), self.dataframe['Temp']))
					self.dataframe['Hum'] = np.where(self.dataframe['Hum'] > upper_limit_hum, self.dataframe['Hum'].mode(),
											np.where(self.dataframe['Hum'] < lower_limit_hum, self.dataframe['Hum'].mode(), self.dataframe['Hum']))

				# Capping outliers (Replacing with upper/lower limits)
				if (self.outlier[0] == "limit"):
					self.dataframe['Temp'] = np.where(self.dataframe['Temp'] > upper_limit_temp, upper_limit_temp,
											np.where(self.dataframe['Temp'] < lower_limit_temp, lower_limit_temp, self.dataframe['Temp']))
					self.dataframe['Hum'] = np.where(self.dataframe['Hum'] > upper_limit_hum, upper_limit_hum,
											np.where(self.dataframe['Hum'] < lower_limit_hum, lower_limit_hum, self.dataframe['Hum']))

			# else --> Identify outliers with Standard Deviation
			if (bool(self.std[0])):
				if bool(self.log[0]):
					print(f'Removing outliers with SD...')
				# standard deviation
				n_std = float(self.s[0])
				threshold = n_std
				# Temperature
				sd_hum = self.dataframe['Hum'].std()
				lower_limit_temp = mean_temp - (n_std*sd_temp)
				upper_limit_temp = mean_temp + (n_std*sd_temp)
				lower_limit_hum = mean_hum - (n_std*sd_hum)
				upper_limit_hum = mean_hum + (n_std*sd_hum)
				# Find outliers
				for temp in self.dataframe['Temp']:
					z = (temp - mean_temp)/sd_temp 
					if z > threshold:
						outlier_temp.append(temp)
				for hum in self.dataframe['Hum']:
					z = (hum - mean_hum)/sd_hum 
					if z > threshold:
						outlier_hum.append(hum)

				# Handling with outliers
				# Trimming outliers (removing)
				if (self.outlier[0] == "remove"):
					self.dataframe = self.dataframe[~((self.dataframe['Temp'] < (lower_limit_temp)) | (self.dataframe['Temp'] > (upper_limit_temp)))]
					self.dataframe = self.dataframe[~((self.dataframe['Hum'] < (lower_limit_hum)) | (self.dataframe['Hum'] > (upper_limit_hum)))]
				
				# Capping outliers (Replacing with Median)
				if (self.outlier[0] == "median"):
					self.dataframe['Temp'] = np.where(self.dataframe['Temp'] > upper_limit_temp, self.dataframe['Temp'].median(),
											np.where(self.dataframe['Temp'] < lower_limit_temp, self.dataframe['Temp'].median(), self.dataframe['Temp']))
					self.dataframe['Hum'] = np.where(self.dataframe['Hum'] > upper_limit_hum, self.dataframe['Hum'].median(),
											np.where(self.dataframe['Hum'] < lower_limit_hum, self.dataframe['Hum'].median(), self.dataframe['Hum']))
				
				# Capping outliers (Replacing with Mean)
				if (self.outlier[0] == "mean"):
					self.dataframe['Temp'] = np.where(self.dataframe['Temp'] > upper_limit_temp, self.dataframe['Temp'].mean(),
											np.where(self.dataframe['Temp'] < lower_limit_temp, self.dataframe['Temp'].mean(), self.dataframe['Temp']))
					self.dataframe['Hum'] = np.where(self.dataframe['Hum'] > upper_limit_hum, self.dataframe['Hum'].mean(),
											np.where(self.dataframe['Hum'] < lower_limit_hum, self.dataframe['Hum'].mean(), self.dataframe['Hum']))

				# Capping outliers (Replacing with Mode)
				if (self.outlier[0] == "mode"):
					self.dataframe['Temp'] = np.where(self.dataframe['Temp'] > upper_limit_temp, self.dataframe['Temp'].mode(),
											np.where(self.dataframe['Temp'] < lower_limit_temp, self.dataframe['Temp'].mode(), self.dataframe['Temp']))
					self.dataframe['Hum'] = np.where(self.dataframe['Hum'] > upper_limit_hum, self.dataframe['Hum'].mode(),
											np.where(self.dataframe['Hum'] < lower_limit_hum, self.dataframe['Hum'].mode(), self.dataframe['Hum']))

				# Capping outliers (Replacing with upper/lower limits)
				if (self.outlier[0] == "limit"):
					self.dataframe['Temp'] = np.where(self.dataframe['Temp'] > upper_limit_temp, upper_limit_temp,
											np.where(self.dataframe['Temp'] < lower_limit_temp, lower_limit_temp, self.dataframe['Temp']))
					self.dataframe['Hum'] = np.where(self.dataframe['Hum'] > upper_limit_hum, upper_limit_hum,
											np.where(self.dataframe['Hum'] < lower_limit_hum, lower_limit_hum, self.dataframe['Hum']))
			

			if (bool(self.no[0])):
				console.print(f'[{messageColor}]Outlier removal/replacement is deactivated.')

			if not (bool(self.no[0])):
				# Show statistical data
				if bool(self.log[0]):
					print(f'Mean Temperature: {mean_temp}')
					print(f'Standard deviation of Temperature: {sd_temp}')
					print(f'Upper Limit Temperature: {upper_limit_temp}')
					print(f'Lower Limit Temperature: {lower_limit_temp}')
					print(f'Mean Humidity: {mean_hum}')
					print(f'Standard deviation of Humidity: {sd_hum}')
					print(f'Upper Limit Humidity: {upper_limit_hum}')
					print(f'Lower Limit Humidity: {lower_limit_hum}')

			if not (bool(self.no[0])):
				# Show Outliers	
				console.print(f'[{messageColor}]Temperature Outliers in dataset: {outlier_temp}')
				console.print(f'[{messageColor}]Humidity Outliers in dataset: {outlier_hum}')
				console.print(f'[{messageColor}]{len(outlier_temp) + len(outlier_hum)} Outliers removed.')
		except Exception as e:
			console.print(f'[{errorColor}]REPLACE_OUTLIERS EXCEPTION - Something strange is going on: {type(e)}')

	def drop_duplicates(self) -> None:
		"""
		Drops duplicates. Running this will keep one instance of the duplicated row, and remove all those after.
		"""
		try:
			self.dataframe = self.dataframe.drop_duplicates()
			console.print(f'[{messageColor}]Dropping duplicates.')
		except Exception as e:
			console.print(f'[{errorColor}]REPLACE_OUTLIERS EXCEPTION - Something strange is going on: {type(e)}')

	def plot_data(self) -> None:
		"""
		Creates Boxplots and Lineplots for Time series Temp and Hum. For a better data comparison two dataframes are compared to each other (before and after outlier removal). If plot = True a plot opened during runtime.
		"""
		try:
			# Dataframes
			data_raw = df_before_check_valid_value
			data_before = df_before_outliers
			data_after = self.dataframe
			# Create Plot
			fig, ax = plt.subplots(3, 2, figsize=(14,10))
			fig.subplots_adjust(hspace=0.5)
			# Plot Title
			if bool(self.std[0]):
				fig.suptitle(f'Sensor Data: Humidity and Temperature (Outlier removal with Standard deviation: SD = {int(self.s[0])} )')
			else:
				fig.suptitle('Sensor Data: Humidity and Temperature (Outlier removal with Interquartile Range: Q1 = 0.25, Q3 = 0.75 )')
			# Boxplot
			ax[0,0].set_xlim(0,150)
			ax[1,0].set_xlim(0,150)
			ax[2,0].set_xlim(0,150)
			ax[0,0].set_title('Boxplot before removal of invalid values')
			ax[1,0].set_title('Boxplot before outlier removal')
			ax[2,0].set_title('Boxplot after outlier removal')
			ax[0,0].set_xlabel('Values')
			ax[1,0].set_xlabel('Values')
			ax[2,0].set_xlabel('Values')
			sns.boxplot(ax=ax[0,0], data=data_raw[['Temp', 'Hum']], orient="h")
			sns.boxplot(ax=ax[1,0], data=data_before[['Temp', 'Hum']], orient="h")
			sns.boxplot(ax=ax[2,0], data=data_after[['Temp', 'Hum']], orient="h")
			# Lineplot
			ax[0,1].set_title('Lineplot before removal of invalid values')
			ax[1,1].set_title('Lineplot before outlier removal')
			ax[2,1].set_title('Lineplot after outlier removal')
			ax[0,1].set_xlabel('Measurements')
			ax[1,1].set_xlabel('Measurements')
			ax[2,1].set_xlabel('Measurements')
			sns.lineplot(ax=ax[0,1], data=data_raw[['Temp', 'Hum']])
			sns.lineplot(ax=ax[1,1], data=data_before[['Temp', 'Hum']])
			sns.lineplot(ax=ax[2,1], data=data_after[['Temp', 'Hum']])
			# Save Plot
			fig.savefig('plot.png')
			# Show Plot
			if bool(self.plot[0]):
				plt.show()
			console.print(f'[{messageColor}]Data plot accomplished: plot.png')
		except Exception as e:
			console.print(f'[{errorColor}]PLOT_DATA EXCEPTION - Something strange is going on: {type(e)}')

###### MAIN - argparse ######
highlightColor = 'blue'
messageColor = 'spring_green2'
errorColor = 'red'
	
if __name__ == '__main__':
	console = Console()

	# parse command line argiments
	parser = argparse.ArgumentParser()

	# arguments
	outlier = parser.add_mutually_exclusive_group(required=True)
	parser.add_argument('-i','--input', action='store', required=True, dest='inputfile', metavar='<filename>', help='Specify the path to the input-file')
	parser.add_argument('-o','--output', action='store', required=True, dest='outputfile', metavar='<filename>', help='Specify the path to the output-file')
	parser.add_argument('-p','--plot', action='store_true', dest='plot', default=False, help='Show Plot (default: disabled)')
	outlier.add_argument('-iq','--iqr', action='store_true', dest='iqr', default=False, help='Use IQR for outlier identification (default: disabled)')
	outlier.add_argument('-st','--std', action='store_true', dest='std', default=False, help='Use Z-Score for outlier identification (default: disabled)')
	outlier.add_argument('-no','--noremoval', action='store_true', dest='no', default=False, help='No outlier removal (default: disabled)')
	parser.add_argument('-u','--outlier', action='store', required=True, dest='outlier', metavar='<choice>', choices = ['remove', 'mean', 'median', 'limit', 'mode', 'ignore'], help='Choose outlier replacement method. Choices: [remove, mean, median, limit, mode, ignore]')
	parser.add_argument('-z','--zscore', action='store', dest='s', default=3, metavar='<s>', required='--std' in sys.argv, type=float, help='Z-Score for outlier detection (default: 3)')
	parser.add_argument('-l','--log', action='store_true', dest='log', default=False, help='Show detailed logs (default: disabled)')
	
	args = parser.parse_args()

	console.print(f'\n[{highlightColor}][bold]Case Study - Time Series - Dockal - TimeSeriesHandler.py STARTED![/bold]\n\n')

###### Sensor Data Application #######
try:
	file = FileHandler(args)
	file.open_file()
	file.rename_columns()
	file.drop_duplicates() # Firstly to remove all duplicates that have been imported via input-file
	file.create_datetime()
	file.get_first_valid_timestamp()
	file.get_last_valid_timestamp()
	file.calculate_mean_timegap()
	file.check_valid_date()
	file.replace_nat()
	file.format_data_columns()
	file.check_valid_value()
	file.interpolate_nan()
	file.remove_outliers()
	file.drop_duplicates() # Secondly to remove all duplicates that may heve been created due to replace_nat or interpolate_nan
	file.plot_data()
	file.export_file()

except KeyboardInterrupt as e:
	console.print(f'[{messageColor}]Keyboard Interrupt!')
except Exception:
	console.print()
	console.print_exception()
finally:
	console.print(f'\n[{highlightColor}][bold]Case Study - Time Series - Dockal - TimeSeriesHandler.py STOPPED![/bold]\n')
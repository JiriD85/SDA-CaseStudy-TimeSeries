##############################################################################
# 						SENSOR DATA PREPROCESSING							 #
##############################################################################

####### Import ########
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import datetime
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings(action='ignore')
import argparse, sys
import pathlib, os
parent = pathlib.Path(os.path.abspath(os.path.dirname(__file__))).parent.parent
sys.path.append(f'{parent}')
from rich.console import Console

###### Variables #######
highlightColor = 'blue'
messageColor = 'spring_green2'
errorColor = 'red'
valid_temp = [-20, 50]  # Wertebereich Temperatur
valid_hum = [0, 100]    # Wertebereich Luftfeuchtigkeit

###### FileHandler ######
class FileHandler(object):

	def __init__(self, args:argparse.Namespace) -> None:
		# Assume a couple of meaningful defaults here
		self.inputfile = args.inputfile,
		self.outputfile = args.outputfile,
		self.plot = args.plot,
		self.drop = args.drop,
		self.iqr = args.iqr,
		self.std = args.std,
		self.dataframe = pd.DataFrame(),
		self.first_index = 0,
		self.last_index = 0,
		self.start_time = 0,
		self.end_time = 0,
		self.mean_timegap = 0

	def open_file(self) -> None:
		try:
			data_url = args.inputfile
			self.dataframe = pd.read_csv(data_url, sep=" ", header=None, index_col=None)
			console.print(f'[{messageColor}]Input-file processed: {args.inputfile}')
			self.dataframe.info()
		except OSError:
			console.print(f'[{errorColor}]Cannot open Input-file: {args.inputfile}')

	def export_file(self) -> None:
		try:
			data_url = args.outputfile
			self.dataframe.to_csv(data_url, index=False)
			console.print(f'[{messageColor}]Output-file processed: {args.outputfile}')
			self.dataframe.info()
		except OSError:
			console.print(f'[{errorColor}]Cannot export Output-file: {args.outputfile}')

	def rename_columns(self) -> None:
		try:
			columns = ['Date', 'Time', 'Temp', 'Hum', 'TO']
			self.dataframe.columns = columns
			console.print(f'[{messageColor}]Columns renamed: {str(columns)}')
		except Exception as e:
			console.print(f'[{errorColor}]EXCEPTION - Something strange is going on: {type(e)}')

	def create_datetime(self) -> None:
		try:
			# Converting colums Date + Time to new column with pd.timestamp 'Datetime'
			self.dataframe['Datetime'] = pd.to_datetime(self.dataframe['Date'] + ' ' + self.dataframe['Time'], errors="coerce")
			# Dropping Columns Date and Time
			drop = ['Date', 'Time']
			self.dataframe = self.dataframe.drop(columns=drop)
			console.print(f'[{messageColor}]Datetime created. Columns dropped: {str(drop)}')
		except Exception as e:
			console.print(f'[{errorColor}]EXCEPTION - Something strange is going on: {type(e)}')

	def get_first_valid_timestamp(self) -> None:
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
			console.print(f'[{errorColor}]EXCEPTION - Something strange is going on: {type(e)}')

	def get_last_valid_timestamp(self) -> None:
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
			console.print(f'[{errorColor}]EXCEPTION - Something strange is going on: {type(e)}')

	def calculate_mean_timegap(self):
		try:
			# calculating mean timegap between timestamps
			self.mean_timegap = (self.end_time - self.start_time) / (self.last_index - self.first_index)
			self.mean_timegap = pd.to_timedelta(str(self.mean_timegap)).round('1s')
			console.print(f'[{messageColor}]Mean Timegap between Timestamps: {self.mean_timegap}')
		except Exception as e:
			console.print(f'[{errorColor}]EXCEPTION - Something strange is going on: {type(e)}')

	def check_valid_date(self):
		""" check_valid_date(self)
		Checks if the date is valid and replaces invalid dates with NaT. Calls replace_nat function to replace NaT with calculated Timestamp. 
		""" 
		now = datetime.today()
		start_time = self.start_time
		last_index = self.last_index

		try:
			# Checking for valid dates and replacing invalid dates with NaT
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
							print("df[" + str(index) + "]['Datetime']=" + str(self.dataframe['Datetime'][index]) + " is not valid! Changing invalid Date to NaT.")
							# Changing invalid Date to NaT
							self.dataframe['Datetime'][index] = str("NaT")
							#self.dataframe.loc[self.dataframe.Datetime == index] = str("NaT")
			console.print(f'[{messageColor}]Invalid Datetime replaced with NaT.')
		except Exception as e:
			console.print(f'[{errorColor}]CHECK_VALID_DATE EXCEPTION - Something strange is going on: {type(e)}, Index: {index}')

	def replace_nat(self) -> None:
		""" replace_nat(df, mean_timegap)
		Checks the dataframe for NaT. Replaces NaT with calculated Timestamp values.
		"""    
		try:
			nat_index = []
			mean_timegap = self.mean_timegap
			first_index = self.first_index
			self.dataframe.head(32)

			# Checking for NaT
			print("Checking for NaT...")
			for index in self.dataframe.index:
				if np.isnat(np.datetime64(str(self.dataframe['Datetime'][index]))):
					print("df[" + str(index) + "]['Datetime']=" + str(self.dataframe['Datetime'][index]) + ": " + str(np.isnat(np.datetime64(str(self.dataframe['Datetime'][index])))))
					nat_index.append(index)
			print(f"Indices with NaT: {nat_index}")
				
			# #replacing NaT with calculated Timestamps
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
					if first_index > 1:
						first_index-=1
				else: 
					self.dataframe['Datetime'][nat] = self.dataframe['Datetime'][first_index] - mean_timegap
			
				print("Calculated Timestamp for: df[" + str(nat) + "]['Datetime']=" + str(self.dataframe['Datetime'][nat]))
			console.print(f'[{messageColor}]NaT replaced with calculated Timestamps. Indices: {nat_index}')
		except Exception as e:
			console.print(f'[{errorColor}]REPLACE_NAT EXCEPTION - Something strange is going on: {type(e)}, Index: {index}')
			
	def format_data_columns(self) -> None:
		try:
			# Replacing Strings in Temp and Hum, Dropping TO
			self.dataframe['Temp'] = self.dataframe['Temp'].str.replace('T=', '')
			self.dataframe['Hum'] = self.dataframe['Hum'].str.replace('H=', '')
			# Droping Column "TO"
			self.dataframe = self.dataframe.drop(columns=['TO'])
			# Convert each value of the column to a string
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
	
	def interpolate_nan(self) -> None:
		try:
			# Interpolate NaN
			self.dataframe['Temp'] = self.dataframe['Temp'].interpolate(method='linear')
			self.dataframe['Hum'] = self.dataframe['Hum'].interpolate(method='linear')
			console.print(f'[{messageColor}]Interpolation of NaN values accomplished.')
		except Exception as e:
			console.print(f'[{errorColor}]FORMAT_DATA_COLUMNS EXCEPTION - Something strange is going on: {type(e)}')
	
	def remove_outliers(self) -> None:
			try:
				# Create copy of the dataframe for visualization
				global df_before_outliers
				df_before_outliers = self.dataframe.copy(deep=True)
				# if arg iqr = True --> Identify outliers with Interquartile Range
				if bool(self.iqr[0]):
					# iqr
					q1_temp = self.dataframe['Temp'].quantile(0.25)
					q3_temp = self.dataframe['Temp'].quantile(0.75)
					iqr_temp = q3_temp - q1_temp
					q1_hum = self.dataframe['Hum'].quantile(0.25)
					q3_hum = self.dataframe['Hum'].quantile(0.75)
					iqr_hum = q3_temp - q1_temp
					self.dataframe = self.dataframe[~((self.dataframe['Temp'] < (q1_temp - 1.5 * iqr_temp)) | (self.dataframe['Temp'] > (q3_temp + 1.5 * iqr_temp)))]
					self.dataframe = self.dataframe[~((self.dataframe['Hum'] < (q1_hum - 1.5 * iqr_hum)) | (self.dataframe['Hum'] > (q3_hum + 1.5 * iqr_hum)))]
				# else --> Identify outliers with Standard Deviation
				else:
					# standard deviation
					n_std = int(self.std[0])
					# Temperature
					mean = self.dataframe['Temp'].mean()
					sd = self.dataframe['Temp'].std()
					self.dataframe = self.dataframe[(self.dataframe['Temp'] <= mean+(n_std*sd))]
					self.dataframe = self.dataframe[(self.dataframe['Hum'] <= mean+(n_std*sd))]	
					# Humidity
					mean = self.dataframe['Hum'].mean()
					sd = self.dataframe['Hum'].std()
				# if arg drop = True
				# if bool(self.drop[0]):
					# Outlier Identification -> NaN -> Replace NaN
				console.print(f'[{messageColor}]Outliers removed.')
			except Exception as e:
				console.print(f'[{errorColor}]REPLACE_OUTLIERS EXCEPTION - Something strange is going on: {type(e)}')

	def plot_data(self) -> None:
			try:
				# Dataframes
				data_before = df_before_outliers
				data_after = self.dataframe
				# Create Plot
				fig, ax = plt.subplots(2, 2, figsize=(14,7))
				fig.subplots_adjust(hspace=0.5)
				fig.suptitle('Sensor Data: Humidity and Temperature')
				# Boxplot
				ax[0,0].set_xlim(0,150)
				ax[1,0].set_xlim(0,150)
				ax[0,0].set_title('Boxplot before outlier removal')
				ax[1,0].set_title('Boxplot after outlier removal')
				ax[0,0].set_xlabel('Values')
				ax[1,0].set_xlabel('Values')
				sns.boxplot(ax=ax[0,0], data=data_before[['Temp', 'Hum']], orient="h")
				sns.boxplot(ax=ax[1,0], data=data_after[['Temp', 'Hum']], orient="h")
				# Lineplot
				ax[0,1].set_title('Lineplot before outlier removal')
				ax[1,1].set_title('Lineplot after outlier removal')
				ax[0,1].set_xlabel('Measurements')
				ax[1,1].set_xlabel('Measurements')
				sns.lineplot(ax=ax[0,1], data=data_before[['Temp', 'Hum']])
				sns.lineplot(ax=ax[1,1], data=data_after[['Temp', 'Hum']])
				# Save Plot
				fig.savefig('plot.png')
				# Show Plot
				if bool(self.plot[0]):
					plt.show()
				console.print(f'[{messageColor}]Data plot accomplished.')
			except Exception as e:
				console.print(f'[{errorColor}]PLOT_DATA EXCEPTION - Something strange is going on: {type(e)}')

###### MAIN - argparse ######
	
if __name__ == '__main__':
	console = Console()
	console.print(f'\n[{highlightColor}][bold]Case Study - Time Series - Dockal - STARTED![/bold]\n\n')

	# parse command line argiments
	parser = argparse.ArgumentParser()

	# arguments
	parser.add_argument('--input', action='store', dest='inputfile', metavar='<filename>', help='specify the path to the input-file')
	parser.add_argument('--output', action='store', dest='outputfile', metavar='<filename>', help='specify the path to the output-file')
	parser.add_argument('--plot', action='store_true', dest='plot', default=False, help='Show Plot (default: disabled)')
	parser.add_argument('--drop', action='store_true', dest='drop', default=False, help='Drop outliers (default: disabled)')
	parser.add_argument('--iqr', action='store_true', dest='iqr', default=False, help='Use IQR for outlier removal (default: disabled -> Standard deviation)')
	parser.add_argument('--std', action='store', dest='std', default=3, metavar='<std>', type=int, help='Standard deviations for outlier detection (default: 3)')
	
	args = parser.parse_args()

###### Sensor Data Application #######
try:
	file = FileHandler(args)
	file.open_file()
	file.rename_columns()
	#check if values are valid. if not --> drop invalid lines at the end and the beginning
	file.create_datetime()
	file.get_first_valid_timestamp()
	file.get_last_valid_timestamp()
	file.calculate_mean_timegap()
	file.check_valid_date()
	file.replace_nat()
	file.format_data_columns()
	file.interpolate_nan()
	file.remove_outliers()
	file.plot_data()
	file.export_file()

except KeyboardInterrupt as e:
	console.print(f'[{messageColor}]Keyboard Interrupt!')
except Exception:
	console.print()
	console.print_exception()
finally:
	console.print(f'\n[{highlightColor}][bold]Case Study - Time Series - Dockal - STOPPED![/bold]\n')
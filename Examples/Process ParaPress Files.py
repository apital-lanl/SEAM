from Pressure import ParaPress

#Date format is 'YEAR-MONTH-DAY-HHMMSS'  i.e. 2021-01-01-000000
initial_starting_datetime = ''
last_data_datetime = ''

# data channels = [1, 2, 3, 4,5 ,6, 7,8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
#       ch.20 is typically a vacuum-line-monitoring channel
# temp channels = [21, 22]
#       ch. 21 is the Friocell interior channel
#       ch. 22 is room temperature channel
channels_to_collect = []


filenames_dict = ParaPress.select_from_dir(channels=[], start_date = '', end_date ='')
# filenames_dict = ParaPress.select_files(channels = [], start_date = '', end_date ='')  #For individual file selection; otherwise it's a pain

pressure_dataframe = ParaPress.filenames_to_dataframe(filenames_dict, 
                                                      plot_block = True, 
                                                      datetime_coerce = 'latest',
                                                      main_directory = '')

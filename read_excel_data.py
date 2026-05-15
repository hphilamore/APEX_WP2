import pandas as pd
import numpy as np
from read_excel_data_funcs import *

# import torch
# import torch.nn as nn
# import torch.nn.functional as F

file_path = "Biosensor data from the start (13-06-24) until 06-01-25.xlsx"

def main():

    # Import data as multi-sheet data frame 
    data = import_excel_data(file_path)

    # Combine as new single sheet data frame, that concatenates data from all pages ordered chronologically 
    all_data = pd.concat(data.values(), ignore_index=True)

    print('length', len(all_data))

    # Sort by date time
    all_data = all_data.sort_values("datetime").reset_index(drop=True)


    # Get names of columns containing MFC voltage data 
    mfc_column_names = extract_mfc_column_names(all_data)

    # Number of columns containing MFC voltage
    n_mfcs = len(mfc_column_names)
    N = n_mfcs + 1

    # Create column of forward-filled COD values for each MFC
    for n in list(range(1,N)):
        all_data["COD_filled_" + str(n)] = all_data["COD" + str(n)].ffill()
        
    # Create column with event flag (1 at COD measurement points, 0 elsewhere) for each MFC 
    for n in list(range(1,N)):
        all_data["COD_event_" + str(n)] = (~all_data["COD" + str(n)].isna()).astype(int)

    # Separate into dictionary of indiviudal MFCs time series data frames
    all_data_separate = separate_mfc_data(all_data, mfc_column_names)

    # Save data
    # df = pd.DataFrame(all_data)
    pd.to_pickle(all_data, "all_data.pkl")

    # dfs = {name: pd.DataFrame(sheet) for name, sheet in all_data_separate.items()}
    pd.to_pickle(all_data_separate, "all_data_separate.pkl")
    
    # all_data = pd.read_pickle("all_data.pkl")

    # # Plot data
    # plot_data(all_data, mfc_column_names, title="all MFCs")


    # # Dictionary to store computed information for each MFC
    # mfc_analysis = {
    #     "Spike delay (days)" : {},

    # }

    # for d in all_data_separate:

    #     print()
    #     print(d)

    #     all_data_separate[d]['Power W'] = all_data_separate["Voltage"] * all_data_separate["Resistance"]**2

    #     data = all_data_separate[d]

    #     # mfc_analysis[d] = {}

    #     # Get index of COD events
    #     cod_events_idx = data.index[data["COD_event"] == 1].to_numpy()
    #     # print('number of cod events ', len(cod_events_idx))

    #     # Get time of COD events
    #     cod_events_time = data["datetime"].iloc[cod_events_idx]
    #     print('COD event times \n', cod_events_time)

    #     # Store index of voltage peaks
    #     voltage_peaks_idx = []

    #     # Get window of voltage data following each COD event
    #     for i in range(len(cod_events_idx)):
    #         start = cod_events_idx[i] 

    #         if i < len(cod_events_idx) - 1:
    #             end = cod_events_idx[i+1]
    #             window = data['Voltage'].iloc[start:end]

    #         # Last segment of data
    #         else:
    #             window = data['Voltage'].iloc[start:]

    #         if len(window) > 0:

    #             # Find maximum voltage recorded in this window (voltage peak)
    #             local_max_pos = np.nanargmax(window.values)

    #             # Convert to global index
    #             max_idx = start + local_max_pos

    #             # Store index of voltage peak
    #             voltage_peaks_idx.append(max_idx)

    #     # print('number of voltage peaks ', len(voltage_peaks_idx))

    #     # Get time of voltage peaks
    #     peak_times = data["datetime"].iloc[voltage_peaks_idx]
    #     print('Voltage peak times \n',peak_times)

    #     # print('Voltage peak values \n',peak_times)
    #     # print(data["Voltage"].iloc[voltage_peaks_idx])

    #     # # Plot seperate data for each MFC
    #     # plot_data(data, 
    #     #           ["Voltage"], 
    #     #           title=d, 
    #     #           voltage_peaks=voltage_peaks_idx)

    #     # Compute time from COD event to voltage spike 
    #     spike_delay_days = [(t2 - t1).total_seconds() / (60 * 60 * 24) for t1, t2 in zip(cod_events_time, peak_times)]
    #     spike_delay_days = [round(i, 5) for i in spike_delay_days]
    #     # print('Delay between COD event and voltage spike (days) ', spike_delay_mins)

    #     mfc_analysis["Spike delay (days)"][d] = spike_delay_days

    #     # Plot seperate data for each MFC
    #     plot_data(data, 
    #               ["Power"], 
    #               title=d)
        
    #     # # Count number of COD events
    #     # n_cod_events_idx = data["COD_event"].sum()
    #     # print(f"number of COD events {d} ", n_cod_events_idx)

    # # for key, value in mfc_analysis["Spike delay (days)"].items():
    # #     print(key, '\t', value)
    # #     if key=='8) 10*10 -2':
    # #         continue
    # #     if '10*10' in key:
    # #         c = 'red'
    # #         if 'AC' in key:
    # #             c = 'orange'
    # #     else:
    # #         c = 'blue'
    # #         if 'AC' in key:
    # #             c = 'green'
    # #     plt.plot(value, label=key, color=c, marker='o', linestyle='none')
    # # plt.xlabel('spike number')
    # # plt.ylabel('spike delay(days)')
    # # plt.ylim(0, 10)
    # # plt.legend()
    # # plt.show()

    

    # # Convert to DataFrame (each list becomes a column)
    # df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in mfc_analysis["Spike delay (days)"].items()]))

    # # Save to Excel
    # df.to_excel("Spike_delay_days.xlsx", index=False)


        
if __name__ == "__main__":
    main()
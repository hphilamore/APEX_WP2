import pandas as pd
import numpy as np
from read_excel_data_funcs import *

# import torch
# import torch.nn as nn
# import torch.nn.functional as F

file_path = "Biosensor data from the start (13-06-24) until 06-01-25_.xlsx"

def main():

    # Import data as multi-sheet data frame 
    data = import_excel_data(file_path)

    # Combine as new single sheet data frame, that concatenates data from all pages ordered chronologically 
    all_data = pd.concat(data.values(), ignore_index=True)

    print('length', len(all_data))

    # Sort by date time
    all_data = all_data.sort_values("datetime").reset_index(drop=True)

    # # Create column of sparse COD values
    # all_data["COD_raw"] = all_data["COD"]

    # Columns containing MFC voltage data 
    mfc_cols = [col for col in all_data.columns if not col.startswith(('COD', 
                                                                       'Resistance', 
                                                                       'TYE', 
                                                                       'datetime')
                                                                     )]

    # Number of columns containing MFC voltage
    n_mfcs = len(mfc_cols)
    N = n_mfcs + 1

    # Create column of forward-filled COD values for each MFC
    for n in list(range(1,N)):
        all_data["COD_filled_" + str(n)] = all_data["COD" + str(n)].ffill()
        
    # Create column with event flag (1 at COD measurement points, 0 elsewhere) for each MFC 
    for n in list(range(1,N)):
        all_data["COD_event_" + str(n)] = (~all_data["COD" + str(n)].isna()).astype(int)

    # print(all_data.head())

    # Plot data
    plot_data(all_data, mfc_cols, title="all MFCs")

    # Separate into dictionary of indiviudal MFCs time series data
    all_data_separate = separate_mfc_data(all_data, mfc_cols)

    for d in all_data_separate:

        print()
        print(d)

        data = all_data_separate[d]

        samples_per_day = 2880 

        # Get indices of COD events
        cod_events = data.index[data["COD_event"] == 1].to_numpy()
        print('number of cod events ', len(cod_events))

        cod_times = data["datetime"].iloc[cod_events]
        print(cod_times)

        selected_indices = []

        # Get window of voltage data following each COD event
        for i in range(len(cod_events)):
            start = cod_events[i] 

            if i < len(cod_events) - 1:
                end = cod_events[i+1]
                window = data['Voltage'].iloc[start:end]

            else:
                # Last segment of data
                window = data['Voltage'].iloc[start:]

            if len(window) > 0:
                # Find maximum voltage recorded in this window (voltage peak)
                local_max_pos = np.nanargmax(window.values)

                # Convert to global index
                max_idx = start + local_max_pos

                selected_indices.append(max_idx)

        print('number of voltage peaks ', len(selected_indices))

        peak_times = data["datetime"].iloc[selected_indices]
        print(peak_times)

        print(data["Voltage"].iloc[selected_indices])

        # # Plot seperate data
        # plot_data(data, ["Voltage"], title=d, voltage_peaks=True)
        plot_data(data, ["Voltage"], title=d, voltage_peaks=selected_indices)

        # # Count number of COD events
        # n_cod_events = data["COD_event"].sum()
        # print(f"number of COD events {d} ", n_cod_events)
        
if __name__ == "__main__":
    main()
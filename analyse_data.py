import pandas as pd
import numpy as np
from read_excel_data_funcs import *

def main():
    # Load stored data
    all_data = pd.read_pickle("all_data.pkl")

    # Convert index to date time format
    all_data = all_data.set_index("datetime", drop=False).sort_index()

    # Select date range to work on 
    all_data = all_data.loc["2024-10-01":"2024-10-30 23:59:59"]

    # Get names of columns containing MFC voltage data
    mfc_column_names = extract_mfc_column_names(all_data)

    # Plot all voltage data
    plot_data(all_data, cols_to_plot=mfc_column_names, title="all MFCs")

    # Separate into dictionary of indiviudal MFCs time series data
    all_data_separate = separate_mfc_data(all_data, mfc_column_names)

    # Dictionary to store computed information for each MFC
    mfc_analysis = {
        "Spike delay (days)" : {},
    }

    for d in all_data_separate:

        print()
        print(d)
        data = all_data_separate[d]

        # Compute power output as time series
        data['Power W'] = data["Voltage"] * data["Resistance"]**2

        # Get index of COD events
        cod_events_idx = data.index[data["COD_event"] == 1].to_numpy()
        # print('number of cod events ', len(cod_events_idx))

        # # Get time of COD events
        # cod_events_time = data["datetime"].iloc[cod_events_idx]
        # print('COD event times \n', cod_events_time)

        # # Get index of voltage peaks
        # voltage_peaks_idx = []

        # # Get window of voltage data following each COD event
        # for i in range(len(cod_events_idx)):
        #     start = cod_events_idx[i] 

        #     if i < len(cod_events_idx) - 1:
        #         end = cod_events_idx[i+1]
        #         window = data['Voltage'].iloc[start:end]

        #     # Last segment of data
        #     else:
        #         window = data['Voltage'].iloc[start:]

        #     if len(window) > 0:

        #         # Find maximum voltage recorded in this window (voltage peak)
        #         local_max_pos = np.nanargmax(window.values)

        #         # Convert to global index
        #         max_idx = start + local_max_pos

        #         # Store index of voltage peak
        #         voltage_peaks_idx.append(max_idx)

        # # print('number of voltage peaks ', len(voltage_peaks_idx))

        # # Get time of voltage peaks
        # peak_times = data["datetime"].iloc[voltage_peaks_idx]
        # print('Voltage peak times \n',peak_times)

        # # print('Voltage peak values \n',peak_times)
        # # print(data["Voltage"].iloc[voltage_peaks_idx])

        # # Plot voltage data for each MFC, showing peaks
        # plot_data(data, 
        #           ["Voltage"], 
        #           title=d, 
        #           voltage_peaks=voltage_peaks_idx)

        # # Compute and store delay between COD event and voltage spike 
        # spike_delay_days = [(t2 - t1).total_seconds() / (60 * 60 * 24) for t1, t2 in zip(cod_events_time, peak_times)]
        # spike_delay_days = [round(i, 5) for i in spike_delay_days]
        # mfc_analysis["Spike delay (days)"][d] = spike_delay_days
        # df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in mfc_analysis["Spike delay (days)"].items()]))
        # df.to_excel("Spike_delay_days.xlsx", index=False)



    #     # Plot seperate data for each MFC
    #     plot_data(data, 
    #               ["Power"], 
    #               title=d)
        

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


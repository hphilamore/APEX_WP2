import pandas as pd
import numpy as np
from read_excel_data_funcs import *
import pickle

# feature_data_file_path = "mfc_features.xlsx"
feature_data_file_name = "mfc_features"

# def extract_features_to_excel(output_file_path=feature_data_file_path):
def extract_and_store_features(input_file_path="all_data.pkl", 
                               output_file_name=feature_data_file_name,
                               window_length_hours = 0):
    
    # Load stored data
    all_data = pd.read_pickle(input_file_path)

    # Convert index to date time format
    all_data = all_data.set_index("datetime", drop=False).sort_index()

    # Select date range to work on 
    # all_data = all_data.loc["2024-08-01":"2024-08-28 23:59:59"]

    # View different timesteps included in data
    # time_diffs = all_data.index.to_series().diff()
    # print(time_diffs.head())
    # print(time_diffs.value_counts())


    # Get names of columns containing MFC voltage data
    mfc_column_names = extract_mfc_column_names(all_data)

    # Plot all voltage data
    plot_data(all_data, cols_to_plot=mfc_column_names, 
              title="all MFCs", 
              show_plot=False
              )

    # Separate into dictionary of indiviudal MFCs time series data
    all_mfc_data_separate = separate_mfc_data(all_data, mfc_column_names)

    # ---------------------------------------------------------------
    # Compute/extract parameters for each COD event, for each MFC
    # ---------------------------------------------------------------

    # Dictionary to store computed/extracted parameters
    mfc_features = {
        "COD date time index" : {},
        "Window length (hours)" : {},
        "COD" : {},
        "Resistance kOhms" : {},
        "Vpeak mV": {}, 
        "Ppeak W": {}, 
        "Vfinal mV": {}, 
        "Pfinal W": {}, 
        "Rise time (days)" : {},
        # "Decay slope (V per s)" : {},
        "Energy J": {},
        "Vwindow mV": {},
        "Pwindow W": {},
        "Timewindow": {},       # timestamp for every voltage sample
        "COD_event_window": {},       # 1 before/at peak, 0 after peak
    }

    # Dates to index mfc analysis dictionary with 
    # cod_events_dates = []
    # cod_events_idx = []

    # window_size_max = 0

    # Iterate over all MFCs 
    for mfc in all_mfc_data_separate:
        print()
        print(mfc)
        data = all_mfc_data_separate[mfc]

        # Set negative voltage values to 0
        data["Voltage mV"] = data["Voltage mV"].clip(lower=0)

        # Set nan voltage values to 0
        data["Voltage mV"] = data["Voltage mV"].fillna(0)

        # Compute column showing MFC power output
        data['Power W'] = (data["Voltage mV"]/1000)**2 / (data["Resistance kOhms"]*1000)

        for feature in mfc_features:
            mfc_features[feature][mfc] = []

        # ------------------------------------------------------
        # -------- Extract features for each COD event ---------
        # ------------------------------------------------------

        # -------- COD events ---------
        # Get date-time index of COD events 
        cod_events_idx = data.index[data["COD_event"] == 1]
        mfc_features["COD date time index"][mfc] = cod_events_idx

        # Store COD values
        COD_vals = list(data.loc[cod_events_idx, "COD"])
        # mfc_features["COD"][mfc] = list(data.loc[cod_events_idx, "COD"])
        mfc_features["COD"][mfc] = COD_vals

        # -------- Resistance --------
        # Store Resistance value assocaited with each COD event 
        resistance_vals = list(data.loc[cod_events_idx, "Resistance kOhms"])
        mfc_features["Resistance kOhms"][mfc] = resistance_vals

        # Arrays to store index of voltage peaks for each COD event
        voltage_peaks_idx = []
        
        # Get window of data following each COD event
        # for i in range(len(cod_events_idx)):
        for i, j in zip(range(len(cod_events_idx)), COD_vals):
            start = cod_events_idx[i]
            print(mfc, "COD=", j)
            print("start", start)

            # Set end of window
            if window_length_hours > 0:
                # Find closest data point to desired window length
                end_actual = start + pd.Timedelta(hours=window_length_hours)
                end = data.index.asof(end_actual)

                mask = (data.index >= start) & (data.index < end)

                # mfc_features["Window length (hours)"][mfc].append(window_length_hours)

            elif i < len(cod_events_idx) - 1:
                end = cod_events_idx[i+1]
                mask = (data.index >= start) & (data.index < end)
                # mfc_features["Window length (hours)"][mfc].append(0)
            
            # Last segment of data 
            else:
                mask = (data.index >= start) 
                # mfc_features["Window length (hours)"][mfc].append(0)

            # Select window of data
            window = data.loc[mask]
            print('Window length', len(window))

            # Get the window of voltage and power data
            V_window = window['Voltage mV']
            P_window = window['Power W']

            # # Update maximum window size
            # window_size = len(V_window)
            # # print(window_size)
            # if window_size > window_size_max:
            #     window_size_max = window_size

            # time_difference = end - start
            # print(time_difference)

            # If there is data in the window
            if V_window.notna().any():

                # -------- Max voltage value --------
                peak_idx = V_window.idxmax()
                V_peak = V_window.loc[peak_idx]
                print("peak", peak_idx)
                print("peak voltage mV", V_peak)
                
                # -------- Power at the max voltage value (i.e. max power becuase R is constant) --------        
                P_peak = P_window.loc[peak_idx]

                # -------- COD event labels --------
                # Get the integer index the peak in the window
                peak_position = V_window.index.get_loc(peak_idx)

                # Use this to create an array of 1s up to the peak and 0s after
                COD_event_labels = np.zeros(len(V_window), dtype=np.float32)
                COD_event_labels[:peak_position + 1] = 1

                label_series = pd.Series(COD_event_labels,
                                         index=V_window.index
)
                # -------- Final voltage value --------
                V_final = V_window.iloc[-1]
                # print(V_final)

                # -------- Final power value --------
                P_final = P_window.iloc[-1]
                # print(P_final)

                # -------- Rise time (time from COD event to voltage peak) --------
                rise_time = (peak_idx - start).total_seconds() / (60 * 60 * 24)  

                # -------- Decay slope --------
                # Define end of window
                window_end = window.index[-1]

                # Get closest index 1 day after peak
                # one_day_after_peak = peak_idx + pd.Timedelta(days=1)
                one_hour_after_peak = peak_idx + pd.Timedelta(hours=1)
                one_hour_after_peak = window.index.asof(one_hour_after_peak)

                # Take whichever comes first as end of slope period
                t_end = min(one_hour_after_peak, window_end)
                # print(t_end)

                # Compute time difference in seconds
                dt = (t_end - peak_idx).total_seconds()
                # print(dt)

                # Compute the slope of voltage decay w.r.t time 
                # decay_slope = (V_window.loc[t_end] - V_peak) / dt
                # print(V_window.loc[t_end])
                # print(decay_slope)
                # print()

            else:
                peak_idx = None
                V_peak = None
                P_peak = None
                V_final = None
                P_final = None
                rise_time = np.nan
                # decay_slope = np.nan

            print(V_window.tolist()[:10])
            print(COD_event_labels.tolist()[:10])
            print(V_window.index.copy().tolist()[:10])
            print()

            # Store features for this data window
            voltage_peaks_idx.append(peak_idx)
            mfc_features["Window length (hours)"][mfc].append(window_length_hours)
            mfc_features["Vwindow mV"][mfc].append(V_window.tolist())
            mfc_features["Pwindow W"][mfc].append(P_window.tolist())
            mfc_features["Vpeak mV"][mfc].append(V_peak)
            mfc_features["Ppeak W"][mfc].append(P_peak)
            mfc_features["Vfinal mV"][mfc].append(V_final)
            mfc_features["Pfinal W"][mfc].append(P_final)
            mfc_features["Rise time (days)"][mfc].append(round(rise_time, 6))
            mfc_features["Timewindow"][mfc].append(V_window.index.copy().tolist())
            mfc_features["COD_event_window"][mfc].append(COD_event_labels.tolist())
            # mfc_features["Decay slope (V per s)"][mfc].append(round(decay_slope, 6))

            # -------- Energy generated per COD event ---------
            # Time axis of the window is every value minus the start value, expressed in seconds
            t = (window.index - window.index[0]).total_seconds()

            # Get the series of power values in the window
            power = window['Power W'].values

            # Replace any nan power values with 0
            power = np.nan_to_num(power, nan=0.0)

            # Compute the total energy as the time integral of power
            energy = np.trapezoid(power, t)

            mfc_features["Energy J"][mfc].append(round(energy, 3))

            # plt.figure()
            # plt.plot(V_window.index, V_window, label="Voltage")
            # plt.plot(V_window.index, COD_event_labels, label="COD label")
            # plt.title(f"{mfc}, COD={j}")
            # plt.xlabel("Time")
            # plt.legend()
            # plt.show()

        # -----------------------------------------------
        # -------- Plot voltage peaks ---------
        # -----------------------------------------------

        # Plot voltage data, showing peaks
        plot_data(data, 
                  ["Voltage mV"], 
                  title=mfc, 
                  voltage_peaks=voltage_peaks_idx,
                  show_days=False,
                  show_plot=False
                  )
        
        plot_data(data, 
                  ["Power W"], 
                  title=mfc, 
                  voltage_peaks=voltage_peaks_idx,
                  show_days=False,
                  show_plot=False
                  )
        
    # print('Window size max', window_size_max)

    # Pad all time series windows with zero to equal length of largest window 
    # for time_series_feature in ['Vwindow mV', 'Pwindow W']:
    #     for mfc, data in mfc_features[time_series_feature].items():
    #         for i, sample in enumerate(data):
    #             current_length = len(sample)
    #             # print(current_length)
    #             if current_length < window_size_max:
    #                 padding = [0] * (window_size_max - current_length)
    #                 data[i] = sample + padding

    # Verify padding worked
    # for mfc, data in mfc_features['Vwindow mV'].items():
    #     for i, sample in enumerate(data):
    #         current_length = len(sample)
    #         print(current_length)
    # for mfc, data in mfc_features['Pwindow W'].items():
    #     for i, sample in enumerate(data):
    #         current_length = len(sample)
    #         print(current_length)
    

    # Save nested dictionary of {features : {mfc names : mfc data}} to pickle file
    with open(output_file_name+".pkl", 'wb') as f:
        pickle.dump(mfc_features, f)

    # # ---------------------------------------------------------------
    # # -------- Save COD event features to excel file ---------
    # # ---------------------------------------------------------------

    # Get string representation of dates of COD events
    cod_events_str = [d.strftime('%d/%m/%Y') for d in cod_events_idx.date]

    # Convert each feature to datastrcuture in order to save to excel file for human readbility   
    with pd.ExcelWriter(output_file_name+".xlsx") as writer:

        for sheet in mfc_features:

            # Skip saving time series features to excel
            if isinstance(mfc_features[sheet][mfc][0], 
                          (list, tuple, dict, set, np.ndarray, pd.Series, pd.DataFrame)):
                # print(f"skipping {sheet}")
                continue

            # Convert each feature to dataframe with all mfc columns
            df = pd.DataFrame({k: pd.Series(v) for k, v in mfc_features[sheet].items()})
            
            # Set your custom datetime index
            # df.index = cod_events_idx
            df.index = cod_events_str

            # Name it so Excel column is labeled nicely
            df.index.name = "Date"

            # Write to excel file
            # mfc_features[sheet].to_excel(writer, sheet_name=sheet, index=False)
            df.to_excel(writer, sheet_name=sheet)


if __name__ == "__main__":
    extract_and_store_features(input_file_path="all_data.pkl",
                               output_file_name=feature_data_file_name,
                            #    window_length_hours=1
                               )


import pandas as pd
import numpy as np
from read_excel_data_funcs import *
import pickle

# feature_data_file_path = "mfc_features.xlsx"
feature_data_file_path = "mfc_features.pkl"

# def extract_features_to_excel(output_file_path=feature_data_file_path):
def extract_and_store_features(output_file_path=feature_data_file_path):

    # Load stored data
    all_data = pd.read_pickle("all_data.pkl")

    # Convert index to date time format
    all_data = all_data.set_index("datetime", drop=False).sort_index()

    # Select date range to work on 
    # all_data = all_data.loc["2024-08-01":"2024-08-28 23:59:59"]

    # Get names of columns containing MFC voltage data
    mfc_column_names = extract_mfc_column_names(all_data)

    # Plot all voltage data
    plot_data(all_data, cols_to_plot=mfc_column_names, title="all MFCs", 
              show_plot=False
              )

    # Separate into dictionary of indiviudal MFCs time series data
    all_data_separate = separate_mfc_data(all_data, mfc_column_names)

    # ---------------------------------------------------------------
    # Compute/extract parameters for each COD event, for each MFC
    # ---------------------------------------------------------------

    # Dictionary to store computed/extracted parameters
    mfc_features = {
        "COD" : {},
        "Resistance kOhms" : {},
        "Vpeak mV": {}, 
        "Ppeak W": {}, 
        "Rise time (days)" : {},
        "Decay slope (V per s)" : {},
        "Energy J": {},
        "Vwindow mV": {},
        "Pwindow W": {},
    }

    # Dates to index mfc analysis dictionary with 
    cod_events_dates = []
    # cod_events_idx = []

    # Iterate over MFCs 
    for d in all_data_separate:
        print()
        print(d)
        data = all_data_separate[d]

        # Add column showing MFC power output
        data['Power W'] = (data["Voltage mV"]/1000)**2 / (data["Resistance kOhms"]*1000)

        for key in mfc_features:
            mfc_features[key][d] = []

        # ------------------------------------------------------
        # -------- Extract features for each COD event ---------
        # ------------------------------------------------------

        # -------- COD events ---------
        # Get date-time index of COD events 
        cod_events_idx = data.index[data["COD_event"] == 1]
        # print(cod_events_idx)

        # # Store the date of each COD event for the first MFC in the data set to use later as an index for all MFCs
        if len(cod_events_dates) == 0:
            cod_events_dates = cod_events_idx.strftime('%Y-%m-%d').tolist()
            print(cod_events_dates)
            # Save list of COD event date-time indexes 
            with open("COD_event_dates.pkl", "wb") as f:
                pickle.dump(cod_events_dates, f)

        # Store COD values
        mfc_features["COD"][d] = list(data.loc[cod_events_idx, "COD"])

        # -------- Resistance --------
        # Store Resistance values
        mfc_features["Resistance kOhms"][d] = list(data.loc[cod_events_idx, "Resistance kOhms"])

        # Arrays to store index of voltage peaks for each COD event
        voltage_peaks_idx = []

        # Get window of data following each COD event
        for i in range(len(cod_events_idx)):
            start = cod_events_idx[i] 
            if i < len(cod_events_idx) - 1:
                end = cod_events_idx[i+1]
                mask = (data.index >= start) & (data.index < end)
            # Last segment of data 
            else:
                mask = (data.index >= start) 
            window = data.loc[mask]

            # Get the window of voltage data
            V_window = window['Voltage mV']

            # If there is data in the window
            if V_window.notna().any():

                # -------- Index of the max voltage value --------
                peak_idx = V_window.idxmax()
 
                # -------- Rise time (time from COD event to voltage peak) --------
                rise_time = (peak_idx - start).total_seconds() / (60 * 60 * 24)

                # -------- Max voltage value --------
                V_peak = V_window.loc[peak_idx]

                # -------- Power at the max voltage value --------
                P_window = window['Power W']
                P_peak = P_window.loc[peak_idx]

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
                decay_slope = (V_window.loc[t_end] - V_peak) / dt
                # print(V_window.loc[t_end])
                # print(decay_slope)
                # print()

            else:
                peak_idx = None
                V_peak = None
                P_peak = None
                rise_time = np.nan
                decay_slope = np.nan

            voltage_peaks_idx.append(peak_idx)


            # Store features for this data window
            mfc_features["Vwindow mV"][d].append(V_window.tolist())
            mfc_features["Pwindow W"][d].append(P_window.tolist())
            mfc_features["Vpeak mV"][d].append(V_peak)
            mfc_features["Ppeak W"][d].append(P_peak)
            mfc_features["Rise time (days)"][d].append(round(rise_time, 6))
            mfc_features["Decay slope (V per s)"][d].append(round(decay_slope, 6))

            
            # -------- Energy generated per COD event ---------
            # Time axis of the window is every value minus the start value, expressed in seconds
            t = (window.index - window.index[0]).total_seconds()

            # Get the power values in the window
            power = window['Power W'].values

            # Replace any nan power values with 0
            power = np.nan_to_num(power, nan=0.0)

            # Compute the total energy as the time integral of power
            energy = np.trapezoid(power, t)

            mfc_features["Energy J"][d].append(round(energy, 3))

        # -----------------------------------------------
        # -------- Plot voltage peaks ---------
        # -----------------------------------------------

        # Plot voltage data, showing peaks
        plot_data(data, 
                  ["Voltage mV"], 
                  title=d, 
                  voltage_peaks=voltage_peaks_idx,
                  show_days=False,
                  show_plot=False
                  )


    # Save nested dictionary of {features : {mfc names : mfc data}} to pickle file
    with open(output_file_path, 'wb') as f:
        pickle.dump(mfc_features, f)





    # # ---------------------------------------------------------------
    # # -------- Save COD event features to excel file ---------
    # # ---------------------------------------------------------------

    # print(type(cod_events_idx[0]))

    # # cod_events_idx = [d.strftime('%d/%m/%Y') for d in cod_events_idx.date]

    # print(type(cod_events_idx[0]))


    # # # # Save features and time series data to pickle file
    # # # with open('mfc_features.pkl', 'wb') as f:
    # # #     pickle.dump(mfc_features, f)

    # # Convert each feature to datastrcuture and save features to excel file  
    # with pd.ExcelWriter(output_file_path) as writer:

    #     for sheet in mfc_features:

    #         # Don't save long time series data to excel
    #         if sheet in ["Vwindow mV", "Pwindow W"]:
    #             continue

    #         # Convert all nested dictionaries to DataFrames in place
    #         mfc_features[sheet] = pd.DataFrame(
    #             {k: pd.Series(v) for k, v in mfc_features[sheet].items()}
    #             )
            
    #         # Set your custom datetime index
    #         mfc_features[sheet].index = cod_events_idx

    #         # Name it so Excel column is labeled nicely
    #         mfc_features[sheet].index.name = "Date"

    #         # Write to excel file
    #         # mfc_features[sheet].to_excel(writer, sheet_name=sheet, index=False)
    #         mfc_features[sheet].to_excel(writer, sheet_name=sheet)

    # # Save features and time series data to pickle file
    # with open('mfc_features.pkl', 'wb') as f:
    #     pickle.dump(mfc_features, f)


if __name__ == "__main__":
    extract_and_store_features(output_file_path=feature_data_file_path)


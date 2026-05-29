import pandas as pd
import numpy as np
from read_excel_data_funcs import *

def main():
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
    mfc_analysis = {
        "COD" : {},
        "Resistance kOhms" : {},
        "Vpeak mV": {}, 
        "Ppeak W": {}, 
        "Rise time (days)" : {},
        "Decay slope (V per s)" : {},
        "Energy J": {},
    }

    # Dates to index mfc analysis dictionary with 
    cod_events_dates = []

    # Iterate over MFCs 
    for d in all_data_separate:
        print()
        print(d)
        data = all_data_separate[d]

        # Add column showing MFC power output
        data['Power W'] = (data["Voltage mV"]/1000)**2 / (data["Resistance kOhms"]*1000)

        for key in mfc_analysis:
            mfc_analysis[key][d] = []

        # ------------------------------------------------------
        # -------- Extract features for each COD event ---------
        # ------------------------------------------------------

        # -------- COD events ---------
        # Get date-time index of COD events
        cod_events_idx = data.index[data["COD_event"] == 1]

        if not cod_events_dates:
            cod_events_dates = [d.isoformat() for d in cod_events_idx.date.tolist()]
            

        # Store COD values
        mfc_analysis["COD"][d] = list(data.loc[cod_events_idx, "COD"])

        # -------- Resistance --------
        # Store Resistance values
        mfc_analysis["Resistance kOhms"][d] = list(data.loc[cod_events_idx, "Resistance kOhms"])

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
            mfc_analysis["Vpeak mV"][d].append(V_peak)
            mfc_analysis["Ppeak W"][d].append(P_peak)
            mfc_analysis["Rise time (days)"][d].append(round(rise_time, 6))
            mfc_analysis["Decay slope (V per s)"][d].append(round(decay_slope, 6))

            
            # -------- Energy generated per COD event ---------

            # Time axis of the window is every value minus the start value, expressed in seconds
            t = (window.index - window.index[0]).total_seconds()

            # Get the power values in the window
            power = window['Power W'].values

            # Replace any nan power values with 0
            power = np.nan_to_num(power, nan=0.0)
            
            # Compute the total energy as the time integral of power
            mfc_analysis["Energy J"][d].append(np.trapezoid(power, t))

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

      
    # ---------------------------------------------------------------
    # -------- Statistical analysis of MFCs grouped by type ---------
    # ---------------------------------------------------------------

    # Save COD event parameters to excel file  
    with pd.ExcelWriter("mfc_analysis.xlsx") as writer:

        for sheet in mfc_analysis:

            # Convert all nested dictionaries to DataFrames in place
            mfc_analysis[sheet] = pd.DataFrame(
                {k: pd.Series(v) for k, v in mfc_analysis[sheet].items()}
                )
            
            # Set custom index
            mfc_analysis[sheet].index = cod_events_dates

            # Name the index column
            mfc_analysis[sheet].index.name = "Date"
            
            # Write to excel file
            mfc_analysis[sheet].to_excel(writer, sheet_name=sheet)

    # Regex patterns for each MFC type to filter data
    patterns = {
        "10x10_AC": r"10\*10\s*AC",
        "20x30_AC": r"20\*30\s*AC",
        "10x10": r"10\*10(?!\s*AC)",   # match 10*10 NOT followed by AC
        "20x30": r"20\*30(?!\s*AC)"    # match 20*30 NOT followed by AC
    }

    # ---------------------------------------------------------------
    # -------- Min, max, mean rise time and total energy for each COD event ---------
    # ---------------------------------------------------------------
    for parameter in ["Rise time (days)", "Energy J"]:
    
        summary = {}

        plt.figure(figsize=(16, 6))

        for mfc_type, pattern in patterns.items():

            # Select only columns that match the heading name pettern
            cols = mfc_analysis[parameter].filter(regex=pattern)   

            # Compute the COD event-wise (i.e. row-wise) min, max, mean
            summary[mfc_type] = {
                "min": cols.min(axis=1),
                "max": cols.max(axis=1),
                "mean": cols.mean(axis=1)
            }

            number_of_COD_events = len(summary[mfc_type]["mean"])

            COD_event_numbers = range(number_of_COD_events)

            # Plot COD event-wise mean
            plt.plot(COD_event_numbers, 
                    summary[mfc_type]["mean"], 
                    label=mfc_type)

            # Shade area between min and max
            plt.fill_between(COD_event_numbers, 
                            summary[mfc_type]['min'], 
                            summary[mfc_type]['max'], 
                            alpha=0.3)

        plt.legend()
        plt.xticks(COD_event_numbers)  # only integers
        plt.xlabel('COD event index')
        plt.ylabel(parameter)
        plt.savefig(f"figs/{parameter}.png")
        # plt.show()

        # print(summary)

    
    # ---------------------------------------------------------------
    # -------- Vpeak // Ppeak // Ener vs COD, coloured by resistance, seperate plot or marker style for each MFC type  ---------
    # ---------------------------------------------------------------

    for parameter in ["Vpeak mV", "Ppeak W", "Energy J"]:

        df_param = mfc_analysis[parameter]
        df_cod = mfc_analysis["COD"]
        df_res = mfc_analysis["Resistance kOhms"]

        for mfc_type, pattern in patterns.items():

            # Select matching columns
            param = df_param.filter(regex=pattern)
            cod = df_cod.filter(regex=pattern)
            res = df_res.filter(regex=pattern)

            # Ensure same column order
            cod = cod[param.columns]
            res = res[param.columns]

            # Flatten to 1D arrays
            x = cod.values.flatten()
            y = param.values.flatten()
            r = res.values.flatten()

            # Remove NaNs (important for plotting)
            mask = ~np.isnan(x) & ~np.isnan(y) & ~np.isnan(r)
            x, y, r = x[mask], y[mask], r[mask]

            # Create plot
            plt.figure(figsize=(10, 6))

            # Get unique resistance values 
            unique_r_vals = sorted(np.unique(r))

            # colors = plt.cm.tab10(range(len(unique_vals)))
            # colours = ["red", "cyan", "green"]

            # Gnerate colour map
            colours = ["red", "cyan", "green"]
            colour_map = dict(zip(unique_r_vals, colours))

            # Plot each resistance group separately
            for val in unique_r_vals: 
                # Get index of equal resistance values
                idx = r == val

                x_ = x[idx]
                y_ = y[idx]
                
                # Plot points from this resistance group
                plt.scatter(x_, 
                            y_, 
                            # color=col, 
                            color=colour_map.get(val, "black"), # Use colour map or default to black
                            label=f"R = {val} kOhm")
                

                # Linear fit

                # Fit line: y = m*x + c
                m, c = np.polyfit(x_, y_, 1)

                # Generate fitted line
                x_fit = np.linspace(min(x_), max(x_), 100)
                y_fit = m * x_fit + c

                # Compute R²

                # Predicited y values using linear equation
                y_pred = m * x_ + c

                # Residual sum of squared error between actual and predicted y values
                ss_res = np.sum((y_ - y_pred) ** 2)

                # total sum of squared error between actual and mean y values
                ss_tot = np.sum((y_ - np.mean(y_)) ** 2)

                # Compute R² with mechnism for 0 division handling
                r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan

                # Plot fitted line
                plt.plot(
                    x_fit,
                    y_fit,
                    color=colour_map.get(val, "black"),
                    linestyle='--'
                )

                # Add R² label to legend
                plt.plot([], [], ' ', label=f"R² (R={val} kOhm) = {r2:.2f}")


            plt.xlabel("COD")
            plt.ylabel(parameter)
            plt.title(parameter + " vs COD - " + mfc_type)
            plt.subplots_adjust(right=0.75)
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
            plt.savefig(f"figs/{parameter} vs COD - {mfc_type}.png")
            # plt.show()

if __name__ == "__main__":
    main()


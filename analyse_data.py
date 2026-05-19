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
            #   show_plot=False
              )

    # Separate into dictionary of indiviudal MFCs time series data
    all_data_separate = separate_mfc_data(all_data, mfc_column_names)

    

    # ---------------------------------------------------------------
    # Compute/extract parameters for each COD event, for each MFC
    # ---------------------------------------------------------------

    # Dictionary to store computed/extracted parameters
    mfc_analysis = {
        "Energy J": {},
        "Resistance kOhms" : {},
        "COD" : {},
        "Vpeak mV": {}, 
        "Ppeak W": {}, 
        "Spike delay (days)" : {},
    }

    # Iterate over MFCs 
    for d in all_data_separate:
        print()
        print(d)
        data = all_data_separate[d]

        # ------------------------------
        # -------- Extract COD ---------
        # ------------------------------
        
        # Get date-time index of COD events
        cod_events_idx = data.index[data["COD_event"] == 1]

        # Store COD values
        mfc_analysis["COD"][d] = list(data.loc[cod_events_idx, "COD"])

        # -------------------------------------
        # -------- Extract Resistance ---------
        # -------------------------------------
        
        # Store Resistance values
        mfc_analysis["Resistance kOhms"][d] = list(data.loc[cod_events_idx, "Resistance kOhms"])

        # --------------------------------------------------------------
        # -------- Compute values for each event in COD window ---------
        # --------------------------------------------------------------

        # Arrays to store values computed for each COD event
        voltage_peaks_idx = []
        power_peaks_idx = []
        voltage_peaks = []
        power_peaks = []
        energy = []

        # print(data["Voltage mV"][:10])

        # Compute mfc power output time series
        data['Power W'] = (data["Voltage mV"]/1000)**2 / (data["Resistance kOhms"]*1000)

        # print(data['Power W'][:10])

        # -------------------------------------------------
        # -------- Compute peak power and voltage ---------
        # -------------------------------------------------

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

            # Find peak voltage and power values in this window
            for parameter, idxs, vals in zip(
                                            ['Voltage mV', 'Power W'], 
                                            [voltage_peaks_idx, power_peaks_idx],
                                            [voltage_peaks, power_peaks]
                                            ):
                # Get the window of data for the selected parameter (voltage or power)
                param = window[parameter]

                # If there is data in the window, compute the max value
                if param.notna().any():
                    peak_idx = param.idxmax()
                    peak_val = param.loc[peak_idx]
                else:
                    peak_idx = None
                    peak_val = None
                    
    #             # print('Peak '+ parameter + ':', peak_idx, peak_val)

                # Store index of the peak
                idxs.append(peak_idx)
                vals.append(peak_val)

            # -------------------------------------------
            # -------- Compute Energy generated ---------
            # -------------------------------------------

            # Get the time axis of the window 
            t = (window.index - window.index[0]).total_seconds()

            # Get the power values in the window
            power = window['Power W'].values

            # Replace any nan power values with 0
            power = np.nan_to_num(power, nan=0.0)

            # print(t[:10])
            # print(power[:10])
            
            # Compute the total energy as the time integral of power
            energy.append(np.trapezoid(power, t))

        # --------------------------------------
        # -------- Store energy values ---------
        # --------------------------------------
        mfc_analysis["Energy J"][d] = energy

        # -----------------------------------------------
        # -------- Store and plot voltage peaks ---------
        # -----------------------------------------------

        mfc_analysis["Vpeak mV"][d] = voltage_peaks

        # Plot voltage data, showing peaks
        plot_data(data, 
                  ["Voltage mV"], 
                  title=d, 
                  voltage_peaks=voltage_peaks_idx,
                  show_days=True,
                  show_plot=False
                  )

        # --------------------------------------
        # -------- Store power peaks -----------
        # --------------------------------------

        mfc_analysis["Ppeak W"][d] = power_peaks
        
        # -----------------------------------------------------------------
        # -------- Store delay between COD event and voltage peak ---------
        # -----------------------------------------------------------------

        # Compute and store delay between COD event and voltage spike
        spike_delay_days = []
        for c, v in zip(cod_events_idx, voltage_peaks_idx):
            if v:
                delay = (v - c).total_seconds() / (60 * 60 * 24)
            else:
                delay = np.nan
            spike_delay_days.append(delay)
        # Round to 6 d.p.
        spike_delay_days = [round(i, 6) for i in spike_delay_days]
        mfc_analysis["Spike delay (days)"][d] = spike_delay_days

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
            
            # Write to excel file
            # mfc_analysis[sheet].to_excel(writer, sheet_name=sheet, index=False)
            mfc_analysis[sheet].to_excel(writer, sheet_name=sheet)


    # Regex patterns for each MFC type to filter data
    patterns = {
        "10x10_AC": r"10\*10\s*AC",
        "20x30_AC": r"20\*30\s*AC",
        "10x10": r"10\*10(?!\s*AC)",   # match 10*10 NOT followed by AC
        "20x30": r"20\*30(?!\s*AC)"    # match 20*30 NOT followed by AC
    }

    # ---------------------------------------------------------------
    # -------- Min, max, mean spike delay and total energy for each COD event ---------
    # ---------------------------------------------------------------
    for parameter in ["Spike delay (days)", "Energy J"]:
    
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
        plt.savefig("figs/" + parameter + "Spike_delay_days.png")
        plt.show()

        print(summary)

    
    # ---------------------------------------------------------------
    # -------- Vpeak vs COD, coloured by resistance, seperate plot or marker style for each MFC type  ---------
    # ---------------------------------------------------------------

    
    df_vpeak = mfc_analysis["Vpeak mV"]
    df_cod = mfc_analysis["COD"]
    df_res = mfc_analysis["Resistance kOhms"]

    for mfc_type, pattern in patterns.items():

        # Select matching columns
        cod = df_cod.filter(regex=pattern)
        vpeak = df_vpeak.filter(regex=pattern)
        res = df_res.filter(regex=pattern)

        # Ensure same column order
        cod = cod[vpeak.columns]
        res = res[vpeak.columns]

        # Flatten to 1D arrays
        x = cod.values.flatten()
        y = vpeak.values.flatten()
        r = res.values.flatten()

        # Remove NaNs (important for plotting)
        mask = ~np.isnan(x) & ~np.isnan(y) & ~np.isnan(r)
        x, y, r = x[mask], y[mask], r[mask]

        # Create plot
        plt.figure(figsize=(16, 6))

        # Get unique resistance values 
        unique_vals = sorted(np.unique(r))

        # colors = plt.cm.tab10(range(len(unique_vals)))
        # colours = ["red", "cyan", "green"]

        # Gnerate colour map
        colours = ["red", "cyan", "green"]
        colour_map = dict(zip(unique_vals, colours))

        # Plot each resistance group separately
        for val, col in zip(unique_vals, colours):
            # Get index of equal resistance values
            idx = r == val
            
            # Plot points from this resistance group
            plt.scatter(x[idx], 
                        y[idx], 
                        # color=col, 
                        color=colour_map.get(val, "black"), # Use colour map or default to black
                        label=f"R = {val} kOhm")

        plt.xlabel("COD")
        plt.ylabel("Vpeak mV")
        plt.title(mfc_type)
        plt.legend()
        plt.show()

    # ---------------------------------------------------------------
    # -------- Ppeak vs COD, coloured by resistance, seperate plot or marker style for each MFC type  ---------
    # ---------------------------------------------------------------

    # ---------------------------------------------------------------
    # -------- Energy vs COD, coloured by resistance, seperate plot or marker style for each MFC type  ---------
    # ---------------------------------------------------------------



if __name__ == "__main__":
    main()


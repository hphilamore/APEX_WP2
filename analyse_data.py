import pandas as pd
import numpy as np
from read_excel_data_funcs import *

def main():
    # Load stored data
    all_data = pd.read_pickle("all_data.pkl")

    # Convert index to date time format
    all_data = all_data.set_index("datetime", drop=False).sort_index()

    # Select date range to work on 
    all_data = all_data.loc["2024-08-01":"2024-08-28 23:59:59"]

    # Get names of columns containing MFC voltage data
    mfc_column_names = extract_mfc_column_names(all_data)

    # Plot all voltage data
    plot_data(all_data, cols_to_plot=mfc_column_names, title="all MFCs", show_plot=False)

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

        print(data["Voltage mV"][:10])

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
            # Translate dictionary to data frame
            df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in mfc_analysis[sheet].items()]))  
            df.to_excel(writer, sheet_name=sheet, index=False)
            # print(df)

    # # MFC types
    # mfc_groups = { '10*10 AC':{}, 
    #             '20*30 AC':{}, 
    #             '10*10':{}, 
    #             '20*30':{}
    #             }

    
    # # Group spike delay data by MFC type and compute min, max, mean for each COD event 
    # for i, mfc_type in zip(range(0, df.shape[1], 3), mfc_groups):

    #     # Take columns in groups of 3
    #     group = df.iloc[:, i:i+3]

    #     mfc_groups[mfc_type]['min'] = group.min(axis=1)
    #     mfc_groups[mfc_type]['max'] = group.max(axis=1)
    #     mfc_groups[mfc_type]['mean'] = group.mean(axis=1)

    #     event_number = range(len(mfc_groups[mfc_type]['mean']))   

    #     # Plot spike delay data
    #     plt.plot(event_number, mfc_groups[mfc_type]['mean'], label=mfc_type)

    #     # shaded area between min and max
    #     plt.fill_between(x, mfc_groups[mfc_type]['min'], mfc_groups[mfc_type]['max'], alpha=0.3)

    # print(mfc_groups)
    # plt.legend()
    # plt.xticks(x)  # only integers
    # plt.xlabel('COD event index')
    # plt.ylabel('Delay from COD event to voltage peak (days)')
    # plt.savefig("Spike_delay_days.png")
    # plt.show()


if __name__ == "__main__":
    main()


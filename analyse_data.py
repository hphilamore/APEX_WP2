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
    plot_data(all_data, cols_to_plot=mfc_column_names, title="all MFCs")

    # Separate into dictionary of indiviudal MFCs time series data
    all_data_separate = separate_mfc_data(all_data, mfc_column_names)


    # ---------------------------------------------------------------
    # Compute/extract parameters for each COD event, for each MFC
    # ---------------------------------------------------------------

    # Dictionary to store computed/extracted parameters
    mfc_analysis = {
        "Spike delay (days)" : {},
        "COD" : {},
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
        mfc_analysis["COD"][d] = data.loc[cod_events_idx, "COD"]

        # -------------------------------------
        # -------- Extract Resistance ---------
        # -------------------------------------
        
        pass

        # ------------------------------------------------------
        # -------- Compute peak power and peak voltage ---------
        # ------------------------------------------------------

        # Arrays to store index of peak values
        voltage_peaks_idx = []
        power_peaks_idx = []

        # Compute power output as time series of Voltage in mV * (R)
        data['Power W'] = (data["Voltage"]/1000) * (data["Resistance"]*1000)**2

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
            for parameter, peak_vals in zip(
                                            ['Voltage', 'Power W'], 
                                            [voltage_peaks_idx, power_peaks_idx]
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
                    
                print('Peak '+ parameter + ':', peak_idx, peak_val)

                # Store index of the peak
                peak_vals.append(peak_idx)

            # -------------------------
            # -------- Energy ---------
            # -------------------------

            # Find total energy recorded in this window (numerical integral of power wrt time) 
            t = (window.index - window.index[0]).total_seconds()
            power = window['Power W'].values
            energy = np.trapezoid(power, t)
            energy_vals.append(energy)

        # Plot voltage data, showing peaks
        plot_data(data, 
                  ["Voltage"], 
                  title=d, 
                  voltage_peaks=voltage_peaks_idx,
                  show_days=True,
                  show_plot=False
                  )
        
        # -----------------------------
        # -------- Peak delay ---------
        # -----------------------------

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

    # Save spike delay for each MFC for each COD event 
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in mfc_analysis["Spike delay (days)"].items()]))  
    df.to_excel("Spike_delay_days.xlsx", index=False)
    print(df)

    # MFC types
    mfc_groups = { '10*10 AC':{}, 
                '20*30 AC':{}, 
                '10*10':{}, 
                '20*30':{}
                }

    
    # Group spike delay data by MFC type and compute min, max, mean for each COD event 
    for i, mfc_type in zip(range(0, df.shape[1], 3), mfc_groups):

        # Take columns in groups of 3
        group = df.iloc[:, i:i+3]

        mfc_groups[mfc_type]['min'] = group.min(axis=1)
        mfc_groups[mfc_type]['max'] = group.max(axis=1)
        mfc_groups[mfc_type]['mean'] = group.mean(axis=1)

        event_number = range(len(mfc_groups[mfc_type]['mean']))   

        # Plot spike delay data
        plt.plot(event_number, mfc_groups[mfc_type]['mean'], label=mfc_type)

        # shaded area between min and max
        plt.fill_between(x, mfc_groups[mfc_type]['min'], mfc_groups[mfc_type]['max'], alpha=0.3)

    print(mfc_groups)
    plt.legend()
    plt.xticks(x)  # only integers
    plt.xlabel('COD event index')
    plt.ylabel('Delay from COD event to voltage peak (days)')
    plt.savefig("Spike_delay_days.png")
    plt.show()


if __name__ == "__main__":
    main()


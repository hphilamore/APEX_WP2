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

        # Get date-time index of COD events
        cod_events_idx = data.index[data["COD_event"] == 1]

        # Get index of voltage peaks
        voltage_peaks_idx = []

        # Get window of voltage data following each COD event
        for i in range(len(cod_events_idx)):
            start = cod_events_idx[i] 

            if i < len(cod_events_idx) - 1:
                end = cod_events_idx[i+1]
                # Get voltage data exclusive of stopping value
                window = data.loc[(data.index >= start) & (data.index < end), 'Voltage']

            # Last segment of data has no stopping value
            else:
                window = data['Voltage'].loc[start:]

            if len(window) > 0:
                # Find maximum voltage recorded in this window (voltage peak)
                if window.notna().any():
                    peak_idx = window.idxmax()
                    peak_val = data['Voltage'].loc[peak_idx]
                else:
                    peak_idx = None
                    peak_val = None
                    
                # print('Voltage peak:', peak_idx, peak_val)

                # Store index of voltage peak
                voltage_peaks_idx.append(peak_idx)

        # Plot voltage data for each MFC, showing peaks
        plot_data(data, 
                  ["Voltage"], 
                  title=d, 
                  voltage_peaks=voltage_peaks_idx,
                  show_days=True,
                  show_plot=False
                  )

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

    # Save spike delay analysis to excel file 
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in mfc_analysis["Spike delay (days)"].items()]))  
    df.to_excel("Spike_delay_days.xlsx", index=False)
    print(df)

    
    # Group spike delay data by MFC type and compute min, max, mean
    mfc_groups = {  '10*10 AC':{}, 
                    '20*30 AC':{}, 
                    '10*10':{}, 
                    '20*30':{}
                    }
    
    for i, mfc_type in zip(range(0, df.shape[1], 3), mfc_groups):

        # Take columns in groups of 3
        group = df.iloc[:, i:i+3]

        mfc_groups[mfc_type]['min'] = group.min(axis=1)
        mfc_groups[mfc_type]['max'] = group.max(axis=1)
        mfc_groups[mfc_type]['mean'] = group.mean(axis=1)


        x = range(len(mfc_groups[mfc_type]['mean']))   # or use datetime index if you have one

        plt.plot(x, mfc_groups[mfc_type]['mean'], label=mfc_type)

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


import pandas as pd
import numpy as np
from read_excel_data_funcs import *

patterns = {
        "10x10_AC": r"10\*10\s*AC",
        "20x30_AC": r"20\*30\s*AC",
        "10x10": r"10\*10(?!\s*AC)",   # match 10*10 NOT followed by AC
        "20x30": r"20\*30(?!\s*AC)"    # match 20*30 NOT followed by AC
    }

def analyse_basic_statistics(file_path="mfc_analysis.xlsx"):

    # Read all sheets into a dict of DataFrames
    mfc_analysis = pd.read_excel(file_path, sheet_name=None)

    print(mfc_analysis.keys())  # sheet names

    # ---------------------------------------------------------------
    # -------- Statistical analysis of MFCs grouped by type ---------
    # ---------------------------------------------------------------
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
        plt.show()

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
            plt.show()

if __name__ == "__main__":
    analyse_basic_statistics()
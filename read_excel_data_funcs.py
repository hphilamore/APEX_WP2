import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import matplotlib.dates as mdates
# from scipy.signal import find_peaks


def reformat_as_year_first(date_value):
    "Reformats date data to year first format YYYY-MM-DD"

    # Convert date value to string
    s = str(date_value).strip()

    # CASE 1 — YYYY-MM-DD, ISO format already
    if isinstance(date_value, (pd.Timestamp, datetime)):
        return date_value.strftime("%Y-%m-%d")              

    # CASE 2 — DD/MM/YYYY, convert to YYYY-MM-DD
    if "/" in s:
        try:
            d = datetime.strptime(s, "%d/%m/%Y")
            return d.strftime("%Y-%m-%d")
        except:
            pass

    # CASE 3 — If it's an Excel serial number
    try:
        serial = float(s)
        base = pd.Timestamp("1899-12-30")
        d = base + pd.to_timedelta(serial, unit="D")
        return d.strftime("%Y-%m-%d")
    except:
        pass

    # FALLBACK — return original string (pd.to_datetime can still handle many)
    return s


def import_excel_data(file_path):

    """
    Imports excel data
    Skips sheets that don't yet have a COD column
    Combines data and time columns into one date-time column
    """

    # A dictionary to store cleaned DataFrames
    data = {}

    # --- Load workbook ---
    xls = pd.ExcelFile(file_path)

    print('N sheets', len(xls.sheet_names))

    # Sheets to import
    # for sheet in xls.sheet_names[33:]: 
    # for sheet in xls.sheet_names[17:27]:
    # for sheet in xls.sheet_names[27:37]: 
    # for sheet in xls.sheet_names[37:]:  
    for sheet in xls.sheet_names:

        # skip first sheet
        if sheet.lower() == "info":
            continue  

        # skip reinoculation sheets
        if sheet.lower().startswith("reinoculation"):
            continue  

        print("Now processing:", sheet)

        # Read sheet:
        # - header=0   --> use first row as column names
        # - skiprows=[1,2]  --> ignore next two heading rows
        df = pd.read_excel(
            file_path,
            sheet_name=sheet,
            header=0,
            skiprows=[1, 2],
            engine="openpyxl",
        )

        # Skip sheets that don't yet have COD column
        if "COD1" not in df.columns:
            continue

        # --- Combine date + time columns ---
        # Give time and date columns a name 
        date_col = df.columns[0]
        time_col = df.columns[1]

        # Reformat date column
        df[date_col] = df[date_col].apply(reformat_as_year_first)
        try:
            df["datetime"] = pd.to_datetime(
                df[date_col].astype(str) + " " + df[time_col].astype(str)
            )
        except:
            print('problem:', sheet, df[date_col].astype(str) + " " + df[time_col].astype(str))

        
        # Raplace voltage values before the COD spike with NaN in each sheet  
        voltage_cols = extract_mfc_column_names(df)
        cod_cols = [col for col in df.columns if col.startswith("COD")]

        # For each MFC
        for v_col, cod_col in zip(voltage_cols, cod_cols):

                    # Find COD event 
                    cod_idx = df[cod_col].first_valid_index()

                    # Replace voltage values recorded ahead of the COD event with NaN
                    if cod_idx is not None:
                        df.loc[:cod_idx, v_col] = np.nan

        # Drop data containing spike with unknown COD value
        if sheet == "30sec x20_3K 2":
            cutoff = pd.to_datetime("11/04/2025", dayfirst=True)
            df = df[df["datetime"] < cutoff]

        # Drop data containing spike with unknown COD value
        if sheet == "biosensor-anode (30 sec) rec8":
            cutoff = pd.to_datetime("12/08/2024", dayfirst=True)
            df = df[df["datetime"] < cutoff]

        # Drop data containing spike due to change in resistor value during recording
        if sheet == "biosensor-anode (30sec) rec15":
            cutoff = pd.to_datetime("10/02/2025 09:56:54", dayfirst=True)
            df = df[df["datetime"] < cutoff]

        # Drop the original separate date & time columns
        df = df.drop(columns=[date_col, time_col])

        # Store cleaned dataframe under its sheet name
        data[sheet] = df

    # Example showing what's loaded:
    for s in data:
        print(f"\nSheet: {s}")
        print(data[s].head(30))

    return data


def plot_data(all_data, cols_to_plot, title=None, voltage_peaks=False, show_days=False, show_plot=True):

    n_mfcs = len(cols_to_plot)

    plt.figure(figsize=(16, 6))

    # ----- PRIMARY AXIS: MFC Voltage -----                                                                  
    # Build a colormap for primary-axis columns
    cmap = cm.get_cmap("gist_rainbow")   
    colors = {col: cmap(i / len(cols_to_plot)) for i, col in enumerate(cols_to_plot)}

    ax1 = plt.gca()

    for col in cols_to_plot:
        ax1.scatter(
            all_data["datetime"],
            all_data[col],
            s=1,
            alpha=0.7,
            color=colors[col],
            label=col
        )

        if isinstance(voltage_peaks, list):

            # Remove None values before plotting 
            voltage_peaks = [v for v in voltage_peaks if v!=None]
 
            # Overlay peaks as points
            plt.scatter(all_data["datetime"].loc[voltage_peaks],
                        all_data[col].loc[voltage_peaks],
                        color="black",
                        marker="o",
                        label="Detected peaks",
                        zorder=3,
                        edgecolor="black", 
                        facecolor="white")

    ax1.set_xlabel("Date–Time")
    ax1.set_ylabel("MFC Voltage (mV)")

    # Set major ticks: every month
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    if show_days:
        # Minor ticks: every day
        ax1.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
        ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))  # day number
        ax1.tick_params(axis='x', which='minor', labelsize=6, labelrotation=90)

    # Adjust spacing for readability
    ax1.tick_params(axis='x', which='major', pad=10, rotation=45)

    # plt.show()
    # return

    # # ----- SECONDARY AXIS: COD and resistance -----
    ax2 = ax1.twinx()

    # Columns to plot as shaded regions 
    shaded_cols = ["Resistance"]

    # Include COD values in columns to plot as shaded regions 
    # (when plotting all MFCs, show COD values for MFC1 only in shaded plot) 
    for col in all_data.columns:
        if col.startswith("COD_filled"):
            shaded_cols.append(col)
            break
    
    # Identify gaps in time series
    gap_threshold = pd.Timedelta("10 minutes")
    gaps = all_data["datetime"].diff() > gap_threshold

    # Plot shaded regions
    for col in shaded_cols:

        # Make a copy of data to plot on vertical axis
        y = all_data[col].astype(float).copy()

        # Convert resistance to Ohms for plotting
        if col == "Resistance":
            y *= 1000

        # Insert NaN where there are gaps in data so shading doesn't cross
        y[gaps] = np.nan

        # Mask invalid values (NaN) so fill_between leaves gaps
        y_masked = np.ma.masked_invalid(y)

        # Set colour 
        c = "red" if col == ("Resistance") else "blue"

        # Set label 
        l = (
            "Resistance (Ohms)" if col == "Resistance"
            # else "COD (most recent)" if col == "COD_filled_1"
            else "COD (most recent)" if col.startswith("COD_filled")
            else None
        )

        # Set opacity
        a = 0.1 # if col == "Resistance" else 0.1

        ax2.fill_between(
            all_data["datetime"],
            y_masked,
            step="post",
            alpha=a,
            color=c,
            label=l
        )

    # Plot COD events (when plotting all MFCs, show COD values for MFC1 only) 
    # Find all columns starting with COD 
    cod_cols = [col for col in all_data.columns if col.startswith("COD")]

    # Plot COD events 
    ax2.scatter(all_data["datetime"],
                all_data[cod_cols[0]],
                label = "COD events",
                marker = "*",
                edgecolor="black", 
                facecolor="white")

    ax2.set_ylabel("Resistance (Ohms)\n COD")

    # ----- MERGE LEGENDS -----
    # get handles from both axes
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()


    # place combined legend in top right
    my_legend = plt.legend(h1 + h2, l1 + l2, 
                            loc="center left", 
                            # push legend outside the axis (horizontal value, vertical value)
                            bbox_to_anchor=(1.1, 0.5),   
                            borderaxespad=0
                            )

    # Enlarge legend markers only 
    for handle in my_legend.legend_handles:
        if hasattr(handle, "set_sizes"):     # scatter plots
            handle.set_sizes([50])           # increase legend marker size


    plt.title(title)
    plt.tight_layout()
    plt.savefig("figs/" + title + ".png")

    if show_plot:
        plt.show()
    plt.close()

def extract_mfc_column_names(all_data):
        column_names = [col for col in all_data.columns if not col.startswith(('COD', 
                                                                       'Resistance', 
                                                                       'TYE', 
                                                                       'datetime',
                                                                       'Date',
                                                                       'Time')
                                                                     )]
        return column_names

def separate_mfc_data(all_data, mfc_cols):
    """
    Splits data into 12 independent sensor time series.
    Each output DataFrame has:
        datetime, Voltage, Resistance, COD_raw, COD_filled, COD_event
    """

    # A dict to store individual mfc data as pandas data frames 
    sensor_dict = {}

    # Number of columns containing MFC volta
    n_mfcs = len(mfc_cols)
    N = n_mfcs + 1

    for col, n in zip(mfc_cols, list(range(1,N))):

        df = all_data.copy()

        # Store the column name 
        mfc_name = col

        # Rename the selected voltage column
        df = df.rename(columns={col: "Voltage"})

        # Keep only the features needed
        # keep_cols = ["datetime", "Voltage", "Resistance", "COD_raw", "COD_filled", "COD_event"]
        keep_cols = ["datetime", "Voltage", "Resistance", "COD" + str(n), "COD_filled_" + str(n), "COD_event_" + str(n)]
        df = df[keep_cols]

        df = df.rename(columns={"COD" + str(n): "COD"})
        df = df.rename(columns={"COD_filled_" + str(n): "COD_filled"})
        df = df.rename(columns={"COD_event_" + str(n): "COD_event"})

        # Change resistance value applied to MFC 6 from 2025-04-28 as it is different from other MFCs
        if mfc_name.startswith("6"):
            # print("MFC 6")

            # Check resistance value before change
            # print(df.loc[df['datetime'] >= '2025-04-28'].head())

            df.loc[df['datetime'] >= '2025-04-28', 'Resistance'] = 1

            # Check resistance value after change
            # print(df.loc[df['datetime'] >= '2025-04-28'].head())

        # Check output looks as it should
        # print('column name ', col)
        # print(df.head(10))

        # Store under the mfc channel name
        sensor_dict[mfc_name] = df

    return sensor_dict
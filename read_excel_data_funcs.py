import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import matplotlib.dates as mdates


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
    for sheet in xls.sheet_names[5:10]: 
    # for sheet in xls.sheet_names:

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
            engine="openpyxl"
        )

        # Skip sheets that don't yet have COD column
        if "COD1" not in df.columns:
            continue

        # --- Combine date + time columns ---
        # Give time and date columns a name 
        date_col = df.columns[0]
        time_col = df.columns[1]

        # Apply normalisation to the date column
        df[date_col] = df[date_col].apply(reformat_as_year_first)

        try:
            df["datetime"] = pd.to_datetime(
                df[date_col].astype(str) + " " + df[time_col].astype(str)
            )
        except:
            print('problem:', sheet, df[date_col].astype(str) + " " + df[time_col].astype(str))

        # Optional: drop the original separate date & time columns
        df = df.drop(columns=[date_col, time_col])

        # Store cleaned dataframe under its sheet name
        data[sheet] = df

    # Example showing what's loaded:
    for s in data:
        print(f"\nSheet: {s}")
        print(data[s].head())

    return data


def plot_data(all_data, mfc_cols):

    # all_data = all_data[:5000]

    # Plot combined data
    plt.figure(figsize=(16, 6))


    
    # ----- PRIMARY AXIS: MFC Voltage -----                                                                  
    # Build a colormap for primary-axis columns
    cmap = cm.get_cmap("gist_rainbow")   
    colors = {col: cmap(i / len(mfc_cols)) for i, col in enumerate(mfc_cols)}

    ax1 = plt.gca()

    for col in mfc_cols:
        ax1.scatter(
            all_data["datetime"],
            all_data[col],
            s=1,
            alpha=0.7,
            color=colors[col],
            label=col
        )

    ax1.set_xlabel("Date–Time")
    ax1.set_ylabel("MFC Voltage (mV)")

    # Set major ticks: every month
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    # # Minor ticks: every day
    # ax1.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
    # ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))  # day number
    # ax1.tick_params(axis='x', which='minor', labelsize=6, labelrotation=90)

    # Adjust spacing for readability
    ax1.tick_params(axis='x', which='major', pad=10, rotation=45)

    # plt.show()
    # return

    # # ----- SECONDARY AXIS: COD and resistance -----
    ax2 = ax1.twinx()

    # Columns to plot as shaded regions 
    shaded_cols = ["Resistance"]
    n_mfcs = len(mfc_cols)
    N = n_mfcs + 1          # plot all MFCs
    N = 2                   # plot MFC1 only (assuming a negligably small difference between MFCs when plotted)
    for n in list(range(1,N)):
        shaded_cols.append("COD_filled_" + str(n))

    print(shaded_cols)
    
    # Identify gaps in time series
    gap_threshold = pd.Timedelta("10 minutes")
    gaps = all_data["datetime"].diff() > gap_threshold

    
    # for col, c, l in zip(shaded_cols, shade_colours, shade_labels):
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
            else "COD (most recent)" if col == "COD_filled_1"
            else None
        )

        # Set opacity
        a = 0.1 if col == "Resistance" else 0.1

        ax2.fill_between(
            all_data["datetime"],
            y_masked,
            step="post",
            alpha=a,
            color=c,
            label=l
        )

    # Plot COD events for MFC1 (assuming a negligably small gap in events for MFCs when plotted)
    ax2.scatter(all_data["datetime"],
                # all_data["COD_raw"],
                all_data["COD1"],
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


    plt.title("Time series of MFC voltage, COD and external load")
    plt.tight_layout()
    plt.savefig("time_series.png")
    plt.show()

def separate_mfc_data(all_data, mfc_cols):
    """
    Splits data into 12 independent sensor time series.
    Each output DataFrame has:
        datetime, Voltage, Resistance, COD_raw, COD_filled, COD_event
    """

    # voltage_cols = all_data.columns[:12]

    sensor_dict = {}

    # Number of columns containing MFC volta
    n_mfcs = len(mfc_cols)
    N = n_mfcs + 1

    # for vcol in voltage_cols:
    # for vcol, n in zip(voltage_cols, list(range(1,N))):
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

        print('column name ', col)
        print(df.head())

        # Store under the mfc channel name
        sensor_dict[mfc_name] = df

    return sensor_dict
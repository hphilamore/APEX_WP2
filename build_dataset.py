import pandas as pd
import numpy as np
from read_excel_data_funcs import *
import re
import scipy
from scipy.optimize import minimize
import matplotlib.pyplot as plt

file_path="mfc_analysis.xlsx"

# Read all sheets into a dict of DataFrames
mfc_analysis = pd.read_excel(file_path, sheet_name=None)


# Get the first sheet (DataFrame)
first_sheet = next(iter(mfc_analysis.values()))

# Get column names
columns = first_sheet.columns.tolist()[1:]

print(columns)


# print(mfc_analysis.keys())  # sheet names

patterns = {
        "10x10_AC": r"10\*10\s*AC",
        "20x30_AC": r"20\*30\s*AC",
        "10x10": r"10\*10(?!\s*AC)",   # match 10*10 NOT followed by AC
        "20x30": r"20\*30(?!\s*AC)"    # match 20*30 NOT followed by AC
    }


def load_series(data, sheet_name, col_name, year):

    # Load sheet
    df = data[sheet_name].copy()

    # Get the name of the first column
    time_col = df.columns[0]

    # Convert using column name 
    df[time_col] = pd.to_datetime(df[time_col].astype(str), errors='coerce', dayfirst=True)

    # Filter rows to select section of time series
    df_by_year = df[df[time_col].dt.year == year] 

    # Exclue last row (anomoly)
    # df_2024 = df_2024.iloc[:-1]

    # Extract the required column
    values = df_by_year[col_name].values
    # values = df_2024[col].values

    return values, df_by_year.iloc[:, 0]  # return values + timestamps

    # for label, pattern in patterns.items():
    #     print(f"\nPattern: {label}")

    #     for col in df.columns:
    #         if re.search(pattern, col):
    #             print(f"  -> {col}")



for col in columns:
    # MFC types to skip 
    if re.search(r"20\*30\s*AC", col):
            continue

    # Section data by year
    for year in [2024, 2025]:

        # TODO: Loop to downselect by resistance 

        cod, time_cod = load_series(mfc_analysis, 'COD', col, year)
        resistance, time_cod = load_series(mfc_analysis, 'Resistance kOhms', col, year)
        v_peak, time_cod = load_series(mfc_analysis, 'Vpeak mV', col, year)
        p_peak, time_cod = load_series(mfc_analysis, 'Ppeak W', col, year)
        energy, time_cod = load_series(mfc_analysis, 'Energy J', col, year)

        # TODO: Line that filters useing resistance 

        # TODO: Add features to training data

        cmap = plt.cm.magma   # choose a colormap
        n = len(cod)                  # number of loop iterations
        colors = cmap(np.linspace(0, 1, n))

        for a,b,c, d in zip(cod, v_peak, resistance, colors):

            if c == 0.1:
                m = '*'
            elif c == 1:
                m = 'o'
            else:
                m = 'v'

            plt.scatter(a, b, marker=m, color=d)
            # plt.scatter(a, b, marker=m)

        plt.xlabel("COD")
        plt.ylabel("Peak")
        plt.show()
















import pandas as pd
import numpy as np
from read_excel_data_funcs import *

# import torch
# import torch.nn as nn
# import torch.nn.functional as F

raw_data_file_path = "Biosensor data from the start (13-06-24) until 06-01-25.xlsx"

def import_data(file_path):

    # Import data as multi-sheet data frame 
    data = import_excel_data(file_path)

    # Combine as new single sheet data frame, that concatenates data from all pages ordered chronologically 
    all_data = pd.concat(data.values(), ignore_index=True)

    # Sort by date time
    all_data = all_data.sort_values("datetime").reset_index(drop=True)

    # Get names of columns containing MFC voltage data 
    mfc_column_names = extract_mfc_column_names(all_data)

    # Number of columns containing MFC voltage
    n_mfcs = len(mfc_column_names)
    N = n_mfcs + 1

    # Create column of forward-filled COD values for each MFC
    for n in list(range(1,N)):
        all_data["COD_filled_" + str(n)] = all_data["COD" + str(n)].ffill()
        
    # Create column with event flag (1 at COD measurement points, 0 elsewhere) for each MFC 
    for n in list(range(1,N)):
        all_data["COD_event_" + str(n)] = (~all_data["COD" + str(n)].isna()).astype(int)

    # Separate into dictionary of indiviudal MFCs time series data frames
    all_data_separate = separate_mfc_data(all_data, mfc_column_names)

    # Save data
    # df = pd.DataFrame(all_data)
    pd.to_pickle(all_data, "all_data.pkl")

    # # dfs = {name: pd.DataFrame(sheet) for name, sheet in all_data_separate.items()}
    # pd.to_pickle(all_data_separate, "all_data_separate.pkl")

if __name__ == "__main__":
    import_data(raw_data_file_path)
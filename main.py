from read_excel_data import *
from extract_features import *
from basic_statistical_analysis import *
from model_performance_comparison import *

def main():

    # Inports raw data
    # import_data(raw_data_file_path)

    # for window_length in [1/12, 1/6, 1/3, 1/2, 1, 2, 3, 4, 5, 12, 18, 24]:
    for window_length in [1/12]:#, 1/6, 1/3]:

        # Store feature set as excel file
        extract_and_store_features(input_file_path="all_data.pkl",
                                output_file_name=feature_data_file_name,
                                window_length_hours=window_length
                                )

        # Run basic statistical analysis on features in excel file and plot data
        # analyse_basic_statistics(file_path=feature_data_file_path)
        features=[
                    'Vpeak mV', 
                    'Ppeak W', 
                    'Energy J', 
                    'Resistance kOhms', 
                    'Vfinal mV', 
                    'Pfinal W'
                    ]

        

        # Build a ridge regression model using the fetaures and test which combinations of input data give the best performance
        best_config = compare_input_data_performance(
                features=features,
                # features=[
                #     'Vpeak mV', 
                #     'Ppeak W', 
                #     'Energy J', 
                #     'Resistance kOhms', 
                #     'Vfinal mV', 
                #     'Pfinal W'
                #     ],
                mfc_types_all = [
                    r"10\*10\s*AC",     # Carbon veil + activated carbon
                    r"20\*30\s*AC",
                    r"10\*10(?!\s*AC)", # Carbon veil
                    r"20\*30(?!\s*AC)"
                    ],
                resistances_all = [0.1, 1, 3],
                years_all = [2024, 2025]
            )
        
        print()
        print(f"Best config for window length {window_length} days")
        print("MFC types:", [mfc_types_regex_mappings[p] for p in best_config["mfc_types"]])
        print("Resistances kOhm:", best_config["resistances"])
        print("Years:", best_config["years"])
        print("R²:", round(best_config["r2"], 4))
        print("MSE:", round(best_config["mse"], 2))
        print("Alpha:", best_config["alpha"]),
        # print("N Samples:", res["n_samples"])
        # print("Terms:", "v_peak, p_peak, energy, resistance")
        print("Terms:", features)
        print("Coefficients:", [float(round(r, 3)) for r in best_config["coefficients"]])
        print("Intercept:", best_config["intercept"])
        print()

    
if __name__ == "__main__":
    main()
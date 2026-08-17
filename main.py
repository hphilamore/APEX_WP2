from read_excel_data import *
from extract_features import *
from basic_statistical_analysis import *
from model_performance_comparison import *
from matplotlib import pyplot as plt
from openpyxl import Workbook

# Create a new workbook
wb = Workbook()

# Remove the default empty sheet
wb.remove(wb.active)

def main():

    # Inports raw data
    # import_data(raw_data_file_path)

    feature_sets = [
        [
                    'Vpeak mV', 
                    'Ppeak W', 
                    'Energy J', 
                    'Resistance kOhms', 
                    'Vfinal mV', 
                    'Pfinal W'
                    ],
        # ['Energy J'],
        # ['Vpeak mV'],
        # [
        #             'Vpeak mV', 
        #             'Ppeak W', 
        #             'Energy J', 
        #             'Resistance kOhms', 
        #             ],


    ]

    models = [Ridge, XGBRegressor]

    model_results = [[] for model in models] 

    # window_lengths = [1/12, 1/6, 1/3, 1/2, 1, 2, 3, 4, 5]#, 12, 18]
    window_lengths = [1/3, 1/2, 1, 2, 3]
    # window_lengths = [1/3, 1/2, 1]

    for features in feature_sets:

        cmap = plt.colormaps["viridis"]
        n = len(window_lengths)


        for i, window_length in enumerate(window_lengths):
        # for window_length in [18]:

            # Store feature set as excel file
            extract_and_store_features(input_file_path="all_data.pkl",
                                    output_file_name=feature_data_file_name,
                                    window_length_hours=window_length
                                    )

            # Run basic statistical analysis on features in excel file and plot data
            # analyse_basic_statistics(file_path=feature_data_file_path)

            # features=[
            #             'Vpeak mV', 
            #             'Ppeak W', 
            #             'Energy J', 
            #             'Resistance kOhms', 
            #             'Vfinal mV', 
            #             'Pfinal W'
            #             ]
                
            # Find the configuration of input data that gives the best performance from each model
            best_configs = compare_input_data_configurations(
                    features=features,
                    labels=['COD'],
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
                    resistances_all = [
                        0.1, 
                        1, 
                        3
                        ],
                    years_all = [2024, 2025],
                    models = models,
                    model_params= [ridge_params, xgb_params],
                    scale_model_features=[True, False],
                    verbose = False
                )


            # Log this configuration to the results for each model
            for best_config, result in zip(best_configs, model_results):

                best_config["window_length"] = window_length

                # Store result
                result.append(best_config)

                # # Print summary
                # print(f"Best config for window length {round(window_length,3)} hours")
                # print("Model:", best_config["model"])
                # print("MFC types:", [mfc_types_regex_mappings[p] for p in best_config["mfc_types"]])
                # print("Resistances kOhm:", best_config["resistances"])
                # print("Years:", best_config["years"])
                # print("R²:", round(best_config["r2"], 3))
                # print("MAE:", round(best_config["mae"], 3))
                # # print("Alpha:", best_config["alpha"]),
                # # print("N Samples:", res["n_samples"])
                # # print("Terms:", "v_peak, p_peak, energy, resistance")
                # print("Model Parameters:", ", ".join(f"{k}: {v:.3f}" for k, v in best_config["parameters"].items())),
                # # print("N Samples:", res["n_samples"])
                # # print("Terms:", "v_peak, p_peak, energy, resistance")
                # print("Terms:", best_config["features"])
                # if "coefficients" in best_config:
                #     print("Coefficients:", best_config["coefficients"])
                # if "intercept" in best_config:
                #     print("Intercept:", best_config["intercept"])
                # if "feature_importances" in best_config:
                #     print("Feature Importances:", best_config["feature_importances"])
                # # print("Coefficients:", [float(round(r, 3)) for r in res["coefficients"]])
                # # print("Intercept:", res["intercept"])
                # print()

    for results, model in zip(model_results, models):

        # Array to store  R2 values for each window size for plotting 
        r2s = []

        # Get model name
        model_name = results[0]["model"]

        # Use the model name as the worksheet name
        sheet_name = model_name

        # Create worksheet
        ws = wb.create_sheet(title=sheet_name)
        # Column headings
        ws.append([            
            "Model",
            "Window Length (h)",
            "N samples"
            "MFC Types",
            "Resistances (kOhm)",
            "Years",
            "R²",
            "MAE",
            "Model Parameters",
            "Terms",
            "Coefficients",
            "Intercept",
            "Feature Importances"
        ])

        # Visualise the best configuration for each window size investigated using this model
        for best_config in results:

            # Print summary
            # print(f"Best config for window length {round(window_length,3)} hours")
            print(f"Best config for window length {round(best_config['window_length'],3)} hours")
            print("Model:", best_config["model"])
            print("MFC types:", [mfc_types_regex_mappings[p] for p in best_config["mfc_types"]])
            print("Resistances kOhm:", best_config["resistances"])
            print("Years:", best_config["years"])
            print("R²:", round(best_config["r2"], 3))
            print("MAE:", round(best_config["mae"], 3))
            # print("Alpha:", best_config["alpha"]),
            print("N Samples:", best_config["n_samples"])
            # print("Terms:", "v_peak, p_peak, energy, resistance")
            print("Model Parameters:", ", ".join(f"{k}: {v:.3f}" for k, v in best_config["parameters"].items())),
            # print("N Samples:", res["n_samples"])
            # print("Terms:", "v_peak, p_peak, energy, resistance")
            print("Terms:", best_config["features"])
            if "coefficients" in best_config:
                print("Coefficients:", best_config["coefficients"])
            if "intercept" in best_config:
                print("Intercept:", best_config["intercept"])
            if "feature_importances" in best_config:
                print("Feature Importances:", best_config["feature_importances"])
            # print("Coefficients:", [float(round(r, 3)) for r in res["coefficients"]])
            # print("Intercept:", res["intercept"])
            print()

            # Save data to excel
            ws.append([
                best_config["model"],
                round(best_config["window_length"], 3),
                best_config["n_samples"],
                ", ".join(mfc_types_regex_mappings[p] for p in best_config["mfc_types"]),
                ", ".join(map(str, best_config["resistances"])),
                ", ".join(map(str, best_config["years"])),
                round(best_config["r2"], 3),
                round(best_config["mae"], 3),
                ", ".join(
                    f"{k}: {v:.3f}"
                    for k, v in best_config["parameters"].items()
                ),
                ", ".join(best_config["features"]),
                ", ".join(map(str, best_config.get("coefficients", []))),
                best_config.get("intercept", ""),
                ", ".join(map(str, best_config.get("feature_importances", []))),
            ])
            
            # Plot data
            # Update the list of R2 values for plotting as line graph
            r2s.append(best_config["r2"])

            # If the model solution is a linear equation create a string of the equation 
            if "coefficients" in best_config:
                equation_string = (
                "COD = " +
                " + ".join(
                    f"{c:.3f}*{f}"
                    for c, f in zip(best_config["coefficients"], features)
                    ) +
                f" + {best_config['intercept']:.3f}" +
                f", R2={best_config['r2']:.3f}"
                )
            else:
                equation_string = None

            # colour = cmap(i / (n - 1))

            # Add R2 value for current window size to scatter plot and label with equation
            plt.scatter(best_config['window_length'], 
                        best_config["r2"], 
                        label=equation_string, 
                        # color=colour
                        )

        # Line graph of R2 values for all window sizes        
        feature_string = (model_name + ", ".join(features))
        plt.plot(window_lengths, r2s, label=feature_string)

        # Plot formatting 
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2))
        plt.subplots_adjust(bottom=0.4)
        plt.xlabel("Time (hours)")
        plt.ylabel("R2 (best configuration)")
        plt.title(feature_string)
        plt.savefig(f"figs/{feature_string}.png", bbox_inches="tight")
        # # plt.show()
        plt.close()

    # Save workbook to excel file
    wb.save("model_performance.xlsx")
            
    # plt.savefig(f"figs/all_v2_Ridge-R2.png", bbox_inches="tight")
    # # plt.show()
    # plt.close()

if __name__ == "__main__":
    main()
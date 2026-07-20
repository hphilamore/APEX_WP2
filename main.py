from read_excel_data import *
from extract_features import *
from basic_statistical_analysis import *
from model_performance_comparison import *
from matplotlib import pyplot as plt

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
        [
                    'Vpeak mV', 
                    'Ppeak W', 
                    'Energy J', 
                    'Resistance kOhms', 
                    # 'Vfinal mV', 
                    # 'Pfinal W'
                    ],


    ]

    for features in feature_sets:

        window_lengths = [1/12, 1/6, 1/3, 1/2, 1, 2, 3, 4, 5]#, 12, 18]
        # window_lengths = [1/3, 1/2, 1, 2, 3]
        # window_lengths = [1/3, 1/2, 1]
        r2s = []

        cmap = plt.get_cmap('viridis')
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
                    years_all = [2024, 2025],
                    verbose = False
                )
            
            print()
            print(f"Best config for window length {round(window_length,3)} days")
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

            r2s.append(best_config["r2"])

            equation_string = (
            "COD = " +
            " + ".join(
                f"{c:.3f}*{f}"
                for c, f in zip(best_config["coefficients"], features)
                ) +
            f" + {best_config['intercept'][0]:.3f}" +
            f", R2={best_config['r2']:.3f}"
            )

            colour = cmap(i / (n - 1))

            plt.scatter(window_length, best_config["r2"], 
                        # label=equation_string, 
                        color=colour
                        )
        
        feature_string = (", ".join(features))
        plt.plot(window_lengths, r2s, label=feature_string)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2))
        plt.subplots_adjust(bottom=0.4)
        plt.xlabel("Time (hours)")
        plt.ylabel("R2 (best configuration)")
        plt.title(feature_string)
        # plt.savefig(f"figs/Ridge-R2-{feature_string}.png", bbox_inches="tight")
        # # plt.show()
        # plt.close()
    
    plt.savefig(f"figs/all_v2_Ridge-R2.png", bbox_inches="tight")
    # plt.show()
    plt.close()

if __name__ == "__main__":
    main()
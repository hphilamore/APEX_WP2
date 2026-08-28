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

models = [Ridge]#, XGBRegressor]
model_params = [ridge_params, xgb_params]
scale_features=[True, False]


feature_set = [
                    'Vpeak mV', 
                    'Ppeak W', 
                    'Energy J', 
                    'Resistance kOhms', 
                    'Vfinal mV', 
                    'Pfinal W'
                    ]

# window_lengths = [1/12, 1/6, 1/3, 1/2, 1, 2, 3, 4, 5]#, 12, 18]
# Window lengths in hours
window_lengths = [1/12, 1/6, 1/3]#, 1/2, 1, 2, 3, 4, 5, 6]

def select_best_results(results, performance_metric):
    # Find a set of configurations that are the best performing for any window size
    top_configurations = set()

    # Get all widnow sizes tested
    for window_size in set(
        window
        for values in results.values()
        for window in values["window"]
    ):

        # Get R2 values for this window size
        window_results = []

        for series_name, values in results.items():

            if window_size in values["window"]:
                index = values["window"].index(window_size)
                result = values["result"][index]

                window_results.append((series_name, result))

        # Sort by R2 and take the best config
        reverse = True if performance_metric == "R²" else False

        n_configs = 1
        top_configs = sorted(
            window_results,
            key=lambda x: x[1],
            reverse=reverse
        )[:n_configs]

        # Add these configurations to the set
        top_configurations.update(
            series_name for series_name, result in top_configs
        )

    # Filter results excluding those that are not in the set of top configurations
    results = {
        series_name: values
        for series_name, values in results.items()
        if series_name in top_configurations
    }

    return results


def plot_data(model, 
              excel_file="model_performance.xlsx",
              performance_metric="R²"):

    model_name = model.__name__

    excel_file = excel_file

    # Read all sheets
    all_sheets = pd.read_excel(excel_file, sheet_name=None)

    # Store R2 values for each configuration
    results = {}

    # print(all_sheets)

    for sheet_name, df in all_sheets.items():

        # Only use sheets belonging to this model
        if not sheet_name.startswith(f"{model_name}"):
            continue

        # else:
        #     print(sheet_name)

        # Extract window size from sheet name
        # e.g. "Ridge, Window=0.333"
        window_size = float(
            sheet_name.split("Window=")[1]
        )

        # Process each row
        for _, row in df.iterrows():

            mfc_type = row["MFC Types"]
            resistance = row["Resistances (kOhm)"]
            year = row["Years"]
            # r2 = row["R²"]
            result = row[performance_metric]

            # Name of this data series
            series_name = (
                f"{mfc_type}, "
                f"R={resistance}, "
                f"{year}"
            )

            # Add new data series to overall results
            if series_name not in results:
                results[series_name] = {
                    "window": [],
                    # "r2": []
                    "result": []
                }

            # Store result from this sheet to data series
            results[series_name]["window"].append(window_size)
            results[series_name]["result"].append(result)

    # # Find a set of configurations that are the best performing for any window size
    # top_configurations = set()

    # # Get all widnow sizes tested
    # for window_size in set(
    #     window
    #     for values in results.values()
    #     for window in values["window"]
    # ):

    #     # Get R2 values for this window size
    #     window_results = []

    #     for series_name, values in results.items():

    #         if window_size in values["window"]:
    #             index = values["window"].index(window_size)
    #             result = values["result"][index]

    #             window_results.append((series_name, result))

    #     # Sort by R2 and take the best config
    #     reverse = True if performance_metric == "R²" else False

    #     n_configs = 1
    #     top_configs = sorted(
    #         window_results,
    #         key=lambda x: x[1],
    #         reverse=reverse
    #     )[:n_configs]

    #     # Add these configurations to the set
    #     top_configurations.update(
    #         series_name for series_name, result in top_configs
    #     )

    # # Filter results excluding those that are not in the set of top configurations
    # results = {
    #     series_name: values
    #     for series_name, values in results.items()
    #     if series_name in top_configurations
    # }

    results = select_best_results(results, performance_metric)

    # Plot
    plt.figure(figsize=(15, 6))

    colours = plt.cm.tab10(np.linspace(0, 1, len(results)))

    for (series_name, values), colour in zip(results.items(), colours):

        # Sort by window size so lines are drawn in the correct order
        sorted_values = sorted(
            zip(values["window"], values["result"])
        )

        windows, result_values = zip(*sorted_values)

        plt.plot(
            windows,
            result_values,
            marker="o",
            label=series_name,
            color=colour
        )

    if performance_metric == "R²":
        plt.ylim(-1, 1)
    else:
        plt.ylim(0, 1000)

    plt.xlabel("Window size (hours)")
    plt.ylabel(performance_metric)
    plot_title = f"{performance_metric} vs Window Size — {model_name}"
    plt.title(plot_title)

    plt.legend(
        # title="Configuration",
        bbox_to_anchor=(1.05, 1),
        loc="upper left"
    )

    plt.grid(True)
    plt.tight_layout()
    plt.subplots_adjust(right=0.7)
    plt.savefig(f"figs/{plot_title}.png")
    # plt.show()
    plt.close()
    


def main():

    for i, window_length in enumerate(window_lengths):
    # for window_length in [18]:

        # # Values for formatting plotted data
        # cmap = plt.colormaps["viridis"]
        # n = len(window_lengths)

        # Extract features for windows of the specified length 
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
            
        # Find the configuration of input data that gives the best performance from each model class
        
        # Get results for each subset tested for this window size and engineered features
        # best_configs = compare_input_data_configurations(
        results = compare_input_data_configurations(
        features=feature_set,
        labels=['COD'],
        mfc_types_all = [
            r"10\*10\s*AC",     # Carbon veil + activated carbon
            r"20\*30\s*AC",
            r"10\*10(?!\s*AC)", # Carbon veil
            r"20\*30(?!\s*AC)"
            ],
        resistances_all = [0.1, 1, 3],
        # resistances_all = [1],
        years_all = [2024, 2025],
        wb=work_book,
        # years_all = [2024],#, 2025],
        # models = [Ridge, XGBRegressor],
        models=models,
        # target_data_points = 25,
        target_data_points=10,
        model_params=model_params,
        test_combinations=False,
        downsample=False,
        scale_features=scale_features,
        verbose=False,
        window_length=window_length
    )

    # Plot the data for each mdoel tested 
    for model in models:
        for metric in ["R²", "MAE"]:
            plot_data(model, 
                    excel_file="model_performance.xlsx",
                    performance_metric=metric)

if __name__ == "__main__":
    main()
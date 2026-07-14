from read_excel_data import *
from extract_features import *
from basic_statistical_analysis import *
from model_performance_comparison import *

def main():

    # Inports raw data
    # import_data(raw_data_file_path)

    # Store feature set as excel file
    # extract_features_to_excel(output_file_path=feature_data_file_path)

    # Run basic statistical analysis on features in excel file and plot data
    # analyse_basic_statistics(file_path=feature_data_file_path)

    # Build a ridge regression model using the fetaures and test which combinations of input data give the best performance
    build_and_evaluate_ridge()



    
if __name__ == "__main__":
    main()
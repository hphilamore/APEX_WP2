from read_excel_data import *
from extract_features import *
from basic_statistical_analysis import *

def main():

    # import_data(raw_data_file_path)

    # extract_features_to_excel(output_file_path=feature_data_file_path)

    analyse_basic_statistics(file_path=feature_data_file_path)

    

if __name__ == "__main__":
    main()
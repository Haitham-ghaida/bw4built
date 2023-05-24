from brwy4build.Objects.objects import LCAh
from collections import OrderedDict
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def save_attributes_to_numpy(obj, attr_names, scenario_name, constant_sen: str = None, path_to_save_folder:str = None):
    for attr_name in attr_names:
        attr = None
        if hasattr(obj, attr_name):
            attr = getattr(obj, attr_name)
            if scenario_name == "high_product":
                scenario_name = "HD"
            if scenario_name == "low_product":
                scenario_name = "LD"
            if scenario_name == "keep":
                scenario_name = "ND"
            if scenario_name == "user input":
                scenario_name = "RW"
            if scenario_name == "high_assembly":
                scenario_name = "HD"
            if scenario_name == "low_assembly":
                scenario_name = "LD"
            if attr_name == "total_impactMC_with_d_rpc_array":
                print_name = "ISD"
            if attr_name == "total_impactMC_without_d_array":
                print_name = "INS"
            if attr_name == "total_impactMC_with_d_standard_array":
                print_name = "ISS"
            if attr_name == "impactsMC_b4_array":
                print_name = "B4"
            attr = attr/120/60
            np.save(os.path.join(path_to_save_folder, f'{constant_sen}_{print_name}_{scenario_name}.npy'), attr)
            print(f'Saved {attr_name} as {scenario_name}_{print_name}.npy')
        else:
            print(f'The object does not have an attribute named {attr_name}')



def load_all_arrays(path_to_folder):
    arrays = {}
    for filename in os.listdir(path_to_folder):
        if filename.endswith('.npy'):
            # Remove the .npy extension to get the array name
            array_name = filename[:-4]
            arrays[array_name] = np.load(os.path.join(path_to_folder, filename))
    return OrderedDict(sorted(arrays.items()))




def export_to_excel(path_to_folder):
    list_of_arrays = load_all_arrays(path_to_folder)

    # Initialize a dictionary to hold the dataframes
    df_dict = {}

    # Iterate over all arrays in the OrderedDict
    for array_name, arr in list_of_arrays.items():
        for i, impact_category in enumerate([method[1].replace(":", "-").replace("/", "-")[:31] for method in LCAh.instances[0].get_list_of_methods]):
            # Select the data for the i-th impact category
            arr_1d = arr[:, i, :].flatten()

            # Apply desired operations
            mean = np.mean(arr_1d)
            median = np.median(arr_1d)
            std_dev = np.std(arr_1d)
            min_val = np.min(arr_1d)
            decile1 = np.percentile(arr_1d, 10)
            quartile1 = np.percentile(arr_1d, 25)
            quartile3 = np.percentile(arr_1d, 75)
            decile3 = np.percentile(arr_1d, 30)
            max_val = np.max(arr_1d)

            # Collect the results in a DataFrame
            if f'{impact_category}' not in df_dict:
                df_dict[f'{impact_category}'] = {}
            df_dict[f'{impact_category}'][array_name] = {
                'mean': mean,
                'median': median,
                'std_dev': std_dev,
                'min': min_val,
                'decile1': decile1,
                'quartile1': quartile1,
                'quartile3': quartile3,
                'decile3': decile3,
                'max': max_val,
            }

    # Convert the dictionaries to dataframes and save to excel
    with pd.ExcelWriter('full_building_sen.xlsx', engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        for impact_category, data in df_dict.items():
            df = pd.DataFrame(data).T
            df.to_excel(writer, sheet_name=impact_category)

    print("Excel file with multiple sheets created successfully.")


def load_all_sen_arrays(path_to_folder, system_boundary):
    # A dictionary to store the arrays for a specific system boundary
    scenarios = {'LD': [], 'HD': [], 'RW': [], 'ND': []}
    
    for filename in os.listdir(path_to_folder):
        if filename.endswith('.npy'):
            # Parse the scenario and system boundary from the filename
            scenario, file_system_boundary, building_scenario = filename.split('_')

            # Only load the array if the system boundary matches the one specified
            if file_system_boundary == system_boundary:
                # Load the array
                array = np.load(os.path.join(path_to_folder, filename))
                # Append the array to the corresponding list in the dictionary
                scenarios[building_scenario[:-4]].append(array)  # remove .npy from building_scenario

    # Convert lists of arrays into single 4D arrays for each scenario
    for scenario, arrays in scenarios.items():
        scenarios[scenario] = np.stack(arrays)

    return scenarios


def plot_scenarios(scenarios, impact_category_index, save):
    # Prepare a list to collect data for each building scenario
    data = []
    labels = []
    
    for scenario_name, scenario_array in scenarios.items():
        # Extract data for the specific impact category, resulting in a (6, 80, 80) array
        impact_data = scenario_array[:, :, impact_category_index, :]
        
        # Concatenate along the Monte Carlo simulations dimensions and flatten
        flattened_data = impact_data.reshape(-1)  # this will result in a 1D array

        data.append(flattened_data)
        labels.append(scenario_name)
        
    # Create a boxplot
    plt.boxplot(data, labels=labels)
    plt.title(f'GWP impact of different building scenarios')
    # y label
    plt.ylabel('GWP [kg CO2-eq]/m2/year')
    if save:
        plt.savefig('boxplot.png', dpi=1000)
    plt.show()
    # save fig with 1000 dpi


    ############################################################################3
def save_attributes_to_numpy_assembly_sen(obj, attr_names, scenario_name, constant_sen: str = None, path_to_save_folder:str = None):
    for attr_name in attr_names:
        attr = None
        if hasattr(obj, attr_name):
            attr = getattr(obj, attr_name)
            attr = attr/120/60
            np.save(os.path.join(path_to_save_folder, f'{constant_sen}_{print_name}_{scenario_name}.npy'), attr)
            print(f'Saved {attr_name} as {scenario_name}_{print_name}.npy')
        else:
            print(f'The object does not have an attribute named {attr_name}')
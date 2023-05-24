list_of_arrays = ["total_impactMC_without_d_array", "total_impactMC_with_d_standard_array", "total_impactMC_with_d_rpc_array"]
list_of_default_values = ["high_product", "low_product", "user input", "keep"]


d1ict = {"a": (1.09186399, 0.44315069, 7.58473472, -0.07522362),
            "b": (1.00000000e+00, 8.07452500e-01, 1.86017358e+02, -2.62179169e-12),
            "c": (1.00000049e+00, 3.54228982e-01, 5.72162691e+01, -4.81510058e-07),
            "d": (90.9335388, 11.56324294, 0.27240267, -3.82067998),
            "e": (1.00151956e+00, 7.27966159e-01, 2.39443872e+01, -3.65332847e-05),
            "f": (1.23640816, 0.59668638, 5.12167984, -0.07709897)}


for default_value in list_of_default_values:
    for sen, value in d1ict.items():
        initialize(projectname="DSPS case studyv14", data_file_path="/home/haithamth/Documents/xlsx/paper1-sen1.xlsx", path_to_save_folder="/home/haithamth/Documents/My_saved_analysis"
                ,project_new=True, lca_new=False, mc_pick=80, MCiterations=150, mode=default_value, default_rel=1, material_flow_mcs=80, save=False, constants=value,
                save_attribute=(list_of_arrays,f"{default_value}",f"{sen}", "/home/haithamth/Documents/results_building_level_sen2"))
        analyze.Analysis.reset()

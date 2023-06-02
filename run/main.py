from brwy4build.Objects.objects import Products, Assemblies, Relations, LCAh, Building
from brwy4build.Analysis.analyze import Analysis
from ..utils.processing import save_attributes_to_numpy
import warnings
import pickle
import os
import logging
import brightway2 as bw


'''
The Idea here is to assess the disassembly potential first a1nd then run the LCA, at the end combining the
disassembly potential with the LCA in the model D some functions are not used anymore, but I left them in
'''

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='logs.log', filemode='a',
                    level=logging.ERROR)

# Some methods will pop a warning because a newer method is available, this is just to avoid printing it
warnings.filterwarnings("ignore")

products_object: Products = None
lca_object: LCAh = None

def save_project(projectname: str = "default", save_folder: str = ""):
    '''This uses pickle to save the project'''
    if not os.path.isdir(f"{save_folder}/{projectname}_save_folder"):
        os.makedirs(f"{save_folder}/{projectname}_save_folder")
    pickle.dump(Building.instances, open(
        f"{save_folder}/{projectname}_save_folder/save_project.p", "wb"))
    print("project saved!")

def load_project(projectname: str = "default", save_folder: str = ""):
    '''This uses pickle to load the project'''
    Building.instances = pickle.load(
        open(f"{save_folder}/{projectname}_save_folder/save_project.p", "rb"))
    for building in Building.instances:
        for assembly in building.assemblies:
            Assemblies.instances.append(assembly)
            for product in assembly.products:
                Products.instances.append(product)
                for relation in product.relations:
                    Relations.instances.append(relation)
    print("project loaded!")

def save_lca(projectname: str = "default", save_folder: str = ""):
    '''This uses pickle to save the lca'''
    if not os.path.isdir(f"{save_folder}/{projectname}_lca_save_folder"):
        os.makedirs(f"{save_folder}/{projectname}_lca_save_folder")
    pickle.dump(LCAh.instances, open(
        f"{save_folder}/{projectname}_lca_save_folder/save_lca.p", "wb"))
    print("lca saved!")


def load_lca(projectname: str = "default", save_folder: str = ""):
    '''This uses pickle to load the lca'''
    LCAh.instances = pickle.load(
        open(f"{save_folder}/{projectname}_lca_save_folder/save_lca.p", "rb"))
    print("lca loaded!")

def load_lca_static(save_folder: str = ""):
    '''This uses pickle to load the lca'''
    LCAh.instances = pickle.load(
        open(f"{save_folder}/save_lca.p", "rb"))
    print("lca loaded!")

#########################################################################################################################################

###########################################################################################################################################


def initialize(projectname: str = "default", data_file_path: str = "default", project_new: bool = False, lca_new: bool = False, path_to_save_folder: str = "", mc_pick: int = 50, include_circularity: bool = True,
               MCiterations: int = 150, connections_input: bool = True, export_excel: bool = False, mode: str = "keep", default_rel: float = 1, assembly: Assemblies = None, save: bool = True,
               brightway_project_name: str = "circularLCA", brightway_bg_db_name: str = "ecoinvent", brightway_method_name: str = "EN15804", load_static_lca_folder_path: str = None,
               material_flow_mcs: int = 100, save_attribute: tuple[str | list, str, str] = None, constants: tuple = (1.09186399, 0.44315069, 7.58473472, -0.07522362),
               assembly_list: list[Assemblies]=None, mode_assembly: str = None,
               tl_mode: str = None):
    bw.projects.set_current(brightway_project_name)
    '''This function initializes the program
    projectname: name of the project it will also be used as the name of the folder where the project will be saved
    data_file_path: path to the data file has to be in .xlsx format and has to follow the provided structure
    project_new: if True it will create a new project, if False it will load the project from the save folder
    lca_new: if True it will create a new lca, if False it will load the lca from the save folder
    path_to_save_folder: path to the folder where the project and lca will be saved or loaded from
    mc_pick: number of Monte Carlo simulations to be chosen from the total number of simulations
    include_circularity: if True it will include the circularity in the LCA
    MCiterations: number of Monte Carlo simulations to be run in the LCA
    connections_input: True if the connections are assessed manually, if false the program will stop and ask for input then run the analysis again with this as True
    export_excel: True if you want to export the results to an excel file named projectname_connections.xlsx
    mode: "keep" if you want to keep if you set a default value it will keep that value for all connections, "user input" if you manually assessed each connection, there are other sen
    default_rel: default value for the relations if mode is set to "keep"
    assembly: if you want to run the analysis for a specific assembly, if None it will run the analysis for all assemblies
    save: if True it will save the project and lca, if False it will not save them
    brightway_project_name: name of the brightway project
    brightway_bg_db_name: name of the brightway background database
    brightway_method_name: name of the LCA brightway method
    load_static_lca_folder_path: path to the folder where the lca will be loaded from, if None it will load the lca from the save folder, use this if you want to load a static lca while running multiple analysis
    save_attribute: saves a result of a building, it should be inputed as a tuple of (building, attribute, name of the sen, path to save)'''
    global lca_object
    global products_object
    if not lca_new and not load_static_lca_folder_path:
        load_lca(projectname=projectname, save_folder=path_to_save_folder)
        lca_object = LCAh.instances[0]
    
    if load_static_lca_folder_path:
        load_lca_static(save_folder=load_static_lca_folder_path)
        lca_object = LCAh.instances[0]

    if project_new:
        # run_first_step(filename=data_file_path)
        Analysis.generate_objects(
            filename=data_file_path, default_rel=default_rel)
        Analysis.setup_analysis(
            filename=data_file_path, reset_objects=False, update_connection=connections_input, export_excel=export_excel, mode=mode, assemblyMC=assembly, mf_mcs=material_flow_mcs,
            constants=constants, assembly_list=assembly_list, mode_assembly=mode_assembly, tl_mode=tl_mode)
        products_object = Products.instances
        if save:
            save_project(projectname=projectname, save_folder=path_to_save_folder)

    if not project_new:
        load_project(projectname=projectname, save_folder=path_to_save_folder)
        products_object = Products.instances

    if lca_new:
        lcah = LCAh()
        for product in Products.instances:
            lcah.get_activityLib(product)
        lcah.method = brightway_method_name
        print(f"LCA method is set to {lcah.method}")
        print("searching for activities in Database...")
        lcah.get_activity()
        save_lca(projectname=projectname, save_folder=path_to_save_folder)
        print("getting LCA library...")
        lcah.get_lca_lib()
        save_lca(projectname=projectname, save_folder=path_to_save_folder)
        print("getting Monte Carlo LCA...")
        lcah.get_multiImpactMonteCarloLCA(iterations=MCiterations)
        lca_object = lcah
        save_lca(projectname=projectname, save_folder=path_to_save_folder)

    if project_new and connections_input:
        Analysis.product_lca(include_circularity = include_circularity, mc_simulations = mc_pick, mf_mcs=material_flow_mcs)
        Analysis.generate_scenarios(mfa_mcs=material_flow_mcs, constants=constants)
        Analysis.generate_results(building=Building.instances[0])
        if save:
            save_project(projectname=projectname, save_folder=path_to_save_folder)
        if save_attribute:
            save_attributes_to_numpy(obj=Building.instances[0],attr_names=save_attribute[0],scenario_name=save_attribute[1], constant_sen=save_attribute[2], other=save_attribute[3],
                                    path_to_save_folder=save_attribute[4])
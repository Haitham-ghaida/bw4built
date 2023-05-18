from brwy4build.Objects.objects import Products, Assemblies, Relations, LCAh, Building
from brwy4build.Analysis.analyze import Analysis
import warnings
import pickle
import os
import logging


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

#########################################################################################################################################

###########################################################################################################################################


def initialize(projectname: str = "default", data_file_path: str = "default", project_new: bool = False, lca_new: bool = False, path_to_save_folder: str = "",
               MCiterations: int = 20, connections_input: bool = False, export_excel: bool = False, mode: str = "keep", default_rel: float = 1, assembly: Assemblies = None, save: bool = True):
    '''This function initializes the program'''
    global lca_object
    global products_object
    if not lca_new:
        load_lca(projectname=projectname, save_folder=path_to_save_folder)
        lca_object = LCAh.instances[0]

    if project_new:
        # run_first_step(filename=data_file_path)
        Analysis.generate_objects(
            filename=data_file_path, default_rel=default_rel)
        Analysis.setup_analysis(
            filename=data_file_path, reset_objects=False, update_connection=connections_input, export_excel=export_excel, mode=mode, assemblyMC=assembly)
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
        lcah.method = "EN15804"
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
        Analysis.product_lca()
        Analysis.generate_scenarios()
        Analysis.generate_results(building=Building.instances[0])
        save_project(projectname=projectname, save_folder=path_to_save_folder)

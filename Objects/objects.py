import numpy as np
import pandas as pd
import brightway2 as bw
import logging
import sys
import networkx as nx
from ..utils.helper import networkx_path_list, mc_por
import random
import os

RECYCLING_LOSS = 0 # not used anymore
REUSE_LOSS = 0.05 # not used anymore
EOL_YEARS_REMAIN_CONST = 0.25
REPLACEMENT_BUFFER_FACTOR = 0.9

CURRENT_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(CURRENT_DIR)
print(PARENT_DIR)

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='logs.log', filemode='a',
                    level=logging.ERROR)


class Building:
    instances = []

    def __init__(self, givenname: str = "default", givenID: str = "IDXXX", location: str = "Over the rainbow", yearBuilt: int = 1948, givenlife: int = 50, givenarea: str = "100 m2", giventype: str = "residential", assemblies: list = []):
        self.area = givenarea
        self.name = givenname
        self.id = givenID
        self.location = location
        self.yearBuilt = yearBuilt
        self.life = givenlife
        self.assemblies = assemblies
        self.type = giventype
        self.__class__.instances.append(self)

    @classmethod
    def generate(cls, filename: str = "default") -> list:
        '''each row of the products df will become a class instance (object) in the products class'''
        try:
            df = pd.read_excel(filename, "Buildings", engine="openpyxl")
        except FileNotFoundError:
            raise FileNotFoundError(
                "the file you are trying to read from does not exist or you entered the wrong name")
        except ValueError as e:
            raise ValueError(e)
        return list(map(lambda x: cls(givenname=x[0], giventype=x[1], givenID=x[2], givenarea=x[3], givenlife=x[4], yearBuilt=x[5], location=x[6]), df.values.tolist()))

    @classmethod
    def connect_to_assemblies(cls):
        if len(Assemblies.instances) == 0:
            raise ValueError("Assemblies class is not generated yet")
        for building in cls.instances:
            building.assemblies = [
                assembly for assembly in Assemblies.instances if assembly.part_of in building.id]
            for assembly in building.assemblies:
                assembly.building = building
        print("buildings connected to assemblies!")

    @classmethod
    def generate_rpc(cls):
        for building in cls.instances:
            building.list_of_a_rpc = [
                assembly.rpc for assembly in building.assemblies]
            building.rpc = np.mean(building.list_of_a_rpc)
        print("buildings rpc calculated!")

    @classmethod
    def delete_all_instances(cls):
        for instance in cls.instances:
            del instance
        cls.instances = []


class Assemblies(object):
    instances = []
    number_of_assemblies = 0

    def __init__(self, assembly_name: str = "", assembly_type: str = "",
                 assembly_id: str = "", assembly_unit: str = "", assembly_amount: int = 0, part_of: str = "EMPTY"):
        self.type = assembly_type
        self.name = assembly_name
        self.amount = assembly_amount
        self.id = assembly_id
        self.unit = assembly_unit
        self.part_of = part_of
        self.products = []
        Assemblies.number_of_assemblies += 0
        self.__class__.instances.append(self)

    @classmethod
    def delete_all_instances(cls):
        for instance in cls.instances:
            del instance
        cls.instances = []

    # @classmethod
    # def group_by_type(cls) -> dict:
    #     '''this will group the the assembly by their type'''
    #     return {k: list(v) for k, v in groupby(sorted(cls.instances, key=lambda x: x.type), key=lambda x: x)}

    @classmethod
    def group_by_type(cls):
        return {obj.type: [o for o in cls.instances if o.type == obj.type] for obj in cls.instances}
    
    @classmethod
    def group_by_brand(cls):
        return {obj.brand_layer: [o for o in cls.instances if o.brand_layer == obj.brand_layer] for obj in cls.instances}
    
    # get assenblies by id
    @classmethod
    def get_assembly_by_id(cls, id: str):
        #if assembly not found
        if len([o for o in cls.instances if o.id == id]) == 0:
            raise ValueError("assembly not found")
        return [o for o in cls.instances if o.id == id][0]

    @property
    def brand_layer(self) -> str:
        if self.type.lower() == 'wall element':
            return 'Skin'
        if self.type.lower() == 'interior wall element':
            return 'Space Plan'
        if self.type.lower() == 'roof element':
            return 'Structure'
        if self.type.lower() == 'floor element':
            return 'Structure'
        if self.type.lower() == 'window element':
            return 'Skin'
        if self.type.lower() == 'door element':
            return 'Space Plan'
        if self.type.lower() == 'structural element':
            return 'Structure'
        if self.type.lower() == 'technical element':
            return 'Services'
        if self.type.lower() == 'aesthetic element':
            return 'Skin'
        if self.type.lower() == 'foundation element':
            return 'Structure'
        if self.type.lower() == 'ceiling element':
            return 'Space Plan'
        # a list of all possible returns
        # return ['Skin', 'Space Plan', 'Structure', 'Services', 'Skin', 'Structure', 'Services', 'Skin', 'Structure', 'Space Plan']
    @classmethod
    def generate(cls, filename: str = "default") -> list:
        '''each row of the Assemblies df will become a class instance (object) in the Assemblies class'''
        try:
            df = pd.read_excel(filename, "Assemblies", engine="openpyxl")
        except FileNotFoundError:
            raise FileNotFoundError(
                "the file you are trying to read from does not exist or you entered the wrong name")
        except ValueError as e:
            raise ValueError(e)
        return list(map(lambda x: Assemblies(assembly_name=x[0],
                                             assembly_type=x[1], assembly_id=x[2], assembly_amount=x[3], assembly_unit=x[4], part_of=x[5]), df.values.tolist()))

    def __str__(self) -> str:
        return f"{self.name}"

    @classmethod
    def get_ids(cls):
        id_list = []
        for obj in cls.instances:
            id_list.append(obj.id)
        return id_list

    @classmethod
    def generate_rpc(cls):
        '''this will generate the assembly rpc'''
        for assembly in cls.instances:
            assembly.list_of_p_rpc = [
                product.rpc for product in assembly.products]
            assembly.rpc = np.mean(assembly.list_of_p_rpc)
        print("assemblies rpc calculated!")

    def list_of_relations(self):
        '''this will generate a list of relations for an assembly'''
        assert len(self.products) != 0, "products are not generated yet"
        assert hasattr(self, "products"), "products are not connected yet"
        list_of_relations = []
        # a list of all connections of the products in the assembly
        for product in self.products:
            list_of_relations.extend(product.relations)
        return list_of_relations

    def can_be_detached(self):
        '''this will return a list of assemblies that can be detached'''
        relations = self.list_of_relations()
        to_check = []
        for relation in relations:
            if relation.is_external:
                to_check.append(relation)
        return all([relation.can_be_detached() for relation in to_check])


class Products(object):
    instances = []
    number_of_products = 0
    list_of_product_ids = []

    def __init__(self, name: str = "", name_in_lci: str = "", location: str = "", product_id: str = "",
                 part_of_assembly: str = "", base: bool = False,
                 disassembly_sequence: str = "", lci_code: str = "",
                 technical_life: float = 0, amount_per_assembly: float = 0,
                 functional_unit: str = "", recycled_content: int = 0, eol_type: str = "", transport_type: str = "",
                 replaced_amount: float = 0, years_of_replacements: list = [], sorting_type: str = "",
                 lhv: float = 0, incineration_r: float = 0, landfill_r: float = 0, recycling_r: float = 0,
                 disposal: str = "", recycling_lci: str = "", replacing_lci: str = ""):
        self.name = name
        self.location = location
        self.id = product_id
        self.base = base
        self.lci_code = lci_code
        self.__class__.list_of_product_ids.append(self.id)
        self.name_in_lci = name_in_lci
        self.ds = disassembly_sequence
        #  create a list of products in the disassembly sequence
        if self.ds is not np.nan:
            self.ds = self.ds.split(";")
        self.ds_tuple_list = list()
        if self.ds is not np.nan:
            for ds in self.ds:
                ds_tuple = (self.id, ds)
                self.ds_tuple_list.append(ds_tuple)
        self.amount = amount_per_assembly
        self.technical_life = technical_life
        self.part_of_assembly = part_of_assembly
        self.fu = functional_unit
        self.recycled_content = recycled_content
        self.eol_type = eol_type
        self.transport_type = transport_type
        self.years_of_replacements = years_of_replacements
        self.list_of_associated_activities = []
        self.__class__.instances.append(self)
        Products.number_of_products += 1
        self.log = {
            "replacements": [],
            "changes": [],
            "sync": []
        }
        self.replacements_affected_by = []
        self.replaced_amount = replaced_amount
        self.sorting_type = sorting_type
        self.LHV = lhv
        self.incineration_r = incineration_r
        self.landfill_r = landfill_r
        self.recycling_r = recycling_r
        self.disposal = disposal
        self.recycling_lci = recycling_lci
        self.replacing_lci = replacing_lci

    @classmethod
    def get_product_by_id(cls, id):
        '''this method will return the product object by its id'''
        # if product is not found
        if len([product for product in cls.instances if product.id == id]) == 0:
            raise Exception(f"the product {id} does not exist")
        return [product for product in cls.instances if product.id == id][0]

    @classmethod
    def connect_to_assembly(cls):
        '''this method will connect the products to the assemblies'''
        if len(Assemblies.instances) == 0:
            raise Exception("you need to generate the assemblies first")
        for product in cls.instances:
            try:
                product.assembly = [
                    assembly for assembly in Assemblies.instances if product.part_of_assembly == assembly.id][0]
            except IndexError:
                raise IndexError(
                    f"the assembly {product.part_of_assembly} does not exist for the product {product.id}")
            if not hasattr(product, "assembly"):
                raise Exception(
                    f"the assembly {product.part_of_assembly} does not exist for the product {product.id}")
            if product not in product.assembly.products:
                product.assembly.products.append(product)

    @classmethod
    def add_replacement_cycles(cls):
        '''this method will add the replacement cycles to the products'''
        for product in cls.instances:
            product.years_of_replacements = list(
                range(product.technical_life, int(REPLACEMENT_BUFFER_FACTOR*product.assembly.building.life), product.technical_life))

    @classmethod
    def generate(cls, filename: str = "default") -> list:
        '''each row of the products df will become a class instance (object) in the products class'''
        try:
            df = pd.read_excel(filename, "Products", engine="openpyxl")
        except FileNotFoundError:
            raise FileNotFoundError(
                "the file you are trying to read from does not exist or you entered the wrong name")
        except ValueError as e:
            raise ValueError(e)
        return list(map(lambda x: cls(name=x[0], name_in_lci=x[1], lci_code=x[2], location=x[3], product_id=x[4], part_of_assembly=x[5],
                                      disassembly_sequence=x[6], technical_life=x[7], amount_per_assembly=x[8],
                                      functional_unit=x[9], recycled_content=x[10], base=x[11], eol_type=x[12],
                                      transport_type=x[13]), df.values.tolist()))

    @property
    def number_of_replacements(self) -> int:
        return len(self.years_of_replacements)
    
    @property
    def number_of_replacements_updated(self) -> int:
        return len(self.years_of_replacements_updated)

    def __str__(self) -> str:
        return f"{self.id}, {self.name}"
    
    @property
    def number_of_reuses(self) -> int:
        # make sure that the product has reuse years
        assert hasattr(self, "disassembly_years"), "the product does not have reuse years run the detachment analysis first"
        return len(self.disassembly_years)

    @classmethod
    def generateDirectedGraph(cls):
        data = nx.DiGraph()
        data.add_nodes_from(cls.get_ids())
        for product in cls.instances:
            if len(product.ds_tuple_list) > 0:
                data.add_edges_from(product.ds_tuple_list)
        return data

    @classmethod
    def generateRelationsClass(cls, mode: float = 1.0):
        return list(map(lambda x: Relations(t=x[0], m=mode), [[x] for x in Products.generateDirectedGraph().edges]))
        
    @classmethod
    def get_ids(cls):
        id_list = []
        for obj in cls.instances:
            id_list.append(obj.id)
        return id_list

    @classmethod
    def add_total_amounts_to_product(cls):
        '''This function will add the total amount of product based on the amount of assemblies'''
        for product in cls.instances:
            if not hasattr(product, "assembly"):
                raise AttributeError(
                    "Assemblies have not been connected yet.")
            else:
                product.total_starting_amount = product.amount * product.assembly.amount
        print("updated total amount of products")

    @classmethod
    def detachment_analysis(cls):
        '''this will generate the detachment analysis for each product'''
        for product in cls.instances:
            if hasattr(product, "relations"):
                pass
            else:
                raise AttributeError(
                    f"Relations have not been generated yet to the product {product}.")
            relations_can_be_detached: list[bool] = []
            for relation in product.relations:
                if not hasattr(relation, "can_be_detached"):
                    raise AttributeError(
                        "Relations detachment analysis have not been generated yet. Please run the detachment analysis method first.")
                # if relation is not connection then skip
                if relation.is_connection is False or relation.is_connection == 0:
                    continue
                elif relation.product1object.base and relation.product2object.base:
                    relation.type = "B2B"
                    relations_can_be_detached.append(
                        relation.can_be_detached)
                elif not relation.product1object.base and relation.product2object.base and not product.base:
                    relation.type = "A2B"
                    relations_can_be_detached.append(
                        relation.can_be_detached)
                elif relation.product1object.base and not relation.product2object.base and not product.base:
                    relation.type = "B2A"
                    relations_can_be_detached.append(
                        relation.can_be_detached)
                else:
                    relation.type = "A2A"
                    relations_can_be_detached.append(
                        relation.can_be_detached)
                if relation.product1object.assembly.id != relation.product2object.assembly.id:
                    relation.is_external = True
            if all(relations_can_be_detached):
                product.can_be_detached = True
            else:
                product.can_be_detached = False
    
        
    def get_min_rpc(self, typ: str, weights_list: list = [1, 1, 1, 1]) -> float:
        '''this will returns the min rpc for a given product given the type of relation and the weights based on importance'''
        assert hasattr(self, "relations"), f"Relations have not been generated yet. {self.id}"
        calc_ca = [relation.ca for relation in self.relations if relation.is_connection and relation.type in typ]
        calc_ct = [relation.ct for relation in self.relations if relation.is_connection and relation.type in typ]
        calc_fc = [relation.fc for relation in self.relations if relation.is_connection and relation.type in typ]
        calc_cr = [relation.cr for relation in self.relations if relation.is_connection and relation.type in typ]

        d = np.column_stack([calc_ca, calc_ct, calc_fc, calc_cr])
        if len(d) > 0:
            p = np.average(d, axis=1, keepdims=True, weights=weights_list)
            min_rpc = np.min(p)
        else:
            min_rpc = 1.0
        return min_rpc
    
    def get_min_ddf(self) -> np.array:
        '''this will generate the min ddf for given product'''
        # assert that self has atr relations
        assert hasattr(self, "relations"), f"Relations have not been generated yet. {self.id}"
        calc_ca = min([relation.ca for relation in self.relations])
        calc_ct = min([relation.ct for relation in self.relations])
        calc_fc = min([relation.fc for relation in self.relations])
        calc_cr = min([relation.cr for relation in self.relations])
        return np.array([calc_ca, calc_ct, calc_fc, calc_cr])


    @classmethod
    def generate_rpc(cls):
        '''this will generate the rpc for each product'''
        for self in cls.instances:
            if self.base:
                self.rpc = self.get_min_rpc(typ=["B2B"])
            else:
                self.rpc = self.get_min_rpc(typ=["A2A", "A2B", "B2A"])
        print("product rpc calculated!")
    
    @classmethod
    def detachment_analysis_access_dep(cls):
        '''This function deals with access type dependencies'''
        for product in cls.instances:
            if hasattr(product, "relations"):
                pass
            else:
                raise AttributeError(
                    f"Relations have not been generated yet to the product {product}.")
            for relation in product.relations:
                if relation.is_connection:
                    continue
                else:
                    relation.ca = relation.product2object.get_min_ddf()[0]
                    relation.ct = relation.product2object.get_min_ddf()[1]
                    relation.fc = relation.product2object.get_min_ddf()[2]
                    relation.cr = relation.product2object.get_min_ddf()[3]
                    
                                    
    @classmethod
    def update_years_of_replacements_based_on_detachability(cls):
        '''this will update the years of replacements based on the detachability of the products and the relations
        '''
        network_data = cls.generateDirectedGraph()
        for product in cls.instances:
            # initialize the updated years of replacement of the product
            product.years_of_replacements_updated = product.years_of_replacements
            product.disassembly_years = set()
            product.disassembly_years_log = []
            # initialize the log of the updates
            # product.updates_log = []
        for product in cls.instances:
            # If the product will not be replaced why check anything but need to be careful because this might change after the loop, thus the list on top
            if len(product.years_of_replacements_updated) == 0:
                continue
            down_stream_product_ids_list = networkx_path_list(
                data=network_data, node=product.id)
            for down_stream_product_id in down_stream_product_ids_list:
                # get product by id
                in_the_way_product = cls.get_product_by_id(down_stream_product_id)
                # check if downstream product can be detached
                if in_the_way_product.can_be_detached:
                    # add this as a prop in a seperate asbract method because we then use len after set on the reuse years
                    # in_the_way_product.reuses = in_the_way_product.reuses + len(product.years_of_replacements_updated2)
                    # the years at which the product will be reused
                    in_the_way_product.disassembly_years.update(product.years_of_replacements_updated)
                    # add to the log why the product needs to be disassembled
                    in_the_way_product.disassembly_years_log.append(
                        f"{product.id} will be replaced at {product.years_of_replacements_updated} and thus {in_the_way_product.id} will be disassembled")
                else:
                    additional_years = [year for year in product.years_of_replacements_updated if year not in in_the_way_product.years_of_replacements_updated]
                    in_the_way_product.years_of_replacements_updated = in_the_way_product.years_of_replacements_updated + additional_years
        for product in cls.instances:
            product.disassembly_years = list(product.disassembly_years)
            product.disassembly_years.sort()
            # check if there is any overlap between product.disassembly_years and product.years_of_replacements_updated and remove the years of replacements from reuse years
            product.disassembly_years = [year for year in product.disassembly_years if year not in product.years_of_replacements_updated]
    @classmethod
    def connect_products_to_relations(cls):
        '''this will connect the relations objects with the products objects'''
        for product in cls.instances:
            product.relations = [relation for relation in Relations.instances if relation.product1object.id ==
                                 product.id or relation.product2object.id == product.id]
            if len(product.relations) == 0:
                logging.error(
                    f"Possible error product {product.id} has no relations!")
        print("relations connected with products!")

    @classmethod
    def material_flow_and_replacements(cls, mf_mcs: int = 100, constants: tuple = (1.09186399, 0.44315069, 7.58473472, -0.07522362)):
        '''this will generate the replaced amount for each product after the upstreams are considered in terms of if they can be detached or not so if not then the total amount will be added
        if it can be detached then it will add to the (reuse years) which is what we use here to calculate the material flow'''
        for product in cls.instances:
            product.material_flow = {0: product.total_starting_amount}
            product.material_flow_updated = {0: product.total_starting_amount}
            product.replaced_amount = 0
            product.replaced_amount_updated = 0
            product.replaced_amount_updated_array = 0
            product.reuse_loss = 0
            product.total_reuse_product_amount_array = 0
            one_reuse_product_amount_array = 0
            for year in product.years_of_replacements: # Replacements from TL without considering upstreams
                material_flow = {f"{year}": product.total_starting_amount}
                product.material_flow.update(material_flow)
                product.replaced_amount = product.replaced_amount + product.total_starting_amount
            for year in product.years_of_replacements_updated:  # Replacements from TL with considering upstreams
                material_flow = {f"{year}": product.total_starting_amount}
                product.material_flow_updated.update(material_flow)
                product.replaced_amount_updated = product.replaced_amount_updated + product.total_starting_amount
            for year in sorted(product.disassembly_years): # replacements from disassembly cycles
                if year not in product.material_flow_updated:
                    amount_added_on_reuse_array = mc_por(product, mf_mcs, constants) # previously reuse_prob_array = mc_por(product)
                    one_reuse_product_amount_array = amount_added_on_reuse_array * product.total_starting_amount
                    one_reuse_product_median_amount = np.median(one_reuse_product_amount_array)
                    material_flow = {f"{year}": one_reuse_product_median_amount}
                    product.material_flow_updated.update(material_flow)
                    product.total_reuse_product_amount_array += one_reuse_product_amount_array
            product.median_amount_added_after_dis_cycle = np.median(one_reuse_product_amount_array)
            product.median_amount_added_after_dis_cycles = np.median(product.total_reuse_product_amount_array)
            product.replaced_amount_updated_array = product.replaced_amount_updated + product.total_reuse_product_amount_array
            # if the above results in a float or int instead of an array then convert it to an array of the same value repeated to the mc sim number
            if isinstance(product.replaced_amount_updated_array, float) or isinstance(product.replaced_amount_updated_array, int):
                product.replaced_amount_updated_array = np.full(mf_mcs, product.replaced_amount_updated_array)
            product.replaced_amount_updated = product.replaced_amount_updated + product.median_amount_added_after_dis_cycles
            product.total_amount_with_replacements = product.replaced_amount + product.total_starting_amount # just add the first one plus the replaced amount
            product.total_amount_with_replacements_updated = product.total_starting_amount +  product.replaced_amount_updated
            product.total_amount_with_replacements_array_updated = product.replaced_amount_updated_array + product.total_starting_amount



    @classmethod
    def add_eol_info(cls):
        '''this will add all the eol information to the products'''
        # read the eol information from the excel file
        # print cwd
        df_eol = pd.read_excel(f"{PARENT_DIR}/sen/sen-eol.xlsx")
        # df_eol = pd.read_excel(f"..sen/sen-eol.xlsx")
        # add the eol information to the products
        for product in cls.instances:
            try:
                product.sorting_type = df_eol.loc[df_eol['Name'] ==
                                                  product.eol_type]["Sorting_process_module_C3"].item()
                product.disposal = tuple(df_eol.loc[df_eol['Name'] ==
                                                    product.eol_type]["Disposal_module_C4"].item().split(";"))
                product.replacing_lci = tuple(df_eol.loc[df_eol['Name'] ==
                                                         product.eol_type]["EoL_module_D2_replacing"].item().split(";"))
                product.recycling_lci = tuple(df_eol.loc[df_eol['Name'] ==
                                                         product.eol_type]["EoL_module_D2_recycling"].item().split(";"))
                product.Incineration_lci = tuple(df_eol.loc[df_eol['Name'] ==
                                                            product.eol_type]["Incineration_dataset"].item().split(";"))
                product.lhv = df_eol.loc[df_eol['Name'] ==
                                         product.eol_type]["EoL_module_D3_LHV"].item()
                product.landfill_r = df_eol.loc[df_eol['Name']
                                                == product.eol_type]["landfilling"].item()
                product.incineration_r = df_eol.loc[df_eol['Name']
                                                    == product.eol_type]["incineration"].item()
                product.recycling_r = df_eol.loc[df_eol['Name']
                                                 == product.eol_type]["recycling"].item()
                product.eol_transport_distance = df_eol.loc[df_eol['Name']
                                                            == product.eol_type]["transport distance"].item()
                product.eol_transport_type = "transport, freight, lorry 16-32 metric ton, EURO5"
            except ValueError:
                raise ValueError(
                    f"Product: {product}, has something wrong with eol type")

    @classmethod
    def delete_all_instances(cls):
        for instance in cls.instances:
            del instance
        cls.instances = []

    @classmethod
    def clean_up(cls):
        '''Cleans intermidiate variables to save memory'''
        # list of object attributes to delete
        list_of_attributes = ['base',
                            'disassembly_years',
                            'disposal',
                            'ds',
                            'ds_tuple_list',
                            'eol_transport_distance',
                            'eol_transport_type',
                            'eol_type',
                            'fu',
                            'impactsMC_c4_array_incineration',
                            'impactsMC_c4_array_landfill',
                            'impactsMC_c4_incineration',
                            'impactsMC_c4_landfill',
                            'impactsMC_d1',
                            'impactsMC_d2',
                            'impactsMC_d2_array',
                            'impactsMC_d2_rec',
                            'impactsMC_d2_rep',
                            'impactsMC_d3',
                            'impactsMC_d3_array',
                            'impactsMC_d3_elec',
                            'impactsMC_d3_heat',
                            'impactsMC_d_rpc',
                            'impactsMC_d_rpc_array',
                            'impactsMC_d_standard',
                            'impactsMC_d_standard_array',
                            'impactsMC_d_standard_reuse',
                            'impacts_c4_array_incineration',
                            'impacts_c4_array_landfill',
                            'impacts_c4_incineration',
                            'impacts_c4_landfill',
                            'impacts_d1',
                            'impacts_d2',
                            'impacts_d2_array',
                            'impacts_d2_rec',
                            'impacts_d2_rep',
                            'impacts_d3',
                            'impacts_d3_array',
                            'impacts_d3_elec',
                            'impacts_d3_heat',
                            'incineration_r',
                            'instances',
                            'landfill_r',
                            'lci_code',
                            'lhv',
                            'list_of_associated_activities',
                            'list_of_product_ids',
                            'location',
                            'log',
                            'material_flow',
                            'material_flow_updated',
                            'median_amount_added_after_dis_cycle',
                            'median_amount_added_after_dis_cycles',
                            'name',
                            'name_in_lci',
                            'number_of_products',
                            'number_of_replacements',
                            'number_of_replacements_updated',
                            'number_of_reuses',
                            'part_of_assembly',
                            'recycled_content',
                            'recycling_lci',
                            'recycling_r',
                            'relations',
                            'replaced_amount',
                            'replaced_amount_updated',
                            'replaced_amount_updated_array',
                            'replacements_affected_by',
                            'replacing_lci',
                            'reuse_loss',
                            'sorting_type',
                            'total_starting_amount',
                            'transport_type',
                            'years_of_replacements',
                            'years_of_replacements_updated']
        for instance in cls.instances:
            for attribute in list_of_attributes:
                try:
                    delattr(instance, attribute)
                except AttributeError:
                    pass
                    


class Relations(object):
    instances = []
    list_of_relations = []
    df = pd.DataFrame(columns=["Connections"])

    def __init__(self, t: tuple = (), m: float = 1.0, is_connection: bool = True):
        self.t = t
        self.product1 = self.t[0]
        self.product2 = self.t[1]
        self.product1object = [
            p for p in Products.instances if p.id == self.t[0]][0]
        self.product2object = [
            p for p in Products.instances if p.id == self.t[1]][0]
        self.__class__.instances.append(self)
        self.__class__.list_of_relations.append(self.t)
        self.ct = m
        self.ca = m
        self.cr = m
        self.fc = m
        # self.rpc = (self.ca + self.cr + self.fc + self.ct) / 4
        self.is_connection = is_connection

    def __str__(self) -> str:
        return f"{self.t}"
    
    @property
    def rpc(self):
        return (self.ca + self.cr + self.fc + self.ct) / 4

    @classmethod
    def delete_all_instances(cls):
        for instance in cls.instances:
            del instance
        cls.instances = []
    
    @classmethod
    def get_relation_by_id(cls, t):
        '''this method will return the relation object by its t value (product1, product2))'''
        # if product is not found
        if len([relation for relation in cls.instances if relation.t == t]) == 0:
            raise Exception(f"the product {id} does not exist")
        return [relation for relation in cls.instances if relation.t == t][0]

    def reset_indicators(self):
        self.ct = 1.00
        self.ca = 1.00
        self.cr = 1.00
        self.fc = 1.00
        self.rpc = (self.ca + self.cr + self.fc + self.ct) / 4

    @classmethod
    def get_ids(cls):
        id_list = []
        for obj in cls.instances:
            id_list.append(obj.t)
        return id_list

    @classmethod
    def detachment_analysis(cls):
        for obj in cls.instances:
            # make sure that relation has is connection atrbute
            assert hasattr(obj, "is_connection"), 'Relations must have is_connection attribute'
            # if dependency is structural consider all indicators
            # print(obj.t, obj.is_connection)
            if obj.is_connection is True or obj.is_connection == 1:
                if obj.ct < 0.2 or obj.ca < 0.2 or obj.fc <= 0.1 or obj.cr <= 0.1:
                    obj.can_be_detached = False
                else:
                    obj.can_be_detached = True
            else:
                obj.can_be_detached = True
            # if obj.ct < 0.2 or obj.ca < 0.2 or obj.fc <= 0.1 and obj.cr <= 0.1 and obj.is_connection is True:
            #     obj.can_be_detached = False
            # elif obj.is_connection is False or obj.is_connection == 0:
            #     obj.can_be_detached = True
            # else:
            #     print('possible error in is_connection attribute')
            #     obj.can_be_detached = True

    @classmethod
    def composite_products(cls):
        '''needs to run after relations are connected to products'''
        for obj in cls.instances:
            if hasattr(obj, "product1object"):
                continue
            elif obj.fc == 0.1:
                obj.product1object.years_of_replacements = obj.product2object.years_of_replacements
                setattr(obj, "as_composite", True)
            elif obj.fc > 0.1:
                setattr(obj, "as_composite", False)
            else:
                raise Exception("Relations not connected to products")

    @classmethod
    def relations_dataframe(cls) -> pd.DataFrame:
        '''this will return a dataframe of all the relations'''
        list_of_joined_relation_tuples = list(
            map(''.join, cls.list_of_relations))
        list_names_tuples = []
        for relation in Relations.instances:
            try:
                mytuple = ("To remove: " + relation.product1object.name,
                           relation.product2object.name)
            except AttributeError as e:
                logging.error(
                    f"Probably {relation.product1object.id} has a relation with a non existent product, error was {e}")
                print("Error check log files")
                sys.exit(1)
            except TypeError as e:
                logging.error(
                    f"Probably {relation.product1object.id} or {relation.product2object.id} is missing a name, error was {e}")
                print("Error check log files")
                sys.exit(1)

            list_names_tuples.append(mytuple)
        list_of_joined_name_tuples = list(
            map(' We need to remove --> '.join, list_names_tuples))
        output_df = pd.DataFrame(Relations.list_of_relations, columns=[
                                 "Relation_id1", "Relation_id2"])
        output_df['Relation_id_as_tuple'] = list(
            zip(output_df.Relation_id1, output_df.Relation_id2))
        output_df = output_df.drop(["Relation_id1", "Relation_id2"], axis=1)
        output_df["Relation_id"] = list_of_joined_relation_tuples
        output_df["Explained"] = list_of_joined_name_tuples
        output_df["Is_connection"] = True
        output_df["Connection_type"] = ""
        output_df["Connection_access"] = ""
        output_df["Form_containment"] = ""
        output_df["Crossings"] = ""
        return output_df

    def output_relations_dataframe_to_excel(df: pd.DataFrame, filename: str = "default", write_output=False):
        '''this will write the relations dataframe to excel'''
        pd_to_print = df
        pd_read = pd.read_excel(
            filename, sheet_name="Relations", engine="openpyxl")
        df_toprint = pd.concat([pd_read, pd_to_print])
        df_toprint = df_toprint.drop_duplicates(
            subset=['Relation_id'], keep="last")
        relation_condition = pd_to_print['Relation_id'].isin(
            pd_read['Relation_id'])
        # print(pd_read)
        # print(df_toprint)
        # print(words_in_animals_condition.iloc)
        # list_of_index = words_in_animals_condition[words_in_animals_condition == False]
        # print(list_of_index)
        if not relation_condition.all():
            if write_output:
                print("Connections changed")
            try:
                writer = pd.ExcelWriter(filename,
                                        engine='openpyxl', mode='a', if_sheet_exists="overlay")
                df_toprint.to_excel(
                    writer, sheet_name='Relations', index=0, startrow=0)
                writer.save()
            except PermissionError:
                print(
                    "please close {} in order to update your connections".format(filename))
                logging.error(
                    "please close {} in order to update your connections".format(filename))
        else:
            if write_output:
                print("Connections are already there")
        try:
            writer2 = pd.ExcelWriter(
                f"{filename}_connections.xlsx", engine='openpyxl')
            pd_to_print.to_excel(writer2, sheet_name='Relations', index=0)
            writer2.save()
        except PermissionError as e:
            print("To update connections excel file, close it first ", e)
            logging.error(
                "To update connections excel file, close it first {}".format(e))

    @classmethod
    def update_connections_to_relations_objects(cls, filename: str = "default", mode: str = "user input", assembly: Assemblies = None):
        '''this will update the relations objects with the connections based on the excel file
        mode can be "user input" or "keep"'''
        if not mode == "keep":
            ca = [0.1, 0.4, 0.8, 1]
            ct = [0.1, 0.2, 0.6, 0.8, 1]
            cr = [0.1, 0.4, 1]
            fc = [0.1, 0.2, 0.8, 1]
            df = pd.read_excel(filename, "Relations", engine="openpyxl")
            if mode == "user input":
                for relation in cls.instances:
                    try:
                        relation.ct = float(
                            df.loc[df["Relation_id_as_tuple"] == str(relation.t)]["Connection_type"])
                    except (TypeError, ValueError) as e:
                        print("Error has occurred check log files")
                        logging.error(
                            f"input error in connection: {relation.t}")
                        sys.exit(1)
                    relation.ca = float(
                        df.loc[df["Relation_id_as_tuple"] == str(relation.t)]["Connection_access"])
                    relation.cr = float(
                        df.loc[df["Relation_id_as_tuple"] == str(relation.t)]["Crossings"])
                    relation.fc = float(
                        df.loc[df["Relation_id_as_tuple"] == str(relation.t)]["Form_containment"])
                    if relation.ca == np.nan or relation.cr == np.nan or relation.fc == np.nan or relation.is_connection == np.nan:
                        logging.error(
                            f"Relation: {relation.t} is missing a value, check it")
            if mode == "lowest_assembly":
                for relation in cls.instances:
                    if relation.product1object.assembly.id == assembly.id or relation.product2object.assembly.id == assembly.id:
                        relation.ct = 0.1
                        relation.ca = 0.1
                        relation.cr = 0.1
                        relation.fc = 0.1
            if mode == "highest_assembly":
                for relation in cls.instances:
                    if relation.product1object.assembly.id == assembly.id or relation.product2object.assembly.id == assembly.id:
                        relation.ct = 1
                        relation.ca = 1
                        relation.cr = 1
                        relation.fc = 1
            if mode == "low_assembly":
                for relation in cls.instances:
                    if relation.product1object.assembly.id == assembly.id or relation.product2object.assembly.id == assembly.id:
                        relation.ct = random.choice(ct[:2])
                        relation.ca = random.choice(ca[:2])
                        relation.cr = random.choice(cr[:2])
                        relation.fc = random.choice(fc[:2])
            if mode == "high_assembly":
                for relation in cls.instances:
                    if relation.product1object.assembly.id == assembly.id or relation.product2object.assembly.id == assembly.id:
                        relation.ct = random.choice(ct[3:])
                        relation.ca = random.choice(ca[3:])
                        relation.cr = random.choice(cr[2:])
                        relation.fc = random.choice(fc[3:])
            if mode == "rng_assembly":
                for relation in cls.instances:
                    if relation.product1object.assembly.id == assembly.id or relation.product2object.assembly.id == assembly.id:
                        relation.ct = random.choice(ct)
                        relation.ca = random.choice(ca)
                        relation.cr = random.choice(cr)
                        relation.fc = random.choice(fc)
                    
            if mode == "low_product":
                for relation in cls.instances:
                    relation.ct = random.choice(ct[:2])
                    relation.ca = random.choice(ca[:2])
                    relation.cr = random.choice(cr[:2])
                    relation.fc = random.choice(fc[:2])
            if mode == "high_product":
                for relation in cls.instances:
                    relation.ct = random.choice(ct[3:])
                    relation.ca = random.choice(ca[3:])
                    relation.cr = random.choice(cr[2:])
                    relation.fc = random.choice(fc[3:])
            if mode == "rng_product":
                for relation in cls.instances:
                    relation.ct = random.choice(ct)
                    relation.ca = random.choice(ca)
                    relation.cr = random.choice(cr)
                    relation.fc = random.choice(fc)
        cls.relations_add_is_connection(filename)

    def mc_for_assemblies(assemblies: list[str], mode: str):
        ca = [0.1, 0.4, 0.8, 1]
        ct = [0.1, 0.2, 0.6, 0.8, 1]
        cr = [0.1, 0.4, 1]
        fc = [0.1, 0.2, 0.8, 1]
        # find assemblies in Assemblies.instances by matching id
        my_assemblies = [assembly for assembly in Assemblies.instances if assembly.id in assemblies]
        for assembly in my_assemblies:
            my_products = [product for product in Products.instances if product.assembly.id == assembly.id]
            for product in my_products:
                my_rel = [relation for relation in Relations.instances if relation.product1object.id == product.id or relation.product2object.id == product.id]
                for relation in my_rel:
                    # if relation is not connection skip
                    if relation.is_connection is False:
                        continue
                    elif mode == "lowest_assembly":
                        relation.ct = 0.1
                        relation.ca = 0.1
                        relation.cr = 0.1
                        relation.fc = 0.1
                    elif mode == "highest_assembly":
                        relation.ct = 1
                        relation.ca = 1
                        relation.cr = 1
                        relation.fc = 1
                    elif mode == "low_assembly":
                        relation.ct = random.choice(ct[:2])
                        relation.ca = random.choice(ca[:2])
                        relation.cr = random.choice(cr[:2])
                        relation.fc = random.choice(fc[:2])
                    elif mode == "high_assembly":
                        relation.ct = random.choice(ct[3:])
                        relation.ca = random.choice(ca[3:])
                        relation.cr = random.choice(cr[2:])
                        relation.fc = random.choice(fc[3:])
                    elif mode == "rng_assembly":
                        relation.ct = random.choice(ct)
                        relation.ca = random.choice(ca)
                        relation.cr = random.choice(cr)
                        relation.fc = random.choice(fc)

    @classmethod
    def relations_add_is_connection(cls, filename: str = "default"):
        df = pd.read_excel(filename, "Relations", engine="openpyxl")
        for relation in cls.instances:
            relation.is_connection = bool(df.loc[df["Relation_id_as_tuple"] == str(
                relation.t)]["Is_connection"].values[0])


class LCAh:
    instances = []

    def __init__(self) -> None:
        self.codeLib = {}
        self.searchLib = {}
        self.lcaLib = {}
        self.activityLib = {}
        self.method = ""
        self.mclcaLib = {}
        self.mainDatabase = bw.Database("ecoi_3.8_cutoff")
        self.sortingDatabase = bw.Database("sorting_eol_sen")
        self.transporta4Database = bw.Database("transport_a4_sen")
        self.recyclingDatabase = bw.Database("impacts_recycling")

        self.__class__.instances.append(self)
        bw.projects.set_current("circularLCA")

    @property 
    def get_list_of_methods(self):
        return [method for method in bw.methods if str(self.method) in str(method)]
    
    @property
    def get_list_of_activities(self):
        return [act for act in self.mainDatabase]
    
    @property
    def get_list_of_units(self):
        return []

    def get_activity(self):
        not_found_code = []
        not_found_search = []
        code_found = {}
        search_found = {}

        if len(self.codeLib) > 0:
            for code in self.codeLib.items():
                # find if code is in code_found keys
                if code[1] in code_found.keys():
                    self.activityLib[f"{code[0]}"] = code_found[code[1]]
                    print(f"code {code[1]} already found")
                    continue
                else:
                    print(f"searching for code {code}")
                    activity = [
                        act for act in self.mainDatabase if fr"{str(code[1])}" in act['code']]
                    if len(activity) == 1:
                        self.activityLib[f"{code[0]}"] = activity[0]
                        code_found[code[1]] = activity[0]
                    elif len(activity) > 1:
                        self.activityLib[f"{code[0]}"] = activity[0]
                        logging.error(
                            f"found more than one activity for code: {code} in the main database")
                        code_found[code[1]] = activity[0]
                    if len(activity) == 0:
                        not_found_code.append(code)
        if len(self.searchLib) > 0:
            for search in self.searchLib.items():
                # find if search is in search_found keys
                if search[1][0] in search_found.keys():
                    self.activityLib[f"{search[0]}"] = search_found[search[1][0]]
                    print(f"search {search[1][0]} already found")
                    continue
                else:
                    print(f"searching for search: {search}")
                    activity = [
                        act for act in self.mainDatabase if fr"{str(search[1][0])}" in act['name'] and fr"{str(search[1][1])}" in act['location'] and fr"{str(search[1][2])}" in act['reference product']]
                    if len(activity) == 1:
                        self.activityLib[f"{search[0]}"] = activity[0]
                        search_found[search[1][0]] = activity[0]
                        if search in not_found_search:
                            not_found_search.remove(search)
                    elif len(activity) > 1:
                        self.activityLib[f"{search[0]}"] = activity[0]
                        logging.error(
                            f"found more than one activity for search: {search} in the main database")
                        search_found[search[1][0]] = activity[0]
                        if search in not_found_search:
                            not_found_search.remove(search)
                    if len(activity) == 0:
                        not_found_search.append(search)

                    activity = [
                        act for act in self.transporta4Database if fr"{str(search[1][0])}" in act['name'] and fr"{str(search[1][1])}" in act['location'] and fr"{str(search[1][2])}" in act['reference product']]
                    if len(activity) == 1:
                        self.activityLib[f"{search[0]}"] = activity[0]
                        if search in not_found_search:
                            not_found_search.remove(search)
                        search_found[search[1][0]] = activity[0]

                    elif len(activity) > 1:
                        self.activityLib[f"{search[0]}"] = activity[0]
                        logging.error(
                            f"found more than one activity for search: {search} in the main database")
                        search_found[search[1][0]] = activity[0]
                        if search in not_found_search:
                            not_found_search.remove(search)
                    if len(activity) == 0:
                        not_found_search.append(search)

                    activity = [
                        act for act in self.sortingDatabase if fr"{str(search[1][0])}" in act['name'] and fr"{str(search[1][1])}" in act['location'] and fr"{str(search[1][2])}" in act['reference product']]
                    if len(activity) == 1:
                        self.activityLib[f"{search[0]}"] = activity[0]
                        search_found[search[1][0]] = activity[0]
                        if search in not_found_search:
                            not_found_search.remove(search)
                    elif len(activity) > 1:
                        self.activityLib[f"{search[0]}"] = activity[0]
                        logging.error(
                            f"found more than one activity for search: {search} in the main database")
                        search_found[search[1][0]] = activity[0]
                        if search in not_found_search:
                            not_found_search.remove(search)
                    if len(activity) == 0:
                        not_found_search.append(search)

    def get_activityLib(self, product: Products):
        print(f"adding activities for {product}......")
        if product.lci_code is not np.nan:
            self.codeLib[f"{product.id}"] = product.lci_code
        if product.lci_code is np.nan and product.name_in_lci != "" and product.location != "":
            self.searchLib[f"{product.id}"] = (
                product.name_in_lci, product.location)
        if product.lci_code is np.nan and product.name_in_lci != "" and product.location == "":
            self.searchLib[f"{product.id}"] = (product.name_in_lci, "", "")
        if product.transport_type is not np.nan:
            self.searchLib[f"{product.id}_a4"] = (
                f"sen_{product.transport_type}_a4_transport", "", "")
        else:
            logging.error(f"transport_type is not defined for {product.id}")
        try:
            if product.sorting_type is not np.nan:
                self.searchLib[f"{product.id}_c3"] = (
                    product.sorting_type, "", "")
            else:
                logging.error(f"sorting_type is not defined for {product.id}")
        except IndexError:
            logging.error(
                f"sorting_type for {product.id} is not in the right format")
        try:
            if product.disposal is not np.nan:
                self.searchLib[f"{product.id}_c4"] = (
                    product.disposal[0], product.disposal[2], product.disposal[1])
            else:
                logging.error(f"disposal is not defined for {product.id}")
        except IndexError:
            logging.error(
                f"disposal for {product.id} is not in the right format {product.disposal}")
        try:
            if product.recycling_lci is not np.nan:
                self.searchLib[f"{product.id}_d2_rec"] = (
                    product.recycling_lci[0], product.recycling_lci[2], product.recycling_lci[1])
            else:
                logging.error(f"recycling_lci is not defined for {product.id}")
        except IndexError:
            logging.error(
                f"recycling_lci for {product.id} is not in the right format")
        try:
            if product.replacing_lci is not np.nan:
                self.searchLib[f"{product.id}_d2_rep"] = (
                    product.replacing_lci[0], product.replacing_lci[2], product.replacing_lci[1])
            else:
                logging.error(f"replacing_lci is not defined for {product.id}")
        except IndexError:
            logging.error(
                f"replacing_lci for {product.id} is not in the right format")
        try:
            if product.Incineration_lci is not np.nan:
                self.searchLib[f"{product.id}_Incineration"] = (
                    product.Incineration_lci[0], product.Incineration_lci[2], product.Incineration_lci[1])
            else:
                logging.error(
                    f"Incineration_lci is not defined for {product.id}")
        except IndexError:
            logging.error(
                f"Incineration_lci for {product.id} is not in the right format")
        self.codeLib["d3_elec"] = "6b62fc44be3477f59828d95cf271337f"
        self.codeLib["d3_heat"] = "e1131ec939080485eaafc6d75a679490"
        self.codeLib["c2_transport"] = "711532d84a97f77b986aec908783769f"

    def get_lca_lib(self):
        myDict = {}
        myMethods = [method for method in bw.methods if str(
            self.method) in str(method)]
        list_of_activities = list(set(self.activityLib.values()))
        for act in list_of_activities:
            print("calculating LCA for: " + str(act))
            impacts = []
            temp_act_dict = {str(act): []}
            myDict.update(temp_act_dict)
            try:
                myLCA = bw.LCA({act: 1}, myMethods[0])
            except IndexError:
                logging.error(
                    f"no method found for {self.method} in the current bw2 database")
                sys.exit(1)
            except KeyError as k:
                logging.error(
                    f"something went wrong with the activity {act} LCA calculation {k}")
                print("something went wrong with an activity LCA calculation")
                sys.exit(1)
            myLCA.lci()
            myLCA.lcia()
            for category in myMethods:
                myLCA.switch_method(category)
                myLCA.lcia()
                impacts.append(myLCA.score)
            myDict[str(act)] = np.array(impacts)
        self.lcaLib = myDict
        print("LCA calculation finished")

    def get_multiImpactMonteCarloLCA(self, iterations=20):
        myMethods = [method for method in bw.methods if str(
            self.method) in str(method)]
        list_of_activities = list(set(self.activityLib.values()))
        myDict = {}
        for act in list_of_activities:
            print("running Monte Carlo LCA for: ", act)
            temp_act_dict = {str(act): []}
            myDict.update(temp_act_dict)
            # Step 1
            MC_lca = bw.MonteCarloLCA({act: 1})
            MC_lca.lci()
            # Step 2
            C_matrices = {}
            # Step 3
            for method in myMethods:
                MC_lca.switch_method(method)
                C_matrices[method] = MC_lca.characterization_matrix
            # Step 4
            results = np.empty((len(myMethods), iterations))
            # Step 5
            for iteration in range(iterations):
                next(MC_lca)
                for method_index, method in enumerate(myMethods):
                    results[method_index, iteration] = (
                        C_matrices[method]*MC_lca.inventory).sum()
            myDict[str(act)].append(results)
        self.mclcaLib = myDict
        print("Monte Carlo LCA calculation finished")


if __name__ == "__main__":
    print('do not run')

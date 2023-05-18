from ..Objects.objects import Products, Assemblies, Building, Relations, LCAh
from ..utils.helper import yearsRemain, randomChoiceArray, mc_por, mc_por_impact
import logging
import numpy as np
import copy

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='logs.log', filemode='a',
                    level=logging.ERROR)



RECYCLING_LOSS = 0.05 # 5% loss in recycling
EOL_YEARS_REMAIN_CONST = 0.25 # 25% of the product's life is left when it reaches EOL
REPLACEMENT_BUFFER_FACTOR = 0.9 # 10% of the building's life is left when it is replaced
AMOUNT_MC_SIM = 100 # number of MC simulations to run

class Analysis:
    def reset():
        Products.delete_all_instances()
        Assemblies.delete_all_instances()
        Building.delete_all_instances()
        Relations.delete_all_instances()
    print("resetting all objects")

    @classmethod
    def generate_objects(cls, filename: str, default_rel: float):
        Products.generate(filename=filename)
        Assemblies.generate(filename=filename)
        Building.generate(filename=filename)
        Products.generateRelationsClass(mode=default_rel)
        # Relations.output_relations_dataframe_to_excel(df=Relations.relations_dataframe(),
        #                                               filename=filename, write_output=False)
        print("objects generated")

    @classmethod
    def setup_analysis(cls, filename, update_connection: bool = True, reset_objects: bool = False,
                       export_excel: bool = False, mode: str = "user input", assemblyMC: Assemblies = None, default_rel: float = 1):
        if reset_objects:
            Analysis.reset()
            Analysis.generate_objects(
                filename=filename, default_rel=default_rel)

        Building.connect_to_assemblies()

        Products.connect_to_assembly()
        if update_connection:
            Relations.update_connections_to_relations_objects(
                filename=filename, mode=mode, assembly=assemblyMC)
        if export_excel:
            Relations.output_relations_dataframe_to_excel(
                df=Relations.relations_dataframe(), filename=filename, write_output=True)

        Products.add_replacement_cycles()
        Products.add_total_amounts_to_product()
        Products.connect_products_to_relations()
        Products.add_eol_info()
        Relations.composite_products()
        Relations.detachment_analysis()
        Products.detachment_analysis_access_dep()
        Products.detachment_analysis()
        Products.generate_rpc()
        Products.update_years_of_replacements_based_on_detachability()
        Products.material_flow_and_replacements()
        Assemblies.generate_rpc()
        Building.generate_rpc()

    def add_a1a3_a4(mc_pick: int = 50):
        '''this will generate a1a3 and a4 impacts for each product'''
        if len(Products.instances) == 0:
            raise Exception("No products have been generated")
        if len(LCAh.instances) == 0:
            raise Exception("No LCAh instances have been generated")
        for product in Products.instances:
            # find the a1a3 activity
            a1a3_Act = LCAh.instances[0].activityLib.get(f"{product.id}")
            if a1a3_Act is None:
                logging.error(
                    f"Could not find a1a3 activity for {product.id}")
                continue
            # look up the a1a3 activity in the impact library
            impacts_a1a3_arr = LCAh.instances[0].lcaLib.get(str(a1a3_Act))
            impactsMC_a1a3 = LCAh.instances[0].mclcaLib.get(str(a1a3_Act))
            impactsMC_a1a3 = randomChoiceArray(impactsMC_a1a3, mc_pick)
            # multiply the impact by the amount of the product
            product.impacts_a1a3 = np.multiply(
                impacts_a1a3_arr, (product.total_starting_amount*(1-product.recycled_content)))
            product.impactsMC_a1a3 = np.multiply(
                impactsMC_a1a3, (product.total_starting_amount*(1-product.recycled_content)))
            # find the a4 activity
            a4_Act = LCAh.instances[0].activityLib.get(f"{product.id}_a4")
            if a4_Act is None:
                logging.error(
                    f"Could not find a4 activity for {product.id}")
                continue
            # look up the a4 activity in the impact library
            impacts_a4_arr = LCAh.instances[0].lcaLib.get(str(a4_Act))
            impactsMC_a4 = LCAh.instances[0].mclcaLib.get(str(a4_Act))
            impactsMC_a4 = randomChoiceArray(impactsMC_a4, mc_pick)
            # multiply the impact by the amount of the product
            product.impacts_a4 = np.multiply(
                impacts_a4_arr, product.total_starting_amount)
            product.impactsMC_a4 = np.multiply(
                impactsMC_a4, product.total_starting_amount)
        print("a1a3 and a4 added!")

    def add_b4(use_updated=False, mc_pick: int = 50):
        '''this will generate the b4 impacts for each product'''

        for product in Products.instances:
            # if the product has number_of_reuse = 0 and number_of_replacements = 0, and number_of_replacements_updated = 0, then skip
            if product.number_of_reuses == 0 and product.number_of_replacements == 0 and product.number_of_replacements_updated == 0:
                # set impacts b4 to 0
                product.impacts_b4 = np.zeros(
                    len(LCAh.instances[0].get_list_of_methods))
                # an array with zeros with (1,len methods,50) shape
                product.impactsMC_b4 = np.zeros(
                    (1, len(LCAh.instances[0].get_list_of_methods), mc_pick))
                # set the impacts_b4_array and impactsMC_b4_array to zeros taking into account the const MC_sim number
                product.impacts_b4_array = np.zeros(
                    (AMOUNT_MC_SIM, len(LCAh.instances[0].get_list_of_methods)))
                product.impactsMC_b4_array = np.zeros(
                    (AMOUNT_MC_SIM, len(LCAh.instances[0].get_list_of_methods),mc_pick)
)
                continue
                # use the updated replacement years if use_updated is true
            else:
                if use_updated:
                    amount = product.replaced_amount_updated
                    amount_array = product.replaced_amount_updated_array
                else:
                    amount = product.replaced_amount
                # find the material impacts activity
                material_Act = LCAh.instances[0].activityLib.get(f"{product.id}")
                if material_Act is None:
                    logging.error(
                        f"Could not find material b4 activity for {product.id}")
                    continue
                # look up the material impacts activity in the impact library
                impacts_material_arr = LCAh.instances[0].lcaLib.get(
                    str(material_Act))
                impactsMC_material = LCAh.instances[0].mclcaLib.get(
                    str(material_Act))
                impactsMC_material = randomChoiceArray(impactsMC_material, mc_pick)
                # multiply the impact by the amount of the product
                product.impacts_b4_materials = np.multiply(
                    impacts_material_arr, (amount*(1-product.recycled_content)))
                product.impactsMC_b4_materials = np.multiply(
                    impactsMC_material, amount*(1-product.recycled_content))
                
                # get the b4 impacts for the array of amount
                impacts_material_arr_reshaped = impacts_material_arr.reshape(1, -1)
                product.impacts_b4_materials_array = np.multiply(
                    impacts_material_arr_reshaped, (amount_array.reshape(-1,1)*(1-product.recycled_content)))
                product.impactsMC_b4_materials_array = np.multiply(
                    impactsMC_material, (amount_array.reshape(-1, 1, 1)*(1-product.recycled_content)))
                # find the transport impacts activity
                transport_Act = LCAh.instances[0].activityLib.get(
                    f"{product.id}_a4")
                if transport_Act is None:
                    logging.error(
                        f"Could not find transport b4 activity for {product.id}")
                    continue
                # look up the transport impacts activity in the impact library
                impacts_transport_arr = LCAh.instances[0].lcaLib.get(
                    str(transport_Act))
                impactsMC_transport = LCAh.instances[0].mclcaLib.get(
                    str(transport_Act))
                impactsMC_transport = randomChoiceArray(impactsMC_transport, mc_pick)
                # multiply the impact by the amount of the product
                product.impacts_b4_transport = np.multiply(
                    impacts_transport_arr, amount)
                product.impactsMC_b4_transport = np.multiply(
                    impactsMC_transport, amount)
                # get the b4 impacts for the array of amount
                impacts_transport_arr_reshaped = impacts_transport_arr.reshape(1,-1)
                product.impacts_b4_transport_array = np.multiply(
                    impacts_transport_arr_reshaped, amount_array.reshape(-1,1))
                product.impactsMC_b4_transport_array = np.multiply(
                    impactsMC_transport, amount_array.reshape(-1, 1, 1))
                # add the material and transport impacts
                product.impacts_b4 = np.add(
                    product.impacts_b4_materials, product.impacts_b4_transport)
                product.impactsMC_b4 = np.add(
                    product.impactsMC_b4_materials, product.impactsMC_b4_transport)
                # add the material and transport impacts for the array of amount
                product.impacts_b4_array = np.add(
                    product.impacts_b4_materials_array, product.impacts_b4_transport_array)
                product.impactsMC_b4_array = np.add(
                    product.impactsMC_b4_materials_array, product.impactsMC_b4_transport_array)
        print("B4 added!")

    def add_c2(use_updated=False, mc_pick: int = 50):
        '''this will generate the c2 impacts for each product assuming that everything is transported at the end of life'''
        # use the updated replacement years if use_updated is true
        for product in Products.instances:
            if use_updated:
                amount = product.total_amount_with_replacements_updated
                amount_array = product.total_amount_with_replacements_array_updated
            else:
                amount = product.total_amount_with_replacements
            # find the c2 activity
            c2_Act = LCAh.instances[0].activityLib.get("c2_transport")
            if c2_Act is None:
                logging.error(
                    f"Could not find c2 activity for {product.id}")
                continue
            # look up the c2 activity in the impact library
            impacts_c2_arr = LCAh.instances[0].lcaLib.get(str(c2_Act))
            impactsMC_c2 = LCAh.instances[0].mclcaLib.get(str(c2_Act))
            impactsMC_c2 = randomChoiceArray(impactsMC_c2, mc_pick)
            # multiply the impact by the amount of the product
            product.impacts_c2 = np.multiply(
                impacts_c2_arr, ((amount*product.eol_transport_distance)/1000))
            product.impactsMC_c2 = np.multiply(
                impactsMC_c2, ((amount*product.eol_transport_distance)/1000))
            # get the c2 impacts for the array of amount
            impacts_c2_arr_reshaped = impacts_c2_arr.reshape(1, -1)
            product.impacts_c2_array = np.multiply(
                impacts_c2_arr_reshaped, ((amount_array.reshape(-1,1)*product.eol_transport_distance)/1000))
            product.impactsMC_c2_array = np.multiply(
                impactsMC_c2, ((amount_array.reshape(-1,1,1)*product.eol_transport_distance)/1000))
        print("C2 added!")

    def add_c3(use_updated=False, mc_pick: int = 50):
        '''this will generate the c3 impacts for each product assuming that everything is sorted at the end of life'''
        for product in Products.instances:
            # set the biogenic content to 0
            biogenic_content = 0
            # use the updated replacement years if use_updated is true
            if use_updated:
                amount = product.total_amount_with_replacements_updated
                number_of_replacements = product.number_of_replacements_updated
                amount_array = product.total_amount_with_replacements_array_updated
            else:
                amount = product.total_amount_with_replacements
                number_of_replacements = product.number_of_replacements
            # find the c3 activity
            c3_Act = LCAh.instances[0].activityLib.get(f"{product.id}_c3")
            if c3_Act is None:
                logging.error(
                    f"Could not find c3 activity for {product.id}")
                continue
            # look up the c3 activity in the impact library
            impacts_c3_arr = LCAh.instances[0].lcaLib.get(str(c3_Act))
            impactsMC_c3 = LCAh.instances[0].mclcaLib.get(str(c3_Act))
            impactsMC_c3 = randomChoiceArray(impactsMC_c3, mc_pick)
            # multiply the impact by the amount of the product
            product.impacts_c3 = np.multiply(impacts_c3_arr, amount)
            product.impactsMC_c3 = np.multiply(impactsMC_c3, amount)
            # get the c3 impacts for the array of amount
            impacts_c3_arr_reshaped = impacts_c3_arr.reshape(1, -1)
            product.impacts_c3_array = np.multiply(
                impacts_c3_arr_reshaped, amount_array.reshape(-1,1))
            product.impactsMC_c3_array = np.multiply(
                impactsMC_c3, amount_array.reshape(-1,1,1))

            # DO THIS FOR THE ARRAY OF AMOUNT
            # DO THIS FOR THE ARRAY OF AMOUNT
            # DO THIS FOR THE ARRAY OF AMOUNT
            # DO THIS FOR THE ARRAY OF AMOUNT
            # DO THIS FOR THE ARRAY OF AMOUNT
            
            # get the biogenic content of the product at a1a3 multiplied by the number of replacements + 1 (i.e. the number of total placements)
            biogenic_content = product.impacts_a1a3[2] * \
                (number_of_replacements+1)
            biogenic_contentMC = np.multiply(
                product.impactsMC_a1a3[0][2], number_of_replacements)
            # if the product contained biogenic carbon at a1a3 then add it to the impacts
            if biogenic_content > 0:
                continue
            else:
                product.impacts_c3[1] = np.subtract(
                    product.impacts_c3[1], biogenic_content)
                product.impacts_c3[2] = np.subtract(
                    product.impacts_c3[2], biogenic_content)
                product.impactsMC_c3[0][1] = np.subtract(
                    product.impactsMC_c3[0][1], biogenic_contentMC)
                product.impactsMC_c3[0][2] = np.subtract(
                    product.impactsMC_c3[0][2], biogenic_contentMC)
        print("C3 added!")

    def add_c4(use_updated=False, mc_pick: int = 50):
        '''this will generate the c4 impacts for each product assuming that everything is landfilled at the end of life'''
        # loop through all the products
        for product in Products.instances:
            # use the updated replacement years if use_updated is true
            if use_updated:
                amount = product.total_amount_with_replacements_updated
                amount_array = product.total_amount_with_replacements_array_updated
            else:
                amount = product.total_amount_with_replacements
            # find the c4 activity
            c4_landfill_Act = LCAh.instances[0].activityLib.get(
                f"{product.id}_c4")
            c4_incineration_Act = LCAh.instances[0].activityLib.get(
                f"{product.id}_Incineration")
            if c4_landfill_Act is None:
                logging.error(
                    f"Could not find c4 activity for {product.id}")
                continue
            if c4_incineration_Act is None:
                logging.error(
                    f"Could not find c4 activity for {product.id}")
                continue
            # look up the c4 activity landfill in the impact library
            impacts_c4_arr_landfill = LCAh.instances[0].lcaLib.get(
                str(c4_landfill_Act))
            impactsMC_c4_landfill = LCAh.instances[0].mclcaLib.get(
                str(c4_landfill_Act))
            impactsMC_c4_landfill = randomChoiceArray(
                impactsMC_c4_landfill, mc_pick)
            # look up the c4 activity incineration in the impact library
            impacts_c4_arr_incineration = LCAh.instances[0].lcaLib.get(
                str(c4_incineration_Act))
            impactsMC_c4_incineration = LCAh.instances[0].mclcaLib.get(
                str(c4_incineration_Act))
            impactsMC_c4_incineration = randomChoiceArray(
                impactsMC_c4_incineration, mc_pick)
            # multiply the impact by the amount of the product and multiply by -1 to make it positive
            product.impacts_c4_landfill = np.multiply(
                impacts_c4_arr_landfill, amount * -1)
            product.impactsMC_c4_landfill = np.multiply(
                impactsMC_c4_landfill, amount * -1)
            # multiply the impact by the amount of the product and multiply by -1 to make it positive
            product.impacts_c4_incineration = np.multiply(
                impacts_c4_arr_incineration, amount * -1)
            product.impactsMC_c4_incineration = np.multiply(
                impactsMC_c4_incineration, amount * -1)
            # get the c4 impacts for the array of amount
            impacts_c4_landfill_arr_reshaped = impacts_c4_arr_landfill.reshape(1, -1)
            product.impacts_c4_array_landfill = np.multiply(
                impacts_c4_landfill_arr_reshaped, amount_array.reshape(-1,1) * -1)
            product.impactsMC_c4_array_landfill = np.multiply(
                impactsMC_c4_landfill, amount_array.reshape(-1,1,1) * -1)
            # get the incineration impacts for the array of amount
            impacts_c4_incineration_arr_reshaped = impacts_c4_arr_incineration.reshape(1, -1)
            product.impacts_c4_array_incineration = np.multiply(
                impacts_c4_incineration_arr_reshaped, amount_array.reshape(-1,1) * -1)
            product.impactsMC_c4_array_incineration = np.multiply(
                impactsMC_c4_incineration, amount_array.reshape(-1,1,1) * -1)

        print("C4 added!")

    def add_d1(use_updated: bool = False):
        '''this will generate the d1 impacts for each product assuming that everything is reused 100% at the end of life'''
        # loop through all the products
        for product in Products.instances:
            # find the d1 activity
            impacts_a1a3 = product.impacts_a1a3.copy()
            if impacts_a1a3[1] < 0:
                # fliip the sign of the impacts if they are negative if they are postive due to biogenic carbon
                impacts_a1a3[1] = impacts_a1a3[1] * -1
                impacts_a1a3[2] = impacts_a1a3[2] * -1
                product.impactsMC_c3[0][1] = product.impactsMC_c3[0][1] * -1
                product.impactsMC_c3[0][2] = product.impactsMC_c3[0][2] * -1
            # multiply the impact by -1 to make it negative
            product.impacts_d1 = np.multiply(impacts_a1a3, -1)
            product.impactsMC_d1 = np.multiply(
                product.impactsMC_a1a3, -1)
        print("D1 added!")

    def add_d2(use_updated: bool = False, mc_pick: int = 50):
        '''this will generate the d2 impacts for each product assuming that everything is recycled 100% at the end of life'''
        # loop through all the products
        for product in Products.instances:
            # use the updated replacement years if use_updated is true
            if use_updated:
                amount = product.total_amount_with_replacements_updated
                amount_array = product.total_amount_with_replacements_array_updated
            else:
                amount = product.total_amount_with_replacements
            # find the d2 activity
            d2_rep_Act = LCAh.instances[0].activityLib.get(
                f"{product.id}_d2_rep")
            if d2_rep_Act is None:
                logging.error(
                    f"Could not find d2 replacement activity for {product.id}")
                continue
            # look up the d2 replacement activity in the impact library
            impacts_d2_rep_arr = LCAh.instances[0].lcaLib.get(str(d2_rep_Act))
            impactsMC_d2_rep = LCAh.instances[0].mclcaLib.get(str(d2_rep_Act))
            impactsMC_d2_rep = randomChoiceArray(impactsMC_d2_rep, mc_pick)
            # multiply the impact by the amount of the product and multiply by -1 to make it negative
            product.impacts_d2_rep = np.multiply(
                impacts_d2_rep_arr, amount * -1)
            product.impactsMC_d2_rep = np.multiply(
                impactsMC_d2_rep, amount * -1)
            # find the d2 recycling activity
            d2_rec_Act = LCAh.instances[0].activityLib.get(
                f"{product.id}_d2_rec")
            if d2_rec_Act is None:
                logging.error(
                    f"Could not find d2 recycling activity for {product.id}")
                continue
            # look up the d2 recycling activity in the impact library
            impacts_d2_rec_arr = LCAh.instances[0].lcaLib.get(str(d2_rec_Act))
            impactsMC_d2_rec = LCAh.instances[0].mclcaLib.get(str(d2_rec_Act))
            impactsMC_d2_rec = randomChoiceArray(impactsMC_d2_rec, mc_pick)
            # multiply the impact by the amount of the product
            product.impacts_d2_rec = np.multiply(impacts_d2_rec_arr, amount)
            product.impactsMC_d2_rec = np.multiply(impactsMC_d2_rec, amount)
            # add the recycling and replacement impacts together this should produce a negative result to make sense only in very specific cases it can be positive
            impacts_total_arr = np.add(
                product.impacts_d2_rec, product.impacts_d2_rep)
            product.impactsMC_d2 = np.add(
                product.impactsMC_d2_rec, product.impactsMC_d2_rep)
            product.impacts_d2 = impacts_total_arr
            # get the d2_rec and d2_rep impacts for the array of amount
            impacts_d2_rec_arr_reshaped = impacts_d2_rec_arr.reshape(1, -1)
            impacts_d2_rep_arr_reshaped = impacts_d2_rep_arr.reshape(1, -1)
            product.impacts_d2_array = np.add(
                np.multiply(impacts_d2_rec_arr_reshaped, amount_array.reshape(-1,1)), np.multiply(impacts_d2_rep_arr_reshaped, amount_array.reshape(-1,1) * -1))
            # impactsmc
            product.impactsMC_d2_array = np.add(
                np.multiply(impactsMC_d2_rec, amount_array.reshape(-1,1,1)), np.multiply(impactsMC_d2_rep, amount_array.reshape(-1,1,1) * -1))

        print("D2 added!")

    def add_d3(use_updated: bool = False, mc_pick: int = 50):
        '''this will generate the d3 impacts for each product assuming that everything is incinerated 100% at the end of life'''
        # get d3 heat and electricity activities
        d3_heat_Act = LCAh.instances[0].activityLib.get("d3_elec")
        d3_elec_Act = LCAh.instances[0].activityLib.get("d3_heat")
        # get d3 heat and electricity impacts
        impacts_d3_heat_arr = LCAh.instances[0].lcaLib.get(str(d3_heat_Act))
        impactsMC_d3_heat = LCAh.instances[0].mclcaLib.get(str(d3_heat_Act))
        impactsMC_d3_heat = randomChoiceArray(impactsMC_d3_heat, mc_pick)
        impacts_d3_elec_arr = LCAh.instances[0].lcaLib.get(str(d3_elec_Act))
        impactsMC_d3_elec = LCAh.instances[0].mclcaLib.get(str(d3_elec_Act))
        impactsMC_d3_elec = randomChoiceArray(impactsMC_d3_elec, mc_pick)
        # loop through all the products
        for product in Products.instances:
            # use the updated replacement years if use_updated is true
            if use_updated:
                amount = product.total_amount_with_replacements_updated
                amount_array = product.total_amount_with_replacements_array_updated
            else:
                amount = product.total_amount_with_replacements
            #  multiply the heat impact by the amount of the product, the lhv, 0.2 and multiply by -1 to make it negative
            product.impacts_d3_heat = np.multiply(
                impacts_d3_heat_arr, amount * -1 * 0.2*product.lhv)
            product.impactsMC_d3_heat = np.multiply(
                impactsMC_d3_heat, amount * -1 * 0.2*product.lhv)
            # multiply the electricity impact by the amount of the product, the lhv, 0.1 and multiply by -1 to make it negative
            product.impacts_d3_elec = np.multiply(
                impacts_d3_elec_arr, amount * -1 * 0.1*product.lhv)
            product.impactsMC_d3_elec = np.multiply(
                impactsMC_d3_elec, amount * -1 * 0.1*product.lhv)
            # add the electricity and heat impacts together this should produce a negative
            impacts_total_arr = np.add(
                product.impacts_d3_elec, product.impacts_d3_heat)
            product.impactsMC_d3 = np.add(
                product.impactsMC_d3_elec, product.impactsMC_d3_heat)
            product.impacts_d3 = impacts_total_arr
            # get the d3_elec and d3_heat impacts for the array of amount
            impacts_d3_elec_arr_reshaped = impacts_d3_elec_arr.reshape(1, -1)
            impacts_d3_heat_arr_reshaped = impacts_d3_heat_arr.reshape(1, -1)
            product.impacts_d3_array = np.add(
                np.multiply(impacts_d3_elec_arr_reshaped, amount_array.reshape(-1,1) * -1 * 0.1*product.lhv), np.multiply(impacts_d3_heat_arr_reshaped, amount_array.reshape(-1,1) * -1 * 0.2*product.lhv))
            # impactsmc
            product.impactsMC_d3_array = np.add(
                np.multiply(impactsMC_d3_elec, amount_array.reshape(-1,1,1) * -1 * 0.1*product.lhv), np.multiply(impactsMC_d3_heat, amount_array.reshape(-1,1,1) * -1 * 0.2*product.lhv))
        print("D3 added!")

    def product_lca(include_circularity: bool = True):
        Analysis.add_a1a3_a4()
        Analysis.add_b4(use_updated=include_circularity)
        Analysis.add_c2(use_updated=include_circularity)
        Analysis.add_c3(use_updated=include_circularity)
        Analysis.add_c4(use_updated=include_circularity)
        Analysis.add_d1(use_updated=include_circularity)
        Analysis.add_d2(use_updated=include_circularity)
        Analysis.add_d3(use_updated=include_circularity)

    def sen_d_standard():
        '''this will simulate the D benefits assuming all products are recycled or incinerated or landfilled at the end of life'''
        '''
        This section assumes no ruse will occur and that all products will be recycled or incinerated at the end of life.
        its stored in product.impacts_d_standard'''
        if len(Products.instances) == 0:
            raise Exception("No products have been added yet")
        for product in Products.instances:
            # copy the needed impacts into a temporary variables
            recycling = None
            incineration = None
            impacts_d = None
            temp_d2 = copy.deepcopy(product.impacts_d2)
            temp_d2MC = copy.deepcopy(product.impactsMC_d2)

            # temp arrays d2
            temp_d2_arr = copy.deepcopy(product.impacts_d2_array)
            temp_d2MC_arr = copy.deepcopy(product.impactsMC_d2_array)
            # temp c4 landfill

            temp_c4_landfill = copy.deepcopy(product.impacts_c4_landfill)
            temp_c4MC_landfill = copy.deepcopy(product.impactsMC_c4_landfill)

            # temp landfill arrays
            temp_c4_landfill_arr = copy.deepcopy(
                product.impacts_c4_array_landfill)
            temp_c4MC_landfill_arr = copy.deepcopy(
                product.impactsMC_c4_array_landfill)
            # incineration
            temp_c4_incineration = copy.deepcopy(
                product.impacts_c4_incineration)
            temp_c4MC_incineration = copy.deepcopy(
                product.impactsMC_c4_incineration)
            # temp c4 arrays
            temp_c4_incineration_arr = copy.deepcopy(
                product.impacts_c4_array_incineration)
            temp_c4MC_incineration_arr = copy.deepcopy(
                product.impactsMC_c4_array_incineration)
            
            # D3
            temp_d3 = copy.deepcopy(product.impacts_d3)
            temp_d3MC = copy.deepcopy(product.impactsMC_d3)

            # temp arrays
            temp_d3_arr = copy.deepcopy(product.impacts_d3_array)
            temp_d3MC_arr = copy.deepcopy(product.impactsMC_d3_array)

            # multiply the impacts by the recycling and incineration rates plus the losses from recycling
            recycling = np.multiply(
                temp_d2, (product.recycling_r-RECYCLING_LOSS))
            recyclingMC = np.multiply(
                temp_d2MC, (product.recycling_r-RECYCLING_LOSS))
            incineration = np.multiply(temp_d3, product.incineration_r)
            incinerationMC = np.multiply(temp_d3MC, product.incineration_r)
            # add the recycling and incineration benefits together
            impacts_d = np.add(recycling, incineration)
            impacts_dMC = np.add(recyclingMC, incinerationMC)
            # assign the benefits to the product
            product.impactsMC_d_standard = impacts_dMC
            product.impacts_d_standard = impacts_d
            # add the landfilling impacts plus the losses from recycling
            impacts_landfill = np.multiply(
                temp_c4_landfill, (product.landfill_r+RECYCLING_LOSS))
            impacts_landfillMC = np.multiply(
                temp_c4MC_landfill, (product.landfill_r+RECYCLING_LOSS))
            # add the incineration impacts plus
            impacts_incineration = np.multiply(
                temp_c4_incineration, product.incineration_r)
            impacts_incinerationMC = np.multiply(
                temp_c4MC_incineration, product.incineration_r)
            # total impacts of c4
            product.impacts_c4_sen1 = np.add(
                impacts_landfill, impacts_incineration)
            product.impactsMC_c4_sen1 = np.add(
                impacts_landfillMC, impacts_incinerationMC)
            
            # do the same for the arrays
            # multiply the impacts by the recycling and incineration rates plus the losses from recycling
            recycling_arr = np.multiply(
                temp_d2_arr, (product.recycling_r-RECYCLING_LOSS))
            recyclingMC_arr = np.multiply(
                temp_d2MC_arr, (product.recycling_r-RECYCLING_LOSS))
            incineration_arr = np.multiply(temp_d3_arr, product.incineration_r)
            incinerationMC_arr = np.multiply(temp_d3MC_arr, product.incineration_r)
            # add the recycling and incineration benefits together
            impacts_d_arr = np.add(recycling_arr, incineration_arr)
            impacts_dMC_arr = np.add(recyclingMC_arr, incinerationMC_arr)
            # assign the benefits to the product
            product.impactsMC_d_standard_array = impacts_dMC_arr
            product.impacts_d_standard_array = impacts_d_arr
            # add the landfilling impacts plus the losses from recycling
            impacts_landfill_arr = np.multiply(
                temp_c4_landfill_arr, (product.landfill_r+RECYCLING_LOSS))
            impacts_landfillMC_arr = np.multiply(
                temp_c4MC_landfill_arr, (product.landfill_r+RECYCLING_LOSS))
            # add the incineration impacts plus
            impacts_incineration_arr = np.multiply(
                temp_c4_incineration_arr, product.incineration_r)
            impacts_incinerationMC_arr = np.multiply(
                temp_c4MC_incineration_arr, product.incineration_r)
            # total impacts of c4
            product.impacts_c4_sen1_array = np.add(
                impacts_landfill_arr, impacts_incineration_arr)
            product.impactsMC_c4_sen1_array = np.add(
                impacts_landfillMC_arr, impacts_incinerationMC_arr)
            
    # def sen_d_standard_plus_reuse():
    #     '''this will simulate the D benefits if no ruse occurs and all products are recycled or incinerated or landfilled at the end of life'''
    #     '''
    #     This section assumes that products that have enough tl and can be detached will be reused. But with no modification of the
    #     result i.e. no multiplication with the rpc. Its stored in product.d_standard_plus_reuse'''
    #     # STANDARD + REUSE
    #     for product in Products.instances:
    #         # Create copies of the arrays
    #         temp_d1 = copy.deepcopy(product.impacts_d1)
    #         temp_d1MC = copy.deepcopy(product.impactsMC_d1)
    #         temp_d2d3 = copy.deepcopy(product.impacts_d_standard)
    #         temp_d2d3MC = copy.deepcopy(product.impactsMC_d_standard)
    #         temp_c4 = copy.deepcopy(product.impacts_c4_sen1)
    #         temp_c4MC = copy.deepcopy(product.impactsMC_c4_sen1)

    #         # Multiply the arrays with the reuse loss
    #         temp_d1MC = np.multiply(temp_d1MC, (1-REUSE_LOSS))
    #         temp_d1 = np.multiply(temp_d1, (1-REUSE_LOSS))
    #         temp_c4 = np.multiply(temp_c4, REUSE_LOSS)
    #         temp_c4MC = np.multiply(temp_c4MC, REUSE_LOSS)
    #         temp_d2d3 = np.multiply(temp_d2d3, REUSE_LOSS)
    #         temp_d2d3MC = np.multiply(temp_d2d3MC, REUSE_LOSS)


    #         # Add the arrays together
    #         temp_d1 = np.add(temp_d1, temp_d2d3)
    #         temp_d1MC = np.add(temp_d1MC, temp_d2d3MC)

    #         # if the conditions the product can be detached and it has enough tl for another cycle then it will be reused
    #         if product.can_be_detached and yearsRemain(product, product.assembly.building.life, True) >= EOL_YEARS_REMAIN_CONST * product.assembly.building.life:
    #             product.impacts_d_standard_reuse = temp_d1
    #             product.impactsMC_d_standard_reuse = temp_d1MC
    #             product.impacts_c4_sen2 = temp_c4
    #             product.impactsMC_c4_sen2 = temp_c4MC
    #             product.route = "reuse"
    #         else:
    #             product.impacts_d_standard_reuse = product.impacts_d_standard
    #             product.impactsMC_d_standard_reuse = product.impactsMC_d_standard
    #             product.impacts_c4_sen2 = product.impacts_c4_sen1
    #             product.impactsMC_c4_sen2 = product.impactsMC_c4_sen1
    #             # add reasons for route
    #             if not product.can_be_detached and not yearsRemain(product, product.assembly.building.life, True) >= EOL_YEARS_REMAIN_CONST * product.assembly.building.life:
    #                 product.route = "downcycle_no_detaching_no_years_remain"
    #             elif not product.can_be_detached:
    #                 product.route = "downcycle_no_detaching"
    #             elif not yearsRemain(product, product.assembly.building.life, True) >= EOL_YEARS_REMAIN_CONST * product.assembly.building.life:
    #                 product.route = "downcycle_no_years_remain"

    def sen_d_standard_plus_reuse_plus_rpc():
        ''' This section is the same as the one above but with the rpc multiplication. Its stored in product.d_rpc'''
        # STANDARD + REUSE + RPC
        for product in Products.instances:
            # create a copy of the impacts
            temp_d1 = copy.deepcopy(product.impacts_d1)
            temp_d1MC = copy.deepcopy(product.impactsMC_d1)
            # create a copy of the impacts
            temp_d2d3 = copy.deepcopy(product.impacts_d_standard)
            temp_d2d3MC = copy.deepcopy(product.impactsMC_d_standard)
            # arrays
            temp_d2d3_array = copy.deepcopy(product.impacts_d_standard_array)
            temp_d2d3MC_array = copy.deepcopy(product.impactsMC_d_standard_array)
            # C4
            temp_c4 = copy.deepcopy(product.impacts_c4_sen1)
            temp_c4MC = copy.deepcopy(product.impactsMC_c4_sen1)
            # C4 arrays
            temp_c4_array = copy.deepcopy(product.impacts_c4_sen1_array)
            temp_c4MC_array = copy.deepcopy(product.impactsMC_c4_sen1_array)

            #Remove the inital material for reuse senario because it will be reuesd

            portion_not_reused = product.replaced_amount_updated/product.total_amount_with_replacements_updated
            temp_d2d3_reuse = np.multiply(temp_d2d3, portion_not_reused)
            temp_d2d3MC_reuse = np.multiply(temp_d2d3MC, portion_not_reused)
            temp_c4_not_reused = np.multiply(temp_c4, portion_not_reused)
            temp_c4MC_not_reused = np.multiply(temp_c4MC, portion_not_reused)
            # multiply the impacts with the reuse losses
            deter_temp_d1 = np.multiply(temp_d1, np.median(mc_por_impact(product)))
            # add the recycling benefits of the losses
            deter_temp_d1 = np.add(deter_temp_d1, temp_d2d3_reuse)
            # multiply the impacts with the reuse losses
            deter_temp_d1MC = np.multiply(temp_d1MC, np.median(mc_por_impact(product)))
            # add the recycling benefits of the losses
            deter_temp_d1MC = np.add(deter_temp_d1MC, temp_d2d3MC_reuse)
            # if product can be detached and has enough tl, reuse it

            # do the same but for the arrays

            temp_d1_array = np.multiply(product.impacts_d1.reshape(1,-1), mc_por_impact(product).reshape(-1,1))
            temp_d1MC_array = np.multiply(product.impactsMC_d1, mc_por_impact(product).reshape(-1,1,1))

            # make sure no zero division
            portion_not_reused_array = np.divide(product.replaced_amount_updated_array, product.total_amount_with_replacements_array_updated)
            
            temp_d2d3_array_reuse = np.multiply(temp_d2d3_array, portion_not_reused_array.reshape(-1,1))
            temp_d2d3MC_array_reuse = np.multiply(temp_d2d3MC_array, portion_not_reused_array.reshape(-1,1,1))

            temp_d1_array = np.add(temp_d1_array, temp_d2d3_array_reuse)
            temp_d1MC_array = np.add(temp_d1MC_array, temp_d2d3MC_array_reuse)

            temp_c4_not_reused_array = np.multiply(temp_c4_array, portion_not_reused_array.reshape(-1,1))
            temp_c4MC_not_reused_array = np.multiply(temp_c4MC_array, portion_not_reused_array.reshape(-1,1,1))


            if product.can_be_detached and yearsRemain(product, product.assembly.building.life, True) >= EOL_YEARS_REMAIN_CONST * product.assembly.building.life:
                product.impacts_d_rpc = deter_temp_d1
                product.impactsMC_d_rpc = deter_temp_d1MC
                product.impacts_c4_sen3 = temp_c4_not_reused
                product.impactsMC_c4_sen3 = temp_c4MC_not_reused
                product.impacts_d_rpc_array = temp_d1_array
                product.impactsMC_d_rpc_array = temp_d1MC_array
                product.impacts_c4_sen3_array = temp_c4_not_reused_array
                product.impactsMC_c4_sen3_array = temp_c4MC_not_reused_array
                product.route = "reuse"
            else:
                product.impacts_d_rpc = product.impacts_d_standard
                product.impactsMC_d_rpc = product.impactsMC_d_standard
                product.impacts_d_rpc_array = product.impacts_d_standard_array
                product.impactsMC_d_rpc_array = product.impactsMC_d_standard_array
                product.impacts_c4_sen3 = product.impacts_c4_sen1
                product.impactsMC_c4_sen3 = product.impactsMC_c4_sen1
                product.impacts_c4_sen3_array = product.impacts_c4_sen1_array
                product.impactsMC_c4_sen3_array = product.impactsMC_c4_sen1_array
                # add reasons for route
                if not product.can_be_detached and not yearsRemain(product, product.assembly.building.life, True) >= EOL_YEARS_REMAIN_CONST * product.assembly.building.life:
                    product.route = "downcycle_no_detaching_no_years_remain"
                elif not product.can_be_detached:
                    product.route = "downcycle_no_detaching"
                elif not yearsRemain(product, product.assembly.building.life, True) >= EOL_YEARS_REMAIN_CONST * product.assembly.building.life:
                    product.route = "downcycle_no_years_remain"

    def export_result_to_product_objs():
        for product in Products.instances:
            # reset values
            product.total_impact_without_d = None
            product.total_impactMC_without_d = None
            product.total_impact_with_d_standard = None
            product.total_impactMC_with_d_standard = None
            product.total_impact_with_d_standard_reuse = None
            product.total_impact_with_d_rpc = None
            product.total_impactMC_with_d_rpc = None
            product.total_impactMC_with_d_standard_reuse = None
            product.total_impact_without_d = product.impacts_a1a3 + product.impacts_a4 + \
                product.impacts_b4 + product.impacts_c2 + \
                product.impacts_c3 + product.impacts_c4_sen1
            product.total_impactMC_without_d = product.impactsMC_a1a3 + product.impactsMC_a4 + \
                product.impactsMC_b4 + product.impactsMC_c2 + \
                product.impactsMC_c3 + product.impactsMC_c4_sen1
            product.total_impact_with_d_standard = np.add(
                product.impacts_d_standard, product.total_impact_without_d)
            product.total_impactMC_with_d_standard = np.add(
                product.impactsMC_d_standard, product.total_impactMC_without_d)
            product.total_impact_with_d_standard_reuse = product.impacts_d_standard_reuse + product.impacts_a1a3 + \
                product.impacts_a4 + product.impacts_b4 + product.impacts_c2 + \
                product.impacts_c3 + product.impacts_c4_sen2
            product.total_impactMC_with_d_standard_reuse = product.impactsMC_a1a3 + product.impactsMC_a4 + product.impactsMC_b4 + \
                product.impactsMC_c2 + product.impactsMC_c3 + \
                product.impactsMC_c4_sen2 + product.impactsMC_d_standard_reuse
            product.total_impact_with_d_rpc = product.impacts_d_rpc + product.impacts_a1a3 + product.impacts_a4 + \
                product.impacts_b4 + product.impacts_c2 + \
                product.impacts_c3 + product.impacts_c4_sen3
            product.total_impactMC_with_d_rpc = product.impactsMC_d_rpc + product.impactsMC_a1a3 + product.impactsMC_a4 + \
                product.impactsMC_b4 + product.impactsMC_c2 + \
                product.impactsMC_c3 + product.impactsMC_c4_sen3
            # arrays
            product.total_impact_without_d_array = product.impacts_a1a3.reshape(1,-1) + product.impacts_a4.reshape(1,-1) + \
                product.impacts_b4_array + product.impacts_c2_array + \
                product.impacts_c3_array + product.impacts_c4_sen1_array
            product.total_impactMC_without_d_array = product.impactsMC_a1a3 + product.impactsMC_a4 + \
                product.impactsMC_b4_array + product.impactsMC_c2_array + \
                product.impactsMC_c3_array + product.impactsMC_c4_sen1_array
            product.total_impact_with_d_standard_array = product.impacts_d_standard_array + product.total_impact_without_d_array
            product.total_impactMC_with_d_standard_array = product.impactsMC_d_standard_array + product.total_impactMC_without_d_array
            # product.total_impact_with_d_standard_reuse_array = product.impacts_d_standard_reuse_array + product.impacts_a1a3.reshape(1,-1) + \
            #     product.impacts_a4.reshape(1,-1) + product.impacts_b4_array + product.impacts_c2_array + \
            #     product.impacts_c3_array + product.impacts_c4_sen2_array
            # product.total_impactMC_with_d_standard_reuse_array = product.impactsMC_a1a3.reshape(1,-1) + product.impactsMC_a4.reshape(1,-1) + product.impactsMC_b4_array + \
            #     product.impactsMC_c2_array + product.impactsMC_c3_array + \
            #     product.impactsMC_c4_sen2_array + product.impactsMC_d_standard_reuse_array
            product.total_impact_with_d_rpc_array = product.impacts_d_rpc_array + product.impacts_a1a3.reshape(1,-1) + product.impacts_a4.reshape(1,-1) + \
                product.impacts_b4_array + product.impacts_c2_array + \
                product.impacts_c3_array + product.impacts_c4_sen3_array
            product.total_impactMC_with_d_rpc_array = product.impactsMC_d_rpc_array + product.impactsMC_a1a3 + product.impactsMC_a4 + \
                product.impactsMC_b4_array + product.impactsMC_c2_array + \
                product.impactsMC_c3_array + product.impactsMC_c4_sen3_array
            
        print("Exported results to product objects")

    def export_result_to_assembly_objs():
        for assembly in Assemblies.instances:
            assembly.impacts_a1a3 = np.sum(
                [product.impacts_a1a3 for product in assembly.products], axis=0)
            assembly.impactsMC_a1a3 = np.sum(
                [product.impactsMC_a1a3 for product in assembly.products], axis=0)
            assembly.impacts_a4 = np.sum(
                [product.impacts_a4 for product in assembly.products], axis=0)
            assembly.impactsMC_a4 = np.sum(
                [product.impactsMC_a4 for product in assembly.products], axis=0)
            assembly.impacts_b4 = np.sum(
                [product.impacts_b4 for product in assembly.products], axis=0)
            assembly.impactsMC_b4 = np.sum(
                [product.impactsMC_b4 for product in assembly.products], axis=0)
            assembly.impacts_c2 = np.sum(
                [product.impacts_c2 for product in assembly.products], axis=0)
            assembly.impactsMC_c2 = np.sum(
                [product.impactsMC_c2 for product in assembly.products], axis=0)
            assembly.impacts_c3 = np.sum(
                [product.impacts_c3 for product in assembly.products], axis=0)
            assembly.impactsMC_c3 = np.sum(
                [product.impactsMC_c3 for product in assembly.products], axis=0)
            assembly.impacts_c4_sen1 = np.sum(
                [product.impacts_c4_sen1 for product in assembly.products], axis=0)
            assembly.impactsMC_c4_sen1 = np.sum(
                [product.impactsMC_c4_sen1 for product in assembly.products], axis=0)
            assembly.impacts_c4_sen2 = np.sum(
                [product.impacts_c4_sen2 for product in assembly.products], axis=0)
            assembly.impactsMC_c4_sen2 = np.sum(
                [product.impactsMC_c4_sen2 for product in assembly.products], axis=0)
            assembly.impacts_c4_sen3 = np.sum(
                [product.impacts_c4_sen3 for product in assembly.products], axis=0)
            assembly.impactsMC_c4_sen3 = np.sum(
                [product.impactsMC_c4_sen3 for product in assembly.products], axis=0)
            assembly.impacts_d_standard = np.sum(
                [product.impacts_d_standard for product in assembly.products], axis=0)
            assembly.impactsMC_d_standard = np.sum(
                [product.impactsMC_d_standard for product in assembly.products], axis=0)
            assembly.impacts_d_standard_reuse = np.sum(
                [product.impacts_d_standard_reuse for product in assembly.products], axis=0)
            assembly.impactsMC_d_standard_reuse = np.sum(
                [product.impactsMC_d_standard_reuse for product in assembly.products], axis=0)
            assembly.impacts_d_rpc = np.sum(
                [product.impacts_d_rpc for product in assembly.products], axis=0)
            assembly.impactsMC_d_rpc = np.sum(
                [product.impactsMC_d_rpc for product in assembly.products], axis=0)
            assembly.total_impact_without_d = np.sum(
                [product.total_impact_without_d for product in assembly.products], axis=0)
            assembly.total_impactMC_without_d = np.sum(
                [product.total_impactMC_without_d for product in assembly.products], axis=0)
            assembly.total_impact_with_d_standard = np.sum(
                [product.total_impact_with_d_standard for product in assembly.products], axis=0)
            assembly.total_impactMC_with_d_standard = np.sum(
                [product.total_impactMC_with_d_standard for product in assembly.products], axis=0)
            assembly.total_impact_with_d_standard_reuse = np.sum(
                [product.total_impact_with_d_standard_reuse for product in assembly.products], axis=0)
            assembly.total_impactMC_with_d_standard_reuse = np.sum(
                [product.total_impactMC_with_d_standard_reuse for product in assembly.products], axis=0)
            assembly.total_impact_with_d_rpc = np.sum(
                [product.total_impact_with_d_rpc for product in assembly.products], axis=0)
            assembly.total_impactMC_with_d_rpc = np.sum(
                [product.total_impactMC_with_d_rpc for product in assembly.products], axis=0)
            # arrays
            assembly.impacts_b4_array = np.sum(
                [product.impacts_b4_array for product in assembly.products], axis=0)
            assembly.impactsMC_b4_array = np.sum(
                [product.impactsMC_b4_array for product in assembly.products], axis=0)
            assembly.impacts_c2_array = np.sum(
                [product.impacts_c2_array for product in assembly.products], axis=0)
            assembly.impactsMC_c2_array = np.sum(
                [product.impactsMC_c2_array for product in assembly.products], axis=0)
            assembly.impacts_c3_array = np.sum(
                [product.impacts_c3_array for product in assembly.products], axis=0)
            assembly.impactsMC_c3_array = np.sum(
                [product.impactsMC_c3_array for product in assembly.products], axis=0)
            assembly.impacts_c4_sen1_array = np.sum(
                [product.impacts_c4_sen1_array for product in assembly.products], axis=0)
            assembly.impactsMC_c4_sen1_array = np.sum(
                [product.impactsMC_c4_sen1_array for product in assembly.products], axis=0)
            # assembly.impacts_c4_sen2_array = np.sum(
            #     [product.impacts_c4_sen2_array for product in assembly.products], axis=0)
            # assembly.impactsMC_c4_sen2_array = np.sum(
            #     [product.impactsMC_c4_sen2_array for product in assembly.products], axis=0)
            assembly.impacts_c4_sen3_array = np.sum(
                [product.impacts_c4_sen3_array for product in assembly.products], axis=0)
            assembly.impactsMC_c4_sen3_array = np.sum(
                [product.impactsMC_c4_sen3_array for product in assembly.products], axis=0)
            assembly.impacts_d_standard_array = np.sum(
                [product.impacts_d_standard_array for product in assembly.products], axis=0)
            assembly.impactsMC_d_standard_array = np.sum(
                [product.impactsMC_d_standard_array for product in assembly.products], axis=0)
            # assembly.impacts_d_standard_reuse_array = np.sum(
            #     [product.impacts_d_standard_reuse_array for product in assembly.products], axis=0)
            # assembly.impactsMC_d_standard_reuse_array = np.sum(
            #     [product.impactsMC_d_standard_reuse_array for product in assembly.products], axis=0)
            assembly.impacts_d_rpc_array = np.sum(
                [product.impacts_d_rpc_array for product in assembly.products], axis=0)
            assembly.impactsMC_d_rpc_array = np.sum(
                [product.impactsMC_d_rpc_array for product in assembly.products], axis=0)
            assembly.total_impact_without_d_array = np.sum(
                [product.total_impact_without_d_array for product in assembly.products], axis=0)
            assembly.total_impactMC_without_d_array = np.sum(
                [product.total_impactMC_without_d_array for product in assembly.products], axis=0)
            assembly.total_impact_with_d_standard_array = np.sum(
                [product.total_impact_with_d_standard_array for product in assembly.products], axis=0)
            assembly.total_impactMC_with_d_standard_array = np.sum(
                [product.total_impactMC_with_d_standard_array for product in assembly.products], axis=0)
            # assembly.total_impact_with_d_standard_reuse_array = np.sum(
            #     [product.total_impact_with_d_standard_reuse_array for product in assembly.products], axis=0)
            # assembly.total_impactMC_with_d_standard_reuse_array = np.sum(
            #     [product.total_impactMC_with_d_standard_reuse_array for product in assembly.products], axis=0)
            assembly.total_impact_with_d_rpc_array = np.sum(
                [product.total_impact_with_d_rpc_array for product in assembly.products], axis=0)
            assembly.total_impactMC_with_d_rpc_array = np.sum(
                [product.total_impactMC_with_d_rpc_array for product in assembly.products], axis=0)
            
        print("Exported results to assembly objects")

    def export_result_to_building_objs(building: Building):
        building.impacts_a1a3 = np.sum(
            [assembly.impacts_a1a3 for assembly in building.assemblies], axis=0)
        building.impactsMC_a1a3 = np.sum(
            [assembly.impactsMC_a1a3 for assembly in building.assemblies], axis=0)
        building.impacts_a4 = np.sum(
            [assembly.impacts_a4 for assembly in building.assemblies], axis=0)
        building.impactsMC_a4 = np.sum(
            [assembly.impactsMC_a4 for assembly in building.assemblies], axis=0)
        building.impacts_b4 = np.sum(
            [assembly.impacts_b4 for assembly in building.assemblies], axis=0)
        building.impactsMC_b4 = np.sum(
            [assembly.impactsMC_b4 for assembly in building.assemblies], axis=0)
        building.impacts_c2 = np.sum(
            [assembly.impacts_c2 for assembly in building.assemblies], axis=0)
        building.impactsMC_c2 = np.sum(
            [assembly.impactsMC_c2 for assembly in building.assemblies], axis=0)
        building.impacts_c3 = np.sum(
            [assembly.impacts_c3 for assembly in building.assemblies], axis=0)
        building.impactsMC_c3 = np.sum(
            [assembly.impactsMC_c3 for assembly in building.assemblies], axis=0)
        building.impacts_c4_sen1 = np.sum(
            [assembly.impacts_c4_sen1 for assembly in building.assemblies], axis=0)
        building.impactsMC_c4_sen1 = np.sum(
            [assembly.impactsMC_c4_sen1 for assembly in building.assemblies], axis=0)
        building.impacts_c4_sen2 = np.sum(
            [assembly.impacts_c4_sen2 for assembly in building.assemblies], axis=0)
        building.impactsMC_c4_sen2 = np.sum(
            [assembly.impactsMC_c4_sen2 for assembly in building.assemblies], axis=0)
        building.impacts_c4_sen3 = np.sum(
            [assembly.impacts_c4_sen3 for assembly in building.assemblies], axis=0)
        building.impactsMC_c4_sen3 = np.sum(
            [assembly.impactsMC_c4_sen3 for assembly in building.assemblies], axis=0)
        building.impacts_d_standard = np.sum(
            [assembly.impacts_d_standard for assembly in building.assemblies], axis=0)
        building.impactsMC_d_standard = np.sum(
            [assembly.impactsMC_d_standard for assembly in building.assemblies], axis=0)
        building.impacts_d_standard_reuse = np.sum(
            [assembly.impacts_d_standard_reuse for assembly in building.assemblies], axis=0)
        building.impactsMC_d_standard_reuse = np.sum(
            [assembly.impactsMC_d_standard_reuse for assembly in building.assemblies], axis=0)
        building.impacts_d_rpc = np.sum(
            [assembly.impacts_d_rpc for assembly in building.assemblies], axis=0)
        building.impactsMC_d_rpc = np.sum(
            [assembly.impactsMC_d_rpc for assembly in building.assemblies], axis=0)
        building.total_impact_without_d = np.sum(
            [assembly.total_impact_without_d for assembly in building.assemblies], axis=0)
        building.total_impactMC_without_d = np.sum(
            [assembly.total_impactMC_without_d for assembly in building.assemblies], axis=0)
        building.total_impact_with_d_standard = np.sum(
            [assembly.total_impact_with_d_standard for assembly in building.assemblies], axis=0)
        building.total_impactMC_with_d_standard = np.sum(
            [assembly.total_impactMC_with_d_standard for assembly in building.assemblies], axis=0)
        building.total_impact_with_d_standard_reuse = np.sum(
            [assembly.total_impact_with_d_standard_reuse for assembly in building.assemblies], axis=0)
        building.total_impactMC_with_d_standard_reuse = np.sum(
            [assembly.total_impactMC_with_d_standard_reuse for assembly in building.assemblies], axis=0)
        building.total_impact_with_d_rpc = np.sum(
            [assembly.total_impact_with_d_rpc for assembly in building.assemblies], axis=0)
        building.total_impactMC_with_d_rpc = np.sum(
            [assembly.total_impactMC_with_d_rpc for assembly in building.assemblies], axis=0)
        
        # ARRAYS
        building.impacts_b4_array = np.sum(
            [assembly.impacts_b4_array for assembly in building.assemblies], axis=0)
        building.impactsMC_b4_array = np.sum(
            [assembly.impactsMC_b4_array for assembly in building.assemblies], axis=0)
        building.impacts_c2_array = np.sum(
            [assembly.impacts_c2_array for assembly in building.assemblies], axis=0)
        building.impactsMC_c2_array = np.sum(
            [assembly.impactsMC_c2_array for assembly in building.assemblies], axis=0)
        building.impacts_c3_array = np.sum(
            [assembly.impacts_c3_array for assembly in building.assemblies], axis=0)
        building.impactsMC_c3_array = np.sum(
            [assembly.impactsMC_c3_array for assembly in building.assemblies], axis=0)
        building.impacts_c4_sen1_array = np.sum(
            [assembly.impacts_c4_sen1_array for assembly in building.assemblies], axis=0)
        building.impactsMC_c4_sen1_array = np.sum(
            [assembly.impactsMC_c4_sen1_array for assembly in building.assemblies], axis=0)
        # building.impacts_c4_sen2_array = np.sum(
        #     [assembly.impacts_c4_sen2_array for assembly in building.assemblies], axis=0)
        # building.impactsMC_c4_sen2_array = np.sum(
        #     [assembly.impactsMC_c4_sen2_array for assembly in building.assemblies], axis=0)
        building.impacts_c4_sen3_array = np.sum(
            [assembly.impacts_c4_sen3_array for assembly in building.assemblies], axis=0)
        building.impactsMC_c4_sen3_array = np.sum(
            [assembly.impactsMC_c4_sen3_array for assembly in building.assemblies], axis=0)
        building.impacts_d_standard_array = np.sum(
            [assembly.impacts_d_standard_array for assembly in building.assemblies], axis=0)
        building.impactsMC_d_standard_array = np.sum(
            [assembly.impactsMC_d_standard_array for assembly in building.assemblies], axis=0)
        # building.impacts_d_standard_reuse_array = np.sum(
        #     [assembly.impacts_d_standard_reuse_array for assembly in building.assemblies], axis=0)
        # building.impactsMC_d_standard_reuse_array = np.sum(
        #     [assembly.impactsMC_d_standard_reuse_array for assembly in building.assemblies], axis=0)
        building.impacts_d_rpc_array = np.sum(
            [assembly.impacts_d_rpc_array for assembly in building.assemblies], axis=0)
        building.impactsMC_d_rpc_array = np.sum(
            [assembly.impactsMC_d_rpc_array for assembly in building.assemblies], axis=0)
        building.total_impact_without_d_array = np.sum(
            [assembly.total_impact_without_d_array for assembly in building.assemblies], axis=0)
        building.total_impactMC_without_d_array = np.sum(
            [assembly.total_impactMC_without_d_array for assembly in building.assemblies], axis=0)
        building.total_impact_with_d_standard_array = np.sum(
            [assembly.total_impact_with_d_standard_array for assembly in building.assemblies], axis=0)
        building.total_impactMC_with_d_standard_array = np.sum(
            [assembly.total_impactMC_with_d_standard_array for assembly in building.assemblies], axis=0)
        # building.total_impact_with_d_standard_reuse_array = np.sum(
        #     [assembly.total_impact_with_d_standard_reuse_array for assembly in building.assemblies], axis=0)
        # building.total_impactMC_with_d_standard_reuse_array = np.sum(
        #     [assembly.total_impactMC_with_d_standard_reuse_array for assembly in building.assemblies], axis=0)
        building.total_impact_with_d_rpc_array = np.sum(
            [assembly.total_impact_with_d_rpc_array for assembly in building.assemblies], axis=0)
        building.total_impactMC_with_d_rpc_array = np.sum(
            [assembly.total_impactMC_with_d_rpc_array for assembly in building.assemblies], axis=0)

        print("Exported results to building objects")

    def generate_scenarios():
        Analysis.sen_d_standard()
        Analysis.sen_d_standard_plus_reuse()
        Analysis.sen_d_standard_plus_reuse_plus_rpc()

    def generate_results(building: Building, assembly_results: bool = True, building_results: bool = True):
        Analysis.export_result_to_product_objs()
        if assembly_results:
            Analysis.export_result_to_assembly_objs()
        if building_results:
            Analysis.export_result_to_assembly_objs()
            Analysis.export_result_to_building_objs(building)
    def clean_up():
        pass

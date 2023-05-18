import networkx as nx
import numpy as np
from copy import deepcopy
import random


def remove_duplicates(my_list):
    no_duplicates = set()
    return [x for x in my_list if not (x in no_duplicates or no_duplicates.add(x))]


def networkx_path_list(data: nx.DiGraph, node: str = "") -> list:
    '''this will return a list of nodes that are downstream of a given node'''
    path = list(reversed(remove_duplicates(
        sum(list(nx.algorithms.bfs_tree(data, node).edges()), ()))))
    # remove the node itself from the list
    if len(path) > 1:
        path.remove(node)
    return path


def yearsRemain(product, year, use_updated: bool = False) -> int:
    '''This function will return the amount of years remaining for a product based on the year of replacement'''
    if use_updated:
        y = list(product.years_of_replacements_updated)
    else:
        y = list(product.years_of_replacements)
    if len(y) == 0:
        return product.technical_life - year
    else:
        y.append(year)
        y_sorted = sorted(y)
        for i, x in enumerate(y_sorted):
            if x == year:
                var = y_sorted[i-1]
        return var - year + product.technical_life


def randomChoiceArray(array: np.array, pick:int = 50):
    '''This function will return a random choice from a given array
    the default picks 50 change if needed'''
    copied = np.array(array)
    choice = copied[:, :, np.random.choice(copied.shape[2], pick, replace=False)]
    return choice



'''[ 1.09186399  0.44315069  7.58473472 -0.07522362]
[ 1.00000000e+00  8.07452500e-01  1.86017358e+02 -2.62179169e-12]
[ 1.00000049e+00  3.54228982e-01  5.72162691e+01 -4.81510058e-07]
[90.9335388  11.56324294  0.27240267 -3.82067998]
[ 1.00151956e+00  7.27966159e-01  2.39443872e+01 -3.65332847e-05]
[ 1.23640816  0.59668638  5.12167984 -0.07709897]'''

def sigmoid(x, a=1.0690464139392881, b=0.5333961150019655, c=-7.57209212334568, d=-0.030342853955192227):
    y = a / (1 + np.exp(-c*(x-b))) + d
    return y


def mc_por(product, num_simulations=100):
    results = []
    sigmoid_prob = 1 - sigmoid(product.rpc)
    for _ in range(num_simulations):
        rand_num = random.random()
        if rand_num < sigmoid_prob:
            results.append(0)  # Reused
        else:
            results.append(1)  # Not reused
            
    return np.array(results)


def mc_por_impact(product, num_simulations=100):
    results = []
    sigmoid_prob = 1 - sigmoid(product.rpc)
    for _ in range(num_simulations):
        rand_num = random.random()
        if rand_num < sigmoid_prob:
            results.append(1)  # Reused
        else:
            results.append(0)  # Not reused
            
    return np.array(results)
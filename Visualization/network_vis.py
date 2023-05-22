import networkx as nx
import matplotlib.pyplot as plt
from brwy4build.Objects.objects import Products, Relations, Building, Assemblies


def plot_DNS(data: nx.DiGraph | nx.Graph = Products.generateDirectedGraph(), size: tuple =(20, 20), save: bool = False, save_path: str = None):
    '''plot a simple networkx graph'''
    options = {"with_labels": True,
               "node_color": "white", "edgecolors": "blue", "node_size": 50, "font_size": 8}
    fig = plt.figure(figsize=size)
    axgrid = fig.add_gridspec(1, 1)
    ax1 = fig.add_subplot(axgrid[0, 0])
    ax1.set_title("Connections")
    pos = nx.layout.fruchterman_reingold_layout(data)
    # pos = nx.spring_layout(data, seed=31134652)
    nx.draw_networkx(data, pos, **options)
    plt.show()
    # save a 600 dpi image
    if save:
        fig.savefig(save_path, dpi=1000)

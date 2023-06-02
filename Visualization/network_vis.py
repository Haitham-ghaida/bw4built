import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
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



def DNSA_with_pyvis(products: list[Products], ep_color:str= "#add8e6", ms_color:str="#ffa500", edge_color:str="#018786", buttons:bool=True):
    g = Network(notebook=True, height="1000px", width="100%", bgcolor="#FFFFFF", font_color="black", cdn_resources='in_line', directed=True, filter_menu=True, )
    g.toggle_physics(False)
    if buttons:
        g.width = "100%"
        g.show_buttons()
    
    # create a dict for the groups
    for product in Products.instances:
        node_color = ms_color if product.base else ep_color
        g.add_node(n_id=product.id, label=product.id, color=node_color,
         title=f"my name is {product.name} \n my GWP impact is {product.total_impact_without_d[1]}")
    
    for relation in Relations.instances:
        edge_color = 'red' if not relation.can_be_detached else "green"
        arrows_param = {'to': {'enabled': True, 'type': 'bar' if not relation.is_connection else 'arrow'}}
        g.add_edge(source=relation.product1, to=relation.product2, color=edge_color, value=relation.rpc*10, title=f"my connection type rating is {relation.ct} \n my access rating is {relation.ca} \n my form containment rating is {relation.fc}, my crossings rating is {relation.cr} \n I am a structural dependency {relation.is_connection}", arrows=arrows_param)
    
    g.show("DNSA.html")


import matplotlib.pyplot as plt
import brightway2 as bw
from brwy4build.Objects.objects import LCAh
import plotly.graph_objects as go
import numpy as np


def uncertainty_box_plot(array):
    ''''
    creates a box plot of the building level uncertainty for the different impact categories'''
    # determine the which array to plot
    # create the plot of size 4x5
    fig, axes = plt.subplots(4, 5, figsize=(20, 10))
    # adjust the spacing between the plots
    plt.subplots_adjust(bottom=0.048, left=0.048, right=0.957,
                        top=0.957, wspace=0.4, hspace=0.3)
    # remove the last empty plot
    fig.delaxes(axes[3, 4])
    # create the plot
    axes = axes.ravel()
    # loop over the different impact categories
    for i, values in enumerate([method for method in LCAh.instances[0].get_list_of_methods]):
        # plot the box plot
        axes[i].boxplot(array[0, i, :])
        # set the title which is the impact category
        axes[i].set_title(f"{values[1].title()}")
        axes[i].set_xticklabels([])  # remove x-labels
        # set the y-label as the unit of the impact category
        axes[i].set_ylabel(bw.Method(values).metadata["unit"])
    # Show the plot
    plt.show()

def multi_uncertainty_box_plot(List_of_arrays: list):
    '''similiar to the uncertainty_box_plot but for multiple arrays where each array will be on an x axis'''
    # create the plot of size 4x5
    fig, axes = plt.subplots(4, 5, figsize=(20, 10))
    # adjust the spacing between the plots
    plt.subplots_adjust(bottom=0.048, left=0.048, right=0.957,
                        top=0.957, wspace=0.4, hspace=0.3)
    # remove the last empty plot
    fig.delaxes(axes[3, 4])
    # create the plot
    axes = axes.ravel()
    # loop over the different impact categories
    for i, values in enumerate([method for method in LCAh.instances[0].get_list_of_methods]):
        # loop over the different arrays
        for array in List_of_arrays:
            # plot the box plot
            axes[i].boxplot(array[0, i, :])
            # set the title which is the impact category
            axes[i].set_title(f"{values[1].title()}")
            axes[i].set_xticklabels([])
            # set the y-label as the unit of the impact category
            axes[i].set_ylabel(bw.Method(values).metadata["unit"])
    # Show the plot
    plt.show()



def plot_all_arrays(arrays, index, fix_labels=True):
    # Separate the array names and the arrays themselves
    labels = list(arrays.keys())
    # Select the subset of each array using the index
    data = [arr[:, index, :].flatten() for arr in arrays.values()]
    print(labels)
    if fix_labels:
        labels = [label.split('_')[0] for label in labels]
    plt.boxplot(data, labels=labels)
    plt.grid(True)
    plt.show()


def plot_all_arrays2(arrays, index):

    # Separate the array names and the arrays themselves
    labels = list(arrays.keys())
    # Select the subset of each array using the index and flatten it to 1D
    data = [arr[:, index, :].flatten() for arr in arrays.values()]

    # Split the labels at '_' and keep only the first part
    labels = [label.split('_')[0] for label in labels]

    # Create a figure
    fig = go.Figure()

    # Add a box trace for each array
    for label, arr in zip(labels, data):
        fig.add_trace(go.Box(y=arr, name=label))

    # Show the figure
    fig.show()


def plot_all_arrays3(arrays, index):
    # Separate the array names and the arrays themselves
    labels = list(arrays.keys())
    # Select the subset of each array using the index and flatten it to 1D
    data = [arr[:, index, :].flatten() for arr in arrays.values()]

    # Split the labels at '_' and keep only the first part
    labels = [label.split('_')[0] for label in labels]

    # Create a figure
    fig = go.Figure()

    # Add a box trace for each array
    for label, arr in zip(labels, data):
        fig.add_trace(go.Box(y=arr, name=label))

    # Show the figure
    fig.show(config={
        'editable': True, 
        'edits': {
            'legendText': True,
            'titleText': True,
            'axisTitleText': True,
            'tickText': True,
        }
    })

def plot_all_arrays4(arrays, index):

    # Separate the array names and the arrays themselves
    labels = list(arrays.keys())
    # Select the subset of each array using the index and flatten it to 1D
    data = [arr[:, index, :].flatten() for arr in arrays.values()]

    # Split the labels at '_' and keep only the first part
    labels = [label.split('_')[0] for label in labels]

    # Create a figure
    fig = go.Figure()

    # Add a box trace for each array to show outliers
    # for label, arr in zip(labels, data):
    #     fig.add_trace(go.Box(y=arr, name=label, marker_color='rgba(0,0,0,0)', line_color='rgba(0,0,0,0)'))

    # Add a bar trace for each array to show mean and standard deviation
    for label, arr in zip(labels, data):
        fig.add_trace(go.Bar(
            y=[np.mean(arr)],
            name=label,
            error_y=dict(type='data', array=[np.std(arr)], visible=True)
        ))

    # Show the figure
    fig.show(config={
        'editable': True, 
        'edits': {
            'legendText': True,
            'titleText': True,
            'axisTitleText': True,
            'tickText': True
        }
    })
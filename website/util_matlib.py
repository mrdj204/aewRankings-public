"""
util_matlib.py

This module provides utility functions for creating graphs using the Matplotlib library.

Functions:
- api_mmr_graphs(division: Division, mmr_type: str, division_key: str, stat_key: str, include_winless: bool) -> List[str]:
    Retrieves multiple Matchmaking Rating (MMR) graphs for a given division.

- api_graphs(division: Division, division_key: str, stat_key: str, include_winless: bool) -> List[str]:
    Retrieves multiple generic statistics graphs for a given division.
"""
import base64
from io import BytesIO
from typing import Union

from matplotlib import pyplot as plt

from mmr_database.division import Division


def api_mmr_graphs(division: Division, mmr_type, division_key, stat_key, include_winless: bool) -> list[str]:
    """
    Retrieves multiple Matchmaking Rating (MMR) graphs for a given division.

    Args:
        division (Division): The division object.
        mmr_type (str): The MMR version, e.g. 'mmr' or 'mmr_noreset'.
        division_key (str): The division key.
        stat_key (str): The stat key.
        include_winless (bool): Flag to include wrestlers with no wins.

    Returns:
        List[str]: A list of HTML image strings representing the MMR graphs.
    """
    return [
        _mmrs("boxplot", division, "alltime", mmr_type, division_key, stat_key, include_winless),
        *_mmrs_allyears("boxplot", division, mmr_type, division_key, stat_key, include_winless),
    ]


def api_graphs(division, division_key, stat_key, include_winless) -> list[str]:
    """
    Retrieves multiple generic statistics graphs for a given division.

    Args:
        division (Division): The division object.
        division_key (str): The division key.
        stat_key (str): The stat key.
        include_winless (bool): Flag to include wrestlers with no wins.

    Returns:
        List[str]: A list of HTML image strings representing the generic statistics graphs.
    """
    return [
        _generic("boxplot", division, "alltime", division_key, stat_key, include_winless),
        *_generic_allyears("boxplot", division, division_key, stat_key, include_winless),
    ]


def _histogram_create_image_html(data: list[list[float]], size: tuple[float, float], title: str) -> str:
    """
    Creates an HTML image tag for a histogram graph.

    Args:
        data (list[list[float]]): The data for the histogram.
        size (tuple[float, float]): The size of the graph.
        title (str): The title of the graph.

    Returns:
        str: The HTML image tag.
    """
    colors = ['#2196f3', '#e0e0e0', '#ffffff', '#c5cae9', '#f44336',
              '#4caf50', '#9c27b0', '#ff5722', '#ffc107', '#607d8b']
    bins = 142
    fig, ax = plt.subplots(figsize=size)
    ax.hist(data, bins=bins, color=colors[:len(data)])
    ax.set_facecolor('#1e1e1e')  # set the background color
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    buffer = BytesIO()
    fig.suptitle(title, fontsize=14, color="white")
    fig.patch.set_alpha(0)  # set the background color to fully transparent
    fig.savefig(buffer, format='png', bbox_inches='tight')
    plt.close(fig)

    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f'<img src="data:image/png;base64,{image_base64}" />'


def _boxplot_create_image_html(data: Union[list[float], list[list[float]]], label: list, title: str) -> str:
    """
    Creates an HTML image tag for a boxplot graph.

    Args:
        data (Union[list[float], list[list[float]]]): The data for the boxplot.
        label (list): The label for the graph.
        title (str): The title of the graph.

    Returns:
        str: A str containing the HTML image tags for the thumbnail and full-size graph.
    """
    thumbnail_size = (6.5, 2)
    full_size = (21, 6)
    thumb_base64 = _get_image(thumbnail_size, data, label, title)
    full_base64 = _get_image(full_size, data, label, title)
    return f'<img class="graph_image" src="data:image/png;base64,{thumb_base64}" ' \
           f'data-fullsize="data:image/png;base64,{full_base64}" />'


def _get_image(size, data, label, title) -> str:
    """
    Creates an image file from the given data.

    Args:
        size: The size of the image.
        data: The data for the graph.
        label: The label for the graph.
        title: The title of the graph.

    Returns:
        str: The base64-encoded image data.
    """
    main_color = '#2196f3'
    grid_color = '#e0e0e0'
    outline_color = '#ffffff'
    median_color = '#c5cae9'
    outlier_color = '#2196f3'
    bg_color = '#1e1e1e'

    fig, ax = plt.subplots(figsize=size)
    ax.boxplot(data, boxprops=dict(linewidth=2, color=main_color),
               whiskerprops=dict(linewidth=2, color=outline_color),
               capprops=dict(linewidth=2, color=outline_color),
               medianprops=dict(linewidth=2, color=median_color),
               flierprops=dict(marker='o', markersize=6, markerfacecolor=outlier_color, markeredgecolor=outlier_color),
               patch_artist=True, vert=False)
    ax.set_facecolor(bg_color)  # set the background color
    ax.grid(axis='y', color=grid_color)
    ax.set_yticklabels(label)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    buffer = BytesIO()
    fig.suptitle(title, fontsize=14, color="white")
    fig.patch.set_alpha(0)  # set the background color to fully transparent
    fig.savefig(buffer, format='png', bbox_inches='tight')
    plt.close(fig)

    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def _get_graph(graph_type: str, data: Union[list[float], list[list[float]]], title: str,
               labels: list[Union[str, float]], size: tuple[float, float] = (21, 6)) -> str:
    """
    Retrieves a graph based on the graph type.

    Args:
        graph_type (str): The type of graph.
        data (Union[list[float], list[list[float]]]): The data for the graph.
        title (str): The title of the graph.
        labels (list[Union[str, float]]): The labels for the graph.
        size (tuple[float, float], optional): The size of the graph. Defaults to (21, 6).

    Returns:
        str: A str containing the HTML image tags for the thumbnail and full-size graph.
    """
    if graph_type == "histogram":
        if isinstance(data[0], float):
            data = [data]
        return _histogram_create_image_html([data], size, title)
    elif graph_type == "boxplot":
        return _boxplot_create_image_html(data, labels, title)


def _get_graph_multi(name: str, graph_type: str, single_image: bool, division: Division,
                     data: dict[str, list[float]]) -> list[str]:
    """
    Retrieves multiple graphs based on the graph type and data.

    Args:
        name (str): The name of the graph.
        graph_type (str): The type of graph.
        single_image (bool): Flag to indicate if a single image is required.
        division (Division): The division object.
        data (dict[str, list[float]]): The data for the graphs.

    Returns:
        list[str]: A list of strings containing the HTML image tags for the graphs.
    """
    size = (6.5, 2)
    images = []
    if single_image:
        labels = [f"{year} ({len(total_wins)})" for year, total_wins in data.items()]
        title = f'({division.name}) {name}'
        new_data = [v for v in data.values()]
        return [_get_graph(graph_type, new_data, title, labels, size)]
    else:
        keys = reversed([k for k in data.keys()])
        values = reversed([v for v in data.values()])
        data = {k: v for k, v in zip(keys, values)}
        for year, data_values in data.items():
            new_data = [data_values]
            label = [year] if graph_type == "boxplot" else ""
            title = f'({division.name}) ({year}) {name} ({len(data_values)})'
            images.append(_get_graph(graph_type, new_data, title, label, size))
        return images


def _mmrs_allyears(graph_type: str, division: Division, mmr_type: str, division_key: str,
                   stat_key: str, include_winless: bool) -> list[str]:
    """
    Retrieves multiple MMR graphs for all years in a division.

    Args:
        graph_type (str): The type of graph.
        division (Division): The division object.
        mmr_type (str): The type of MMR.
        division_key (str): The division key.
        stat_key (str): The stat key.
        include_winless (bool): Flag to include winless data.

    Returns:
        list[str]: A list of strings containing the HTML image tags for the MMR graphs.
    """
    mmr_key = f"{division_key}_{mmr_type}"
    data: dict[str, list[float]] = division.api_graphs_mmrs_allyears(division_key, stat_key, mmr_key, include_winless)
    title = f"({mmr_key}) ({stat_key})"
    graphs = _get_graph_multi(title, graph_type, True, division, data)
    graphs += _get_graph_multi(title, graph_type, False, division, data)
    return graphs


def _mmrs(graph_type: str, division: Division, year: Union[int, str], mmr_type: str,
          division_key: str, stat_key: str, include_winless: bool) -> str:
    """
    Retrieves an MMR graph for a specific year in a division.

    Args:
        graph_type (str): The type of graph.
        division (Division): The division object.
        year (Union[int, str]): The year for the graph.
        mmr_type (str): The type of MMR.
        division_key (str): The division key.
        stat_key (str): The stat key.
        include_winless (bool): Flag to include winless data.

    Returns:
        str: A str containing the HTML image tags for the MMR graph.
    """
    mmr_key = f"{division_key}_{mmr_type}"
    data: list[float] = division.api_graphs_mmrs(year, division_key, stat_key, mmr_key, include_winless)
    label = [year] if graph_type == "boxplot" else ""
    title = f'({division.name}) ({year}) ({mmr_key}) ({stat_key}) ({len(data)})'
    return _get_graph(graph_type, data, title, label)


def _generic_allyears(graph_type: str, division: Division, division_key: str, stat_key: str = "wins",
                      include_winless: bool = False) -> list[str]:
    """
    Retrieves multiple generic graphs for all years in a division.

    Args:
        graph_type (str): The type of graph.
        division (Division): The division object.
        division_key (str): The division key.
        stat_key (str, optional): The stat key. Defaults to "wins".
        include_winless (bool, optional): Flag to include winless data. Defaults to False.

    Returns:
        list[str]: A list of strings representing the generic graphs.
    """
    data: dict[str, list[float]] = division.api_graphs_generic_allyears(division_key, stat_key, include_winless)
    title = f"({stat_key.capitalize()}) ({division_key.capitalize()})"
    graphs = _get_graph_multi(title, graph_type, True, division, data)
    graphs += _get_graph_multi(title, graph_type, False, division, data)
    return graphs


def _generic(graph_type: str, division: Division, year: Union[str, float], division_key: str,
             stat_key: str = "wins", include_winless: bool = False) -> str:
    """
    Retrieves a generic graph for a specific year in a division.

    Args:
        graph_type (str): The type of graph.
        division (Division): The division object.
        year (Union[str, float]): The year for the graph.
        division_key (str): The division key.
        stat_key (str, optional): The stat key. Defaults to "wins".
        include_winless (bool, optional): Flag to include winless data. Defaults to False.

    Returns:
        str: The HTML image tag for the generic graph.
    """
    data: list[float] = division.api_graphs_generic(year, division_key, stat_key, include_winless)
    label = [str(year).capitalize()] if graph_type == "boxplot" else ""
    title = f'({str(year).capitalize()}) ({division.name}) ({division_key.capitalize()}) ' \
            f'({stat_key.capitalize()}) ({len(data)})'
    return _get_graph(graph_type, data, title, label)

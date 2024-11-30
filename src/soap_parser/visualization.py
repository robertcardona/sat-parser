import base64
import io
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from IPython import display
from PIL import Image, ImageFile

from soap_parser.tvg import *

def convert_figure(figure: plt.Figure) -> ImageFile.ImageFile:
    figure.savefig(buffer := io.BytesIO(), bbox_inches = "tight")
    # figure.savefig(buffer := io.BytesIO(), pad_inches = 0.75)
    buffer.seek(0)
    return Image.open(buffer)

def save_gif(filename: str, images: list[ImageFile.ImageFile], duration: int = 750) -> None:
    images[0].save(
        filename,
        save_all=True,
        append_images=images[1:],
        optimize=False,
        duration=duration,
        loop=0
    )

    return None

def show_gif(filename: str):

    with open(filename, 'rb') as fd:
        b64 = base64.b64encode(fd.read()).decode('ascii')
    return display.HTML(f'<img src="data:image/gif;base64,{b64}" />')

def circular_pos(g: nx.Graph) -> dict[int, tuple[int, int]]:
    # assumes each node in g is an integer 
    pos: dict[int, tuple[int, int]] = dict()
    n = len(g.nodes())
    for node in g.nodes():
        pos[node] = (np.cos(2 * np.pi * node / n), np.sin(2 * np.pi * node / n))
        
    return pos

def draw_reeb_graph(rg: nx.Graph, title: str | None = None) -> ImageFile.ImageFile:
    # TODO : add legend based on if representative reaches threshold

    # times = set()
    # for i in rg.nodes():
    #     times.add(rg.nodes[i]["column"])

    times_list = sorted(list({rg.nodes[i]["column"] for i in rg.nodes()}))
    identities_list = [n for n in rg.nodes() if rg.nodes[n]["column"] == 0]

    pos = nx.random_layout(rg)
    x = np.linspace(0, 20, len(times_list))
    y = np.linspace(0, 20, len(identities_list))

    for i in np.arange(len(times_list)):
        for node in rg.nodes():
            if rg.nodes[node]["column"] == times_list[i]:
                pos[node][0] = x[i]
    for i in np.arange(len(identities_list)):
        for node in rg.nodes():
            pos[node][1] = rg.nodes[node]["repr"]
            # if rg.nodes[node]["repr"] == identities_list[i]:
            #     pos[node][1] = y[i]
    nx.draw(rg, pos, with_labels = False, node_color = "lightblue", node_size = 10, edge_color = "gray")
    # plt.show()

    if title is not None:
        plt.title(f"Reeb Graph {title}")

    figure = plt.gcf()
    # plt.clf()

    image = convert_figure(figure)

    plt.clf()
    plt.cla()
    plt.close()

    return image

# TODO : copy over latest version from curvature
def save_tvg(
    tvg: TVG,
    filename: str,
    sample_times: list[float] | None = None
) -> None:

    if sample_times is None:
        sample_times = tvg.get_critical_times()

    images: list[ImageFile.ImageFile] = []

    for t in sample_times:
        fig = plt.figure(figsize=(5, 5))

        g = tvg.get_graph_at(t)
        pos = circular_pos(g)

        nx.draw(g, pos = pos, with_labels=True, font_weight='bold')
        figure = plt.gcf()
        images.append(convert_figure(figure))
        plt.clf()

    save_gif(filename, images)

    return None


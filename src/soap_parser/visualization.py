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
    buffer.seek(0)
    return Image.open(buffer)

def save_gif(filename: str, images: list[ImageFile.ImageFile]) -> None:
    images[0].save(
        filename,
        save_all=True,
        append_images=images[1:],
        optimize=False,
        duration=750,
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

def save_tvg(
    tvg: TVG,
    filename: str,
    sample_times: list[float] | None = None
) -> None:

    if sample_times is None:
        sample_times = tvg.get_critical_times()

    images: list[ImageFile.ImageFile] = []

    for t in sample_times:
        g = tvg.get_graph_at(t)
        pos = circular_pos(g)

        nx.draw(g, pos = pos, with_labels=True, font_weight='bold')
        figure = plt.gcf()
        images.append(convert_figure(figure))
        plt.clf()

    save_gif(filename, images)

    return None


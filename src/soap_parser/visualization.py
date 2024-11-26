import io
import matplotlib.pyplot as plt

from PIL import Image, ImageFile

def convert_figure(figure: plt.Figure) -> ImageFile.ImageFile:
    figure.savefig(buffer := io.BytesIO())
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
import numpy as np

import napari
from napari.utils.colormaps import AVAILABLE_COLORMAPS

image = np.full((100, 101), np.nan)
image[10:40, 10:40] = 0
image[10:40, 60:90] = 1
image[60:90, 10:40] = float("-inf")
image[60:90, 60:90] = float("inf")


base_cmap = AVAILABLE_COLORMAPS["viridis"]
cmap = base_cmap.copy()

cmap.nan_color = "blue"  # NaNs → blue
cmap.low_color = "red"  # ≤ 0 → red

viewer = napari.Viewer(title="Phase Images")


viewer.add_image(
    image,
    colormap=("myviridis", cmap),
    contrast_limits=(-1, 2),
)

napari.run()

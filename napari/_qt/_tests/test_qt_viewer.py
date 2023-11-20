import gc
import os
import weakref
from dataclasses import dataclass
from typing import List, Tuple
from unittest import mock

import numpy as np
import numpy.testing as npt
import pytest
from imageio import imread
from pytestqt.qtbot import QtBot
from qtpy.QtGui import QGuiApplication
from qtpy.QtWidgets import QMessageBox
from scipy import ndimage as ndi

from napari._qt.qt_viewer import QtViewer
from napari._tests.utils import (
    add_layer_by_type,
    check_viewer_functioning,
    layer_test_data,
    skip_local_popups,
    skip_on_win_ci,
)
from napari._vispy._tests.utils import vispy_image_scene_size
from napari.components.viewer_model import ViewerModel
from napari.layers import Labels, Points
from napari.settings import get_settings
from napari.utils.interactions import mouse_press_callbacks
from napari.utils.theme import available_themes

BUILTINS_DISP = 'napari'
BUILTINS_NAME = 'builtins'


def test_qt_viewer(make_napari_viewer):
    """Test instantiating viewer."""
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer

    assert viewer.title == 'napari'
    assert view.viewer == viewer

    assert len(viewer.layers) == 0
    assert view.layers.model().rowCount() == 0

    assert viewer.dims.ndim == 2
    assert view.dims.nsliders == viewer.dims.ndim
    assert np.sum(view.dims._displayed_sliders) == 0


def test_qt_viewer_with_console(make_napari_viewer):
    """Test instantiating console from viewer."""
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer
    # Check console is created when requested
    assert view.console is not None
    assert view.dockConsole.widget() is view.console


def test_qt_viewer_toggle_console(make_napari_viewer):
    """Test instantiating console from viewer."""
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer
    # Check console has been created when it is supposed to be shown
    view.toggle_console_visibility(None)
    assert view._console is not None
    assert view.dockConsole.widget() is view.console


@skip_local_popups
@pytest.mark.skipif(os.environ.get("MIN_REQ", "0") == "1", reason="min req")
def test_qt_viewer_console_focus(qtbot, make_napari_viewer):
    """Test console has focus when instantiating from viewer."""
    viewer = make_napari_viewer(show=True)
    view = viewer.window._qt_viewer
    assert not view.console.hasFocus(), "console has focus before being shown"

    view.toggle_console_visibility(None)

    def console_has_focus():
        assert (
            view.console.hasFocus()
        ), "console does not have focus when shown"

    qtbot.waitUntil(console_has_focus)


@pytest.mark.parametrize('layer_class, data, ndim', layer_test_data)
def test_add_layer(make_napari_viewer, layer_class, data, ndim):
    viewer = make_napari_viewer(ndisplay=int(np.clip(ndim, 2, 3)))
    view = viewer.window._qt_viewer

    add_layer_by_type(viewer, layer_class, data)
    check_viewer_functioning(viewer, view, data, ndim)


def test_new_labels(make_napari_viewer):
    """Test adding new labels layer."""
    # Add labels to empty viewer
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer

    viewer._new_labels()
    assert np.max(viewer.layers[0].data) == 0
    assert len(viewer.layers) == 1
    assert view.layers.model().rowCount() == len(viewer.layers)

    assert viewer.dims.ndim == 2
    assert view.dims.nsliders == viewer.dims.ndim
    assert np.sum(view.dims._displayed_sliders) == 0

    # Add labels with image already present
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer

    np.random.seed(0)
    data = np.random.random((10, 15))
    viewer.add_image(data)
    viewer._new_labels()
    assert np.max(viewer.layers[1].data) == 0
    assert len(viewer.layers) == 2
    assert view.layers.model().rowCount() == len(viewer.layers)

    assert viewer.dims.ndim == 2
    assert view.dims.nsliders == viewer.dims.ndim
    assert np.sum(view.dims._displayed_sliders) == 0


def test_new_points(make_napari_viewer):
    """Test adding new points layer."""
    # Add labels to empty viewer
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer

    viewer.add_points()
    assert len(viewer.layers[0].data) == 0
    assert len(viewer.layers) == 1
    assert view.layers.model().rowCount() == len(viewer.layers)

    assert viewer.dims.ndim == 2
    assert view.dims.nsliders == viewer.dims.ndim
    assert np.sum(view.dims._displayed_sliders) == 0

    # Add points with image already present
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer

    np.random.seed(0)
    data = np.random.random((10, 15))
    viewer.add_image(data)
    viewer.add_points()
    assert len(viewer.layers[1].data) == 0
    assert len(viewer.layers) == 2
    assert view.layers.model().rowCount() == len(viewer.layers)

    assert viewer.dims.ndim == 2
    assert view.dims.nsliders == viewer.dims.ndim
    assert np.sum(view.dims._displayed_sliders) == 0


def test_new_shapes_empty_viewer(make_napari_viewer):
    """Test adding new shapes layer."""
    # Add labels to empty viewer
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer

    viewer.add_shapes()
    assert len(viewer.layers[0].data) == 0
    assert len(viewer.layers) == 1
    assert view.layers.model().rowCount() == len(viewer.layers)

    assert viewer.dims.ndim == 2
    assert view.dims.nsliders == viewer.dims.ndim
    assert np.sum(view.dims._displayed_sliders) == 0

    # Add points with image already present
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer

    np.random.seed(0)
    data = np.random.random((10, 15))
    viewer.add_image(data)
    viewer.add_shapes()
    assert len(viewer.layers[1].data) == 0
    assert len(viewer.layers) == 2
    assert view.layers.model().rowCount() == len(viewer.layers)

    assert viewer.dims.ndim == 2
    assert view.dims.nsliders == viewer.dims.ndim
    assert np.sum(view.dims._displayed_sliders) == 0


def test_z_order_adding_removing_images(make_napari_viewer):
    """Test z order is correct after adding/ removing images."""
    data = np.ones((10, 10))

    viewer = make_napari_viewer()
    vis = viewer.window._qt_viewer.canvas.layer_to_visual
    viewer.add_image(data, colormap='red', name='red')
    viewer.add_image(data, colormap='green', name='green')
    viewer.add_image(data, colormap='blue', name='blue')
    order = [vis[x].order for x in viewer.layers]
    np.testing.assert_almost_equal(order, list(range(len(viewer.layers))))

    # Remove and re-add image
    viewer.layers.remove('red')
    order = [vis[x].order for x in viewer.layers]
    np.testing.assert_almost_equal(order, list(range(len(viewer.layers))))
    viewer.add_image(data, colormap='red', name='red')
    order = [vis[x].order for x in viewer.layers]
    np.testing.assert_almost_equal(order, list(range(len(viewer.layers))))

    # Remove two other images
    viewer.layers.remove('green')
    viewer.layers.remove('blue')
    order = [vis[x].order for x in viewer.layers]
    np.testing.assert_almost_equal(order, list(range(len(viewer.layers))))

    # Add two other layers back
    viewer.add_image(data, colormap='green', name='green')
    viewer.add_image(data, colormap='blue', name='blue')
    order = [vis[x].order for x in viewer.layers]
    np.testing.assert_almost_equal(order, list(range(len(viewer.layers))))


@skip_on_win_ci
def test_screenshot(make_napari_viewer):
    "Test taking a screenshot"
    viewer = make_napari_viewer()

    np.random.seed(0)
    # Add image
    data = np.random.random((10, 15))
    viewer.add_image(data)

    # Add labels
    data = np.random.randint(20, size=(10, 15))
    viewer.add_labels(data)

    # Add points
    data = 20 * np.random.random((10, 2))
    viewer.add_points(data)

    # Add vectors
    data = 20 * np.random.random((10, 2, 2))
    viewer.add_vectors(data)

    # Add shapes
    data = 20 * np.random.random((10, 4, 2))
    viewer.add_shapes(data)

    # Take screenshot
    with pytest.warns(FutureWarning):
        screenshot = viewer.window.qt_viewer.screenshot(flash=False)
    screenshot = viewer.window.screenshot(flash=False, canvas_only=True)
    assert screenshot.ndim == 3


@pytest.mark.skip("new approach")
def test_screenshot_dialog(make_napari_viewer, tmpdir):
    """Test save screenshot functionality."""
    viewer = make_napari_viewer()

    np.random.seed(0)
    # Add image
    data = np.random.random((10, 15))
    viewer.add_image(data)

    # Add labels
    data = np.random.randint(20, size=(10, 15))
    viewer.add_labels(data)

    # Add points
    data = 20 * np.random.random((10, 2))
    viewer.add_points(data)

    # Add vectors
    data = 20 * np.random.random((10, 2, 2))
    viewer.add_vectors(data)

    # Add shapes
    data = 20 * np.random.random((10, 4, 2))
    viewer.add_shapes(data)

    # Save screenshot
    input_filepath = os.path.join(tmpdir, 'test-save-screenshot')
    mock_return = (input_filepath, '')
    with mock.patch('napari._qt._qt_viewer.QFileDialog') as mocker, mock.patch(
        'napari._qt._qt_viewer.QMessageBox'
    ) as mocker2:
        mocker.getSaveFileName.return_value = mock_return
        mocker2.warning.return_value = QMessageBox.Yes
        viewer.window._qt_viewer._screenshot_dialog()
    # Assert behaviour is correct
    expected_filepath = input_filepath + '.png'  # add default file extension
    assert os.path.exists(expected_filepath)
    output_data = imread(expected_filepath)
    expected_data = viewer.window._qt_viewer.screenshot(flash=False)
    assert np.allclose(output_data, expected_data)


def test_points_layer_display_correct_slice_on_scale(make_napari_viewer):
    viewer = make_napari_viewer()
    data = np.zeros((60, 60, 60))
    viewer.add_image(data, scale=[0.29, 0.26, 0.26])
    pts = viewer.add_points(name='test', size=1, ndim=3)
    pts.add((8.7, 0, 0))
    viewer.dims.set_point(0, 30 * 0.29)  # middle plane

    request = pts._make_slice_request(viewer.dims)
    response = request()
    np.testing.assert_equal(response.indices, [0])


@skip_on_win_ci
def test_qt_viewer_clipboard_with_flash(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    # make sure clipboard is empty
    QGuiApplication.clipboard().clear()
    clipboard_image = QGuiApplication.clipboard().image()
    assert clipboard_image.isNull()

    # capture screenshot
    with pytest.warns(FutureWarning):
        viewer.window.qt_viewer.clipboard(flash=True)

    viewer.window.clipboard(flash=False, canvas_only=True)

    clipboard_image = QGuiApplication.clipboard().image()
    assert not clipboard_image.isNull()

    # ensure the flash effect is applied
    assert (
        viewer.window._qt_viewer._welcome_widget.graphicsEffect() is not None
    )
    assert hasattr(
        viewer.window._qt_viewer._welcome_widget, "_flash_animation"
    )
    qtbot.wait(500)  # wait for the animation to finish
    assert viewer.window._qt_viewer._welcome_widget.graphicsEffect() is None
    assert not hasattr(
        viewer.window._qt_viewer._welcome_widget, "_flash_animation"
    )

    # clear clipboard and grab image from application view
    QGuiApplication.clipboard().clear()
    clipboard_image = QGuiApplication.clipboard().image()
    assert clipboard_image.isNull()

    # capture screenshot of the entire window
    viewer.window.clipboard(flash=True)
    clipboard_image = QGuiApplication.clipboard().image()
    assert not clipboard_image.isNull()

    # ensure the flash effect is applied
    assert viewer.window._qt_window.graphicsEffect() is not None
    assert hasattr(viewer.window._qt_window, "_flash_animation")
    qtbot.wait(500)  # wait for the animation to finish
    assert viewer.window._qt_window.graphicsEffect() is None
    assert not hasattr(viewer.window._qt_window, "_flash_animation")


@skip_on_win_ci
def test_qt_viewer_clipboard_without_flash(make_napari_viewer):
    viewer = make_napari_viewer()
    # make sure clipboard is empty
    QGuiApplication.clipboard().clear()
    clipboard_image = QGuiApplication.clipboard().image()
    assert clipboard_image.isNull()

    # capture screenshot
    with pytest.warns(FutureWarning):
        viewer.window.qt_viewer.clipboard(flash=False)

    viewer.window.clipboard(flash=False, canvas_only=True)

    clipboard_image = QGuiApplication.clipboard().image()
    assert not clipboard_image.isNull()

    # ensure the flash effect is not applied
    assert viewer.window._qt_viewer._welcome_widget.graphicsEffect() is None
    assert not hasattr(
        viewer.window._qt_viewer._welcome_widget, "_flash_animation"
    )

    # clear clipboard and grab image from application view
    QGuiApplication.clipboard().clear()
    clipboard_image = QGuiApplication.clipboard().image()
    assert clipboard_image.isNull()

    # capture screenshot of the entire window
    viewer.window.clipboard(flash=False)
    clipboard_image = QGuiApplication.clipboard().image()
    assert not clipboard_image.isNull()

    # ensure the flash effect is not applied
    assert viewer.window._qt_window.graphicsEffect() is None
    assert not hasattr(viewer.window._qt_window, "_flash_animation")


def test_active_keybindings(make_napari_viewer):
    """Test instantiating viewer."""
    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer

    # Check only keybinding is Viewer
    assert len(view._key_map_handler.keymap_providers) == 1
    assert view._key_map_handler.keymap_providers[0] == viewer

    # Add a layer and check it is keybindings are active
    data = np.random.random((10, 15))
    layer_image = viewer.add_image(data)
    assert viewer.layers.selection.active == layer_image
    assert len(view._key_map_handler.keymap_providers) == 2
    assert view._key_map_handler.keymap_providers[0] == layer_image

    # Add a layer and check it is keybindings become active
    layer_image_2 = viewer.add_image(data)
    assert viewer.layers.selection.active == layer_image_2
    assert len(view._key_map_handler.keymap_providers) == 2
    assert view._key_map_handler.keymap_providers[0] == layer_image_2

    # Change active layer and check it is keybindings become active
    viewer.layers.selection.active = layer_image
    assert viewer.layers.selection.active == layer_image
    assert len(view._key_map_handler.keymap_providers) == 2
    assert view._key_map_handler.keymap_providers[0] == layer_image


@dataclass
class MouseEvent:
    # mock mouse event class
    pos: List[int]


def test_process_mouse_event(make_napari_viewer):
    """Test that the correct properties are added to the
    MouseEvent by _process_mouse_events.
    """
    # make a mock mouse event
    new_pos = [25, 25]
    mouse_event = MouseEvent(
        pos=new_pos,
    )
    data = np.zeros((5, 20, 20, 20), dtype=int)
    data[1, 0:10, 0:10, 0:10] = 1

    viewer = make_napari_viewer()
    view = viewer.window._qt_viewer
    labels = viewer.add_labels(data, scale=(1, 2, 1, 1), translate=(5, 5, 5))

    @labels.mouse_drag_callbacks.append
    def on_click(layer, event):
        np.testing.assert_almost_equal(event.view_direction, [0, 1, 0, 0])
        np.testing.assert_array_equal(event.dims_displayed, [1, 2, 3])
        assert event.dims_point[0] == data.shape[0] // 2

        expected_position = view.canvas._map_canvas2world(new_pos)
        np.testing.assert_almost_equal(expected_position, list(event.position))

    viewer.dims.ndisplay = 3
    view.canvas._process_mouse_event(mouse_press_callbacks, mouse_event)


@skip_local_popups
def test_memory_leaking(qtbot, make_napari_viewer):
    data = np.zeros((5, 20, 20, 20), dtype=int)
    data[1, 0:10, 0:10, 0:10] = 1
    viewer = make_napari_viewer()
    image = weakref.ref(viewer.add_image(data))
    labels = weakref.ref(viewer.add_labels(data))
    del viewer.layers[0]
    del viewer.layers[0]
    qtbot.wait(100)
    gc.collect()
    gc.collect()
    assert image() is None
    assert labels() is None


@skip_on_win_ci
@skip_local_popups
def test_leaks_image(qtbot, make_napari_viewer):
    viewer = make_napari_viewer(show=True)
    lr = weakref.ref(viewer.add_image(np.random.rand(10, 10)))
    dr = weakref.ref(lr().data)

    viewer.layers.clear()
    qtbot.wait(100)
    gc.collect()
    gc.collect()
    assert not lr()
    assert not dr()


@skip_on_win_ci
@skip_local_popups
def test_leaks_labels(qtbot, make_napari_viewer):
    viewer = make_napari_viewer(show=True)
    lr = weakref.ref(
        viewer.add_labels((np.random.rand(10, 10) * 10).astype(np.uint8))
    )
    dr = weakref.ref(lr().data)
    viewer.layers.clear()
    qtbot.wait(100)
    gc.collect()
    gc.collect()
    assert not lr()
    assert not dr()


@pytest.mark.parametrize("theme", available_themes())
def test_canvas_color(make_napari_viewer, theme):
    """Test instantiating viewer with different themes.

    See: https://github.com/napari/napari/issues/3278
    """
    # This test is to make sure the application starts with
    # with different themes
    get_settings().appearance.theme = theme
    viewer = make_napari_viewer()
    assert viewer.theme == theme


def test_remove_points(make_napari_viewer):
    viewer = make_napari_viewer()
    viewer.add_points([(1, 2), (2, 3)])
    del viewer.layers[0]
    viewer.add_points([(1, 2), (2, 3)])


def test_remove_image(make_napari_viewer):
    viewer = make_napari_viewer()
    viewer.add_image(np.random.rand(10, 10))
    del viewer.layers[0]
    viewer.add_image(np.random.rand(10, 10))


def test_remove_labels(make_napari_viewer):
    viewer = make_napari_viewer()
    viewer.add_labels((np.random.rand(10, 10) * 10).astype(np.uint8))
    del viewer.layers[0]
    viewer.add_labels((np.random.rand(10, 10) * 10).astype(np.uint8))


@pytest.mark.parametrize('multiscale', [False, True])
def test_mixed_2d_and_3d_layers(make_napari_viewer, multiscale):
    """Test bug in setting corner_pixels from qt_viewer.on_draw"""
    viewer = make_napari_viewer()

    img = np.ones((512, 256))
    # canvas size must be large enough that img fits in the canvas
    canvas_size = tuple(3 * s for s in img.shape)
    expected_corner_pixels = np.asarray([[0, 0], [s - 1 for s in img.shape]])

    vol = np.stack([img] * 8, axis=0)
    if multiscale:
        img = [img[::s, ::s] for s in (1, 2, 4)]
    viewer.add_image(img)
    img_multi_layer = viewer.layers[0]
    viewer.add_image(vol)

    viewer.dims.order = (0, 1, 2)
    viewer.window._qt_viewer.canvas.size = canvas_size
    viewer.window._qt_viewer.canvas.on_draw(None)
    np.testing.assert_array_equal(
        img_multi_layer.corner_pixels, expected_corner_pixels
    )

    viewer.dims.order = (2, 0, 1)
    viewer.window._qt_viewer.canvas.on_draw(None)
    np.testing.assert_array_equal(
        img_multi_layer.corner_pixels, expected_corner_pixels
    )

    viewer.dims.order = (1, 2, 0)
    viewer.window._qt_viewer.canvas.on_draw(None)
    np.testing.assert_array_equal(
        img_multi_layer.corner_pixels, expected_corner_pixels
    )


def test_remove_add_image_3D(make_napari_viewer):
    """
    Test that adding, removing and readding an image layer in 3D does not cause issues
    due to the vispy node change. See https://github.com/napari/napari/pull/3670
    """
    viewer = make_napari_viewer(ndisplay=3)
    img = np.ones((10, 10, 10))

    layer = viewer.add_image(img)
    viewer.layers.remove(layer)
    viewer.layers.append(layer)


@skip_on_win_ci
@skip_local_popups
def test_qt_viewer_multscale_image_out_of_view(make_napari_viewer):
    """Test out-of-view multiscale image viewing fix.

    Just verifies that no RuntimeError is raised in this scenario.

    see: https://github.com/napari/napari/issues/3863.
    """
    # show=True required to test fix for OpenGL error
    viewer = make_napari_viewer(ndisplay=2, show=True)
    viewer.add_shapes(
        data=[
            np.array(
                [[1500, 4500], [4500, 4500], [4500, 1500], [1500, 1500]],
                dtype=float,
            )
        ],
        shape_type=['polygon'],
    )
    viewer.add_image([np.eye(1024), np.eye(512), np.eye(256)])


def test_surface_mixed_dim(make_napari_viewer):
    """Test that adding a layer that changes the world ndim
    when ndisplay=3 before the mouse cursor has been updated
    doesn't raise an error.

    See PR: https://github.com/napari/napari/pull/3881
    """
    viewer = make_napari_viewer(ndisplay=3)

    verts = np.array([[0, 0, 0], [0, 20, 10], [10, 0, -10], [10, 10, -10]])
    faces = np.array([[0, 1, 2], [1, 2, 3]])
    values = np.linspace(0, 1, len(verts))
    data = (verts, faces, values)
    viewer.add_surface(data)

    timeseries_values = np.vstack([values, values])
    timeseries_data = (verts, faces, timeseries_values)
    viewer.add_surface(timeseries_data)


def test_insert_layer_ordering(make_napari_viewer):
    """make sure layer ordering is correct in vispy when inserting layers"""
    viewer = make_napari_viewer()
    pl1 = Points()
    pl2 = Points()

    viewer.layers.append(pl1)
    viewer.layers.insert(0, pl2)

    pl1_vispy = viewer.window._qt_viewer.canvas.layer_to_visual[pl1].node
    pl2_vispy = viewer.window._qt_viewer.canvas.layer_to_visual[pl2].node
    assert pl1_vispy.order == 1
    assert pl2_vispy.order == 0


def test_create_non_empty_viewer_model(qtbot):
    viewer_model = ViewerModel()
    viewer_model.add_points([(1, 2), (2, 3)])

    viewer = QtViewer(viewer=viewer_model)

    viewer.close()
    viewer.deleteLater()
    # try to del local reference for gc.
    del viewer_model
    del viewer
    qtbot.wait(50)
    gc.collect()


def _update_data(
    layer: Labels,
    label: int,
    qtbot: QtBot,
    qt_viewer: QtViewer,
    dtype=np.uint64,
) -> Tuple[np.ndarray, np.ndarray]:
    """Change layer data and return color of label and middle pixel of screenshot."""
    layer.data = np.full((2, 2), label, dtype=dtype)
    layer.selected_label = label

    qtbot.wait(50)  # wait for .update() to be called on QtColorBox from Qt

    color_box_color = qt_viewer.controls.widgets[layer].colorBox.color
    screenshot = qt_viewer.screenshot(flash=False)
    shape = np.array(screenshot.shape[:2])
    middle_pixel = screenshot[tuple(shape // 2)]

    return color_box_color, middle_pixel


@pytest.fixture()
def qt_viewer_with_controls(qtbot):
    qt_viewer = QtViewer(viewer=ViewerModel())
    qt_viewer.show()
    qt_viewer.controls.show()
    yield qt_viewer
    qt_viewer.controls.hide()
    qt_viewer.controls.close()
    qt_viewer.hide()
    qt_viewer.close()
    qt_viewer._instances.clear()
    qtbot.wait(50)


@skip_local_popups
@skip_on_win_ci
@pytest.mark.parametrize(
    "use_selection", [True, False], ids=["selected", "all"]
)
@pytest.mark.parametrize("dtype", [np.int16, np.int64])
def test_label_colors_matching_widget_auto(
    qtbot, qt_viewer_with_controls, use_selection, dtype
):
    """Make sure the rendered label colors match the QtColorBox widget."""

    # XXX TODO: this unstable! Seed = 0 fails, for example. This is due to numerical
    #           imprecision in random colormap on gpu vs cpu
    np.random.seed(1)
    data = np.ones((2, 2), dtype=dtype)
    layer = qt_viewer_with_controls.viewer.add_labels(data)
    layer.show_selected_label = use_selection
    layer.opacity = 1.0  # QtColorBox & single layer are blending differently
    n_c = layer.num_colors

    test_colors = np.concatenate(
        (
            np.arange(1, 10, dtype=dtype),
            [n_c - 1, n_c, n_c + 1],
            np.random.randint(
                min(2**20, np.iinfo(dtype).max), size=20, dtype=dtype
            ),
            [-2],
        )
    )

    for label in test_colors:
        # Change color & selected color to the same label
        color_box_color, middle_pixel = _update_data(
            layer, label, qtbot, qt_viewer_with_controls, dtype
        )

        npt.assert_allclose(
            color_box_color, middle_pixel, atol=1, err_msg=f"label {label}"
        )
        # there is a difference of rounding between the QtColorBox and the screenshot


@skip_local_popups
@skip_on_win_ci
@pytest.mark.parametrize("use_selection", [True, False])
def test_label_colors_matching_widget_direct(
    qtbot, qt_viewer_with_controls, use_selection
):
    """Make sure the rendered label colors match the QtColorBox widget."""
    data = np.ones((2, 2), dtype=np.uint64)
    layer = qt_viewer_with_controls.viewer.add_labels(data)
    layer.show_selected_label = use_selection
    layer.opacity = 1.0  # QtColorBox & single layer are blending differently
    layer.color = {
        0: "transparent",
        1: "yellow",
        3: "blue",
        8: "red",
        1000: "green",
        None: "white",
    }

    test_colors = (1, 2, 3, 8, 1000, 50)

    color_box_color, middle_pixel = _update_data(
        layer, 0, qtbot, qt_viewer_with_controls
    )
    assert np.allclose([0, 0, 0, 255], middle_pixel)

    for label in test_colors:
        # Change color & selected color to the same label
        color_box_color, middle_pixel = _update_data(
            layer, label, qtbot, qt_viewer_with_controls
        )
        assert np.allclose(color_box_color, middle_pixel, atol=1), label


def test_axes_labels(make_napari_viewer):
    viewer = make_napari_viewer(ndisplay=3)
    layer = viewer.add_image(np.zeros((2, 2, 2)), scale=(1, 2, 4))

    layer_visual = viewer._window._qt_viewer.layer_to_visual[layer]
    axes_visual = viewer._window._qt_viewer.canvas._overlay_to_visual[
        viewer._overlays['axes']
    ]

    layer_visual_size = vispy_image_scene_size(layer_visual)
    assert tuple(layer_visual_size) == (8, 4, 2)
    assert tuple(axes_visual.node.text.text) == ('2', '1', '0')


@pytest.fixture()
def qt_viewer(qtbot):
    qt_viewer = QtViewer(ViewerModel())
    qt_viewer.show()
    qt_viewer.resize(460, 460)
    yield qt_viewer
    qt_viewer.close()
    qt_viewer._instances.clear()
    del qt_viewer


# @pytest.mark.xfail(reason="Fails on CI, but not locally")
@skip_local_popups
@pytest.mark.parametrize('direct', [True, False], ids=["direct", "auto"])
def test_thumbnail_labels(qtbot, direct, qt_viewer: QtViewer):
    # Add labels to empty viewer
    layer = qt_viewer.viewer.add_labels(np.array([[0, 1], [2, 3]]), opacity=1)
    if direct:
        layer.color = {0: 'red', 1: 'green', 2: 'blue', 3: 'yellow'}
    else:
        layer.num_colors = 49
    qt_viewer.viewer.reset_view()
    # this test is fragile as reset view is not always working
    # I do not know how to enforce it.
    qt_viewer.canvas.native.paintGL()
    qtbot.wait(200)

    canvas_screenshot = qt_viewer.screenshot(flash=False)
    # cut off black border
    sh = canvas_screenshot.shape[:2]
    short_side = min(sh)
    margin1 = (sh[0] - short_side) // 2 + 20
    margin2 = (sh[1] - short_side) // 2 + 20
    canvas_screenshot = canvas_screenshot[margin1:-margin1, margin2:-margin2]
    thumbnail = layer.thumbnail
    scaled_thumbnail = ndi.zoom(
        thumbnail,
        np.array(canvas_screenshot.shape) / np.array(thumbnail.shape),
        order=0,
    )

    npt.assert_almost_equal(canvas_screenshot, scaled_thumbnail, decimal=1)


@pytest.mark.parametrize("dtype", [np.int8, np.int32])
def test_background_color(qtbot, qt_viewer: QtViewer, dtype):
    data = np.zeros((10, 10), dtype=dtype)
    data[5:] = 10
    layer = qt_viewer.viewer.add_labels(data, opacity=1)
    color = layer.colormap.map(10)[0] * 255

    backgrounds = (0, 2, -2)

    for background in backgrounds:
        layer._background_label = background
        data[:5] = background
        layer.data = data
        layer.num_colors = 49
        qtbot.wait(50)
        canvas_screenshot = qt_viewer.screenshot(flash=False)
        shape = np.array(canvas_screenshot.shape[:2])
        background_pixel = canvas_screenshot[tuple((shape * 0.25).astype(int))]
        color_pixel = canvas_screenshot[tuple((shape * 0.75).astype(int))]
        npt.assert_array_equal(
            background_pixel,
            [0, 0, 0, 255],
            err_msg=f"background {background}",
        )
        npt.assert_array_equal(
            color_pixel, color, err_msg=f"background {background}"
        )

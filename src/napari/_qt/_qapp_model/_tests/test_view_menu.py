import functools
import json
import operator
import os
import sys
import time

import numpy as np
import pytest
from packaging.version import parse as parse_version
from qtpy import QT_VERSION
from qtpy.QtCore import QEvent, QObject, QPoint, QPointF, Qt
from qtpy.QtGui import QMouseEvent, QWindow
from qtpy.QtWidgets import QApplication

from napari._app_model import get_app_model
from napari._app_model.actions._view import (
    _get_current_tooltip_visibility,
    _toggle_canvas_ndim,
    toggle_actions,
)
from napari._qt._qapp_model._tests.utils import register_qactions_and_plugins
from napari._tests.utils import skip_local_focus, skip_local_popups
from napari.viewer import ViewerModel


def check_windows_style(viewer):
    if os.name != 'nt':
        return
    import win32con
    import win32gui

    window_handle = viewer.window._qt_window.windowHandle()
    window_handle_id = int(window_handle.winId())
    window_style = win32gui.GetWindowLong(window_handle_id, win32con.GWL_STYLE)
    assert window_style & win32con.WS_BORDER == win32con.WS_BORDER


def check_view_menu_visibility(viewer, qtbot):
    if viewer.window._qt_window.menuBar().isNativeMenuBar():
        return

    assert not viewer.window.view_menu.isVisible()
    qtbot.keyClick(
        viewer.window._qt_window.menuBar(),
        Qt.Key.Key_V,
        modifier=Qt.KeyboardModifier.AltModifier,
    )
    qtbot.waitUntil(viewer.window.view_menu.isVisible)
    viewer.window.view_menu.close()
    assert not viewer.window.view_menu.isVisible()


@pytest.mark.parametrize(
    ('action_id', 'action_title', 'attribute_path'),
    functools.reduce(operator.iadd, toggle_actions.values(), []),
)
def test_toggle_axes_scale_bar_coordinate_grid_attr(
    action_id, action_title, attribute_path
):
    """
    Test toggle actions related with viewer axes and scale bar attributes.

    * Viewer `axes` attributes:
        * `visible`
        * `colored`
        * `labels`
        * `dashed`
        * `arrows`
    * Viewer `scale_bar` attributes:
        * `visible`
        * `box`
        * `colored`
        * `ticks`
    * Viewer `coordinate_grid` attributes:
        * `visible`
        * `labels`
    """
    app = get_app_model()
    viewer = ViewerModel()

    # Get viewer attribute to check (`axes` or `scale_bar`)
    *parent_path, attr_name = attribute_path.split('.')
    parent = viewer
    for part in parent_path:
        parent = getattr(parent, part)
    initial_value = getattr(parent, attr_name)

    # Change sub-attribute via action command execution and check value
    with app.injection_store.register(providers={ViewerModel: viewer}):
        app.commands.execute_command(action_id)

    changed_value = getattr(parent, attr_name)

    assert initial_value is not changed_value


@skip_local_popups
@pytest.mark.skipif(
    parse_version(QT_VERSION) >= parse_version('6.9.0')
    and sys.platform == 'win32',
    reason='bug in Qt with maximized windows, https://bugreports.qt.io/browse/QTBUG-135844',
)
@pytest.mark.flaky(
    reruns=2, reruns_delay=250, condition=sys.platform == 'darwin'
)  # sometimes fails on macos CI
@pytest.mark.qt_log_level_fail('WARNING')
def test_toggle_fullscreen_from_normal(
    make_napari_viewer, qtbot, qtlog, request
):
    """
    Test toggle fullscreen action from normal window state.

    Check that toggling from a normal state can be done without
    generating any type of warning and menu bar elements are visible in any
    window state.
    """
    action_id = 'napari.window.view.toggle_fullscreen'
    app = get_app_model()
    viewer = make_napari_viewer(show=True)
    debug = _DebugFullScreen(viewer.window._qt_window, qtbot)
    try:
        # Check initial default state (no fullscreen)
        assert not viewer.window._qt_window.isFullScreen()

        # Check `View` menu can be seen in normal window state
        check_view_menu_visibility(viewer, qtbot)
        debug.sample('start')

        # Check fullscreen state change
        mark = debug.mark()
        app.commands.execute_command(action_id)
        if sys.platform == 'darwin':
            # On macOS, wait for the animation to complete
            debug.wait(250)
        debug.sample('after_enter')
        if _DEBUG_FULLSCREEN == 'wait':
            debug.wait_platform(mark, full_screen=True)
        assert viewer.window._qt_window.isFullScreen()
        check_windows_style(viewer)

        # Check `View` menu can be seen in fullscreen window state
        check_view_menu_visibility(viewer, qtbot)

        # Check return to non fullscreen state
        mark = debug.mark()
        app.commands.execute_command(action_id)
        if sys.platform == 'darwin':
            # On macOS, wait for the animation to complete
            debug.wait(250)
        debug.sample('after_exit')
        if _DEBUG_FULLSCREEN == 'wait':
            debug.wait_platform(mark, full_screen=False)
        assert not viewer.window._qt_window.isFullScreen()
        check_windows_style(viewer)

        # Check `View` still menu can be seen in non fullscreen window state
        check_view_menu_visibility(viewer, qtbot)
        debug.sample('end')
    finally:
        debug.report(request, qtlog)


# --- macOS full-screen debugging (temporary, debug branch only) ------------
# '' only logs, 'wait' also waits for macOS to finish each transition
_DEBUG_FULLSCREEN = os.environ.get('NAPARI_DEBUG_FULLSCREEN', '')
_NS_WINDOW_STYLE_MASK_FULL_SCREEN = 1 << 14
_NS_WINDOW_OCCLUSION_STATE_VISIBLE = 1 << 1


def _debug_state_value(state) -> int:
    return int(getattr(state, 'value', state))


def _debug_ns_window(widget) -> dict | None:
    """Read the full-screen state of the widget's NSWindow."""
    if sys.platform != 'darwin':
        return None
    import ctypes

    objc = ctypes.cdll.LoadLibrary('/usr/lib/libobjc.A.dylib')
    objc.sel_registerName.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    address = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
    vp = ctypes.c_void_p
    send_id = ctypes.CFUNCTYPE(vp, vp, vp)(address)
    send_ulong = ctypes.CFUNCTYPE(ctypes.c_ulong, vp, vp)(address)
    send_bool = ctypes.CFUNCTYPE(ctypes.c_bool, vp, vp)(address)
    send_bool_sel = ctypes.CFUNCTYPE(ctypes.c_bool, vp, vp, vp)(address)

    def sel(name: str) -> int:
        return objc.sel_registerName(name.encode())

    handle = widget.windowHandle()
    if handle is None:
        return None
    window = send_id(int(handle.winId()), sel('window'))
    if not window:
        return {'window': None}
    style = send_ulong(window, sel('styleMask'))
    qt_full_screen = None
    if send_bool_sel(window, sel('respondsToSelector:'), sel('qt_fullScreen')):
        qt_full_screen = send_bool(window, sel('qt_fullScreen'))
    occlusion = send_ulong(window, sel('occlusionState'))
    return {
        'style_fs': bool(style & _NS_WINDOW_STYLE_MASK_FULL_SCREEN),
        'qt_fs': qt_full_screen,
        'zoomed': send_bool(window, sel('isZoomed')),
        'visible': send_bool(window, sel('isVisible')),
        'occl_visible': bool(occlusion & _NS_WINDOW_OCCLUSION_STATE_VISIBLE),
    }


class _DebugFullScreen(QObject):
    """Record what Qt and macOS report while the window toggles full screen."""

    def __init__(self, window, qtbot) -> None:
        from qtpy.QtCore import QLoggingCategory

        super().__init__()
        self.window = window
        self.qtbot = qtbot
        self.t0 = time.time()
        # [time, label, widget state, NSWindow state, frame]
        self.samples: list = []
        # [time, 'widget' or 'window', state, spontaneous] for each
        # WindowStateChange; macOS reports a finished transition to the
        # QWindow, which forwards it to the widget only if its state changed
        self.events: list = []
        # NSWindow state changes during the waits: [time, NSWindow state]
        self.timeline: list = []
        # [label, seconds waited or None on timeout]
        self.platform_waits: list = []
        self.handle = window.windowHandle()
        window.installEventFilter(self)
        self.handle.installEventFilter(self)
        QLoggingCategory.setFilterRules('qt.qpa.window.debug=true')

    def now(self) -> float:
        return round(time.time() - self.t0, 3)

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.WindowStateChange:
            is_window = isinstance(obj, QWindow)
            state = obj.windowStates() if is_window else obj.windowState()
            self.events.append(
                [
                    self.now(),
                    'window' if is_window else 'widget',
                    _debug_state_value(state),
                    event.spontaneous(),
                ]
            )
        return False

    def sample(self, label: str) -> None:
        self.samples.append(
            [
                self.now(),
                label,
                _debug_state_value(self.window.windowState()),
                _debug_ns_window(self.window),
                list(self.window.frameGeometry().getRect()),
            ]
        )

    def _poll(self) -> None:
        state = _debug_ns_window(self.window)
        if not self.timeline or self.timeline[-1][1] != state:
            self.timeline.append([self.now(), state])

    def wait(self, ms: int) -> None:
        """Wait like qtbot.wait, logging NSWindow state changes."""
        end = time.time() + ms / 1000
        self._poll()
        while time.time() < end:
            self.qtbot.wait(10)
            self._poll()

    def mark(self) -> int:
        return len(self.events)

    def wait_platform(
        self, mark: int, full_screen: bool, timeout: float = 5
    ) -> None:
        """Wait for macOS to report the requested full-screen state."""
        flag = _debug_state_value(Qt.WindowState.WindowFullScreen)
        start = time.time()

        def reported() -> bool:
            return any(
                target == 'window'
                and spontaneous
                and bool(state & flag) == full_screen
                for _, target, state, spontaneous in self.events[mark:]
            )

        while not reported() and time.time() - start < timeout:
            self.qtbot.wait(10)
            self._poll()
        waited = round(time.time() - start, 3) if reported() else None
        self.platform_waits.append(
            ['enter' if full_screen else 'exit', waited]
        )
        self.sample('after_platform_' + ('enter' if full_screen else 'exit'))

    def report(self, request, qtlog) -> None:
        from qtpy.QtCore import QLoggingCategory

        QLoggingCategory.setFilterRules('qt.qpa.window.debug=false')
        self.window.removeEventFilter(self)
        self.handle.removeEventFilter(self)
        messages = [
            [round(r.when.timestamp() - self.t0, 3), r.message[:200]]
            for r in qtlog.records
            if any(
                key in r.message
                for key in ('Applying', 'handleWindowStateChanged', 'cclusion')
            )
        ]
        summary = {
            'test': request.node.name,
            'variant': _DEBUG_FULLSCREEN,
            'samples': self.samples,
            'events': self.events,
            'timeline': self.timeline,
            'platform_waits': self.platform_waits,
            'qt_messages': messages,
        }
        capman = request.config.pluginmanager.getplugin('capturemanager')
        with capman.global_and_fixture_disabled():
            print('FSLOG', json.dumps(summary), flush=True)  # noqa: T201


@skip_local_popups
@pytest.mark.flaky(
    reruns=2, reruns_delay=250, condition=sys.platform == 'darwin'
)  # sometimes fails on macos CI
@pytest.mark.skipif(
    parse_version(QT_VERSION) >= parse_version('6.9.0'),
    reason='bug in Qt with maximized windows, https://bugreports.qt.io/browse/QTBUG-135844',
)
@pytest.mark.qt_log_level_fail('WARNING')
def test_toggle_fullscreen_from_maximized(make_napari_viewer, qtbot):
    """
    Test toggle fullscreen action from maximized window state.

    Check that toggling from a maximized state can be done without
    generating any type of warning and menu bar elements are visible in any
    window state.
    """
    action_id = 'napari.window.view.toggle_fullscreen'
    app = get_app_model()
    viewer = make_napari_viewer(show=True)

    # Check fullscreen state change while maximized
    assert not viewer.window._qt_window.isMaximized()
    viewer.window._qt_window.showMaximized()

    # Check `View` menu can be seen in maximized window state
    check_view_menu_visibility(viewer, qtbot)

    # Check fullscreen state change
    app.commands.execute_command(action_id)
    if sys.platform == 'darwin':
        # On macOS, wait for the animation to complete
        qtbot.wait(250)
    assert viewer.window._qt_window.isFullScreen()
    check_windows_style(viewer)

    # Check `View` menu can be seen in fullscreen window state coming from maximized state
    check_view_menu_visibility(viewer, qtbot)

    # Check return to non fullscreen state
    app.commands.execute_command(action_id)
    if sys.platform == 'darwin':
        # On macOS, wait for the animation to complete
        qtbot.wait(250)

    def check_not_fullscreen():
        assert not viewer.window._qt_window.isFullScreen()

    qtbot.waitUntil(check_not_fullscreen)
    check_windows_style(viewer)

    # Check `View` still menu can be seen in non fullscreen window state
    check_view_menu_visibility(viewer, qtbot)


def _mouse_move_to(widget, pos):
    """Send a synthetic MouseMove event to *widget* at local position *pos*.

    Uses ``QApplication.sendEvent`` instead of ``QTest.mouseMove`` because
    the latter bypasses QApplication event filters in Qt6, making it unreliable
    for testing the event-filter-based menubar toggle behavior.
    """
    global_pos = widget.mapToGlobal(QPoint(pos.x(), pos.y()))
    event = QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(pos),
        QPointF(global_pos),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )

    QApplication.sendEvent(widget, event)


@skip_local_focus
@pytest.mark.skipif(
    sys.platform == 'darwin',
    reason='Toggle menubar action not enabled on macOS',
)
def test_toggle_menubar(make_napari_viewer, qtbot):
    """
    Test menubar toggle functionality.

    Skipped on macOS since the menubar is the system one so the menubar
    toggle action doesn't exist/isn't enabled there.
    """
    action_id = 'napari.window.view.toggle_menubar'
    app = get_app_model()
    viewer = make_napari_viewer(show=True)

    # Check initial state (visible menubar)
    assert viewer.window._qt_window.menuBar().isVisible()
    assert not viewer.window._qt_window._toggle_menubar_visibility

    # Check menubar gets hidden
    app.commands.execute_command(action_id)
    assert not viewer.window._qt_window.menuBar().isVisible()
    assert viewer.window._qt_window._toggle_menubar_visibility
    viewer.window._qt_window.move(0, 0)
    qtbot.waitUntil(viewer.window._qt_window.isVisible)
    # Check menubar gets visible via mouse hovering over the window top area
    _mouse_move_to(viewer.window._qt_window, QPoint(15, 15))
    qtbot.waitUntil(viewer.window._qt_window.menuBar().isVisible)

    # Check menubar hides when the mouse no longer is hovering over the window top area
    _mouse_move_to(viewer.window._qt_window, QPoint(200, 200))
    qtbot.waitUntil(lambda: not viewer.window._qt_window.menuBar().isVisible())

    # Check restore menubar visibility
    app.commands.execute_command(action_id)
    assert viewer.window._qt_window.menuBar().isVisible()
    assert not viewer.window._qt_window._toggle_menubar_visibility


@pytest.mark.allow_animation_thread
def test_toggle_play(make_napari_viewer, qtbot):
    """Test toggle play action."""
    action_id = 'napari.window.view.toggle_play'
    app = get_app_model()
    viewer = make_napari_viewer()

    # Check action on empty viewer
    with pytest.warns(
        expected_warning=UserWarning, match='Refusing to play a hidden axis'
    ):
        app.commands.execute_command(action_id)

    # Check action on viewer with layer
    np.random.seed(0)
    data = np.random.random((10, 10, 15))
    viewer.add_image(data)
    # Assert action triggers play
    app.commands.execute_command(action_id)
    qtbot.waitUntil(lambda: viewer.window._qt_viewer.dims.is_playing)
    # Assert action stops play
    with qtbot.waitSignal(
        viewer.window._qt_viewer.dims._animation_thread.finished
    ):
        app.commands.execute_command(action_id)
        QApplication.processEvents()
    qtbot.waitUntil(lambda: not viewer.window._qt_viewer.dims.is_playing)


@skip_local_popups
def test_toggle_activity_dock(make_napari_viewer):
    """Test toggle activity dock"""
    action_id = 'napari.window.view.toggle_activity_dock'
    app = get_app_model()
    viewer = make_napari_viewer(show=True)

    # Check initial activity dock state (hidden)
    assert not viewer.window._qt_window._activity_dialog.isVisible()
    assert (
        viewer.window._status_bar._activity_item._activityBtn.arrowType()
        == Qt.ArrowType.UpArrow
    )

    # Check activity dock gets visible
    app.commands.execute_command(action_id)
    assert viewer.window._qt_window._activity_dialog.isVisible()
    assert (
        viewer.window._status_bar._activity_item._activityBtn.arrowType()
        == Qt.ArrowType.DownArrow
    )

    # Restore activity dock visibility (hidden)
    app.commands.execute_command(action_id)
    assert not viewer.window._qt_window._activity_dialog.isVisible()
    assert (
        viewer.window._status_bar._activity_item._activityBtn.arrowType()
        == Qt.ArrowType.UpArrow
    )


def test_toggle_layer_tooltips(mock_app_model):
    """Test toggle layer tooltips"""
    register_qactions_and_plugins()
    action_id = 'napari.window.toggle_layer_tooltips'
    app = get_app_model()

    # Check initial layer tooltip visibility settings state (False)
    assert not _get_current_tooltip_visibility()

    # Check layer tooltip visibility toggle
    app.commands.execute_command(action_id)
    assert _get_current_tooltip_visibility()

    # Restore layer tooltip visibility
    app.commands.execute_command(action_id)
    assert not _get_current_tooltip_visibility()


def test_zoom_actions(make_napari_viewer):
    """Test zoom actions"""
    viewer = make_napari_viewer()
    app = get_app_model()

    viewer.add_image(np.ones((10, 10, 10)))

    # get initial zoom state
    initial_zoom = viewer.scene.camera.zoom

    # Check zoom in action
    app.commands.execute_command('napari.scene.zoom_in')
    assert viewer.scene.camera.zoom == pytest.approx(1.5 * initial_zoom)

    # Check zoom out action
    app.commands.execute_command('napari.scene.zoom_out')
    assert viewer.scene.camera.zoom == pytest.approx(initial_zoom)

    viewer.scene.camera.zoom = 2
    # Check reset zoom action
    app.commands.execute_command('napari.scene.fit_to_view')
    assert viewer.scene.camera.zoom == pytest.approx(initial_zoom)

    # Check that angle is preserved
    viewer.dims.ndisplay = 3
    viewer.scene.camera.angles = (90, 0, 0)
    viewer.scene.camera.zoom = 2
    app.commands.execute_command('napari.scene.fit_to_view')
    # Zoom should be reset, but angle unchanged
    assert viewer.scene.camera.zoom == pytest.approx(initial_zoom)
    assert viewer.scene.camera.angles == (90, 0, 0)


@pytest.mark.parametrize(('initial', 'expected'), [(3, 2), (2, 3)])
def test_toggle_canvas_ndim(initial, expected):
    """Check that _toggle_canvas_ndim toggles the canvas ndims."""
    viewer = ViewerModel()
    viewer.dims.ndisplay = initial
    _toggle_canvas_ndim(viewer)
    assert viewer.dims.ndisplay == expected


def test_toggle_grid_mode():
    viewer = ViewerModel()
    app = get_app_model()

    viewer.add_image(np.ones((10, 10, 10)))

    # Change sub-attribute via action command execution and check value
    with app.injection_store.register(providers={ViewerModel: viewer}):
        assert viewer.canvas.grid.enabled is False
        app.commands.execute_command('napari.canvas.toggle_grid_mode')
        assert viewer.canvas.grid.enabled is True
        app.commands.execute_command('napari.canvas.toggle_grid_mode')
        assert viewer.canvas.grid.enabled is False


def test_toggle_crosshair():
    viewer = ViewerModel()
    app = get_app_model()

    # Change sub-attribute via action command execution and check value
    with app.injection_store.register(providers={ViewerModel: viewer}):
        assert viewer.scene.overlays.crosshair.visible is False
        app.commands.execute_command('napari.scene.toggle_crosshair')
        assert viewer.scene.overlays.crosshair.visible is True
        app.commands.execute_command('napari.scene.toggle_crosshair')
        assert viewer.scene.overlays.crosshair.visible is False

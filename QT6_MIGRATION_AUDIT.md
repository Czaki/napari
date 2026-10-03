# Qt6 migration audit

Date: 2026-10-02. Scope: Git-tracked Python code across src, examples, tools, tests, and vendored code, plus packaging, tox, workflows, and supporting configuration. Generated build artifacts, installed dependencies, and the separate napari-docs checkout are outside this audit.

## Applied changes

- Removed the pyqt5 optional dependency group from pyproject.toml.
- Raised the PyQt6 minimum to 6.7 and removed the now-redundant macOS exclusion for 6.6.1.
- Removed Qt5 environments, factors, extras, and references from tox.ini.
- Migrated former Qt5 CI coverage to PyQt6, including minimum requirements and macOS Intel without numba; removed Qt5 from prerelease matrices and binary-package selection.
- Updated stale examples/comments in the reusable test workflow.
- Removed the deleted-extra lookup from tools/check_updated_packages.py so the dependency-update workflow continues to work.

Runtime branches and deprecated API usages below are findings for the next code migration; they were deliberately left available for review in this change.

## Qt5 branches and compatibility fallbacks to remove

| Location | Finding / action |
| --- | --- |
| [src/napari/_qt/__init__.py:94](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/__init__.py:94) | Explicit Qt < 5.12.3 check; obsolete warning block. The nested distribution-version comparison is at line 99. Remove or replace with a supported Qt6 minimum check. |
| [src/napari/_qt/qt_event_loop.py:216](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_event_loop.py:216) | `PYQT5`: sets the two legacy high-DPI attributes before QApplication creation. Remove the branch and import at line 9. |
| [src/napari/conftest.py:1131](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/conftest.py:1131) | `PYQT5`: high-DPI setup in the QApplication fixture. Remove the branch and import at line 1066. |
| [src/napari/_qt/qt_main_window.py:108](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:108) | `SHOW_QT_WARNING = QT5`; consumed at line 248 to show the Qt5 deprecation warning once. Remove the flag, warning block, and QT5 import. |
| [src/napari/utils/theme.py:301](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/utils/theme.py:301) | `not QT6`: warns and returns dark theme. Remove this branch and QT6 import; then remove the associated pytest warning filter from pyproject.toml. |
| [src/napari/_tests/test_examples.py:49](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_tests/test_examples.py:49) | Windows CI + PyQt5: disables all examples. Remove this branch and the now-unused API_NAME import. |
| [src/napari/_qt/_qapp_model/_tests/test_view_menu.py:201](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_qapp_model/_tests/test_view_menu.py:201) | `QT_VERSION.startswith("5")`: chooses a synthetic mouse-event constructor. Keep the Qt6 constructor. |
| [src/napari/_wayland_fix.py:32](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_wayland_fix.py:32) | API fallback: QLibraryInfo.path -> location after AttributeError (line 35). Keep path and the outer import/error handling. |
| [src/napari/_qt/widgets/qt_scrollbar.py:35](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/qt_scrollbar.py:35) | API fallback: position().toPoint() if present, otherwise pos(). Keep the Qt6 expression. |
| [src/napari/_qt/qt_main_window.py:302](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:302) | API fallback: globalPosition().toPoint() if present, otherwise globalPos(). Keep the Qt6 expression. |
| [src/napari/_qt/containers/_layer_delegate.py:236](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/containers/_layer_delegate.py:236) | API fallback: globalPosition().toPoint() if present, otherwise globalPos(). Keep the Qt6 expression. |
| [src/napari/_qt/widgets/qt_dims_slider.py:508](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/qt_dims_slider.py:508) | Qt >= 5.12 feature check: hasattr(setStepType). All supported Qt6 versions provide this; simplify to the unconditional call. |

## Qt6 version checks and binding differences to retain or review separately

| Location | Finding / action |
| --- | --- |
| [src/napari/_qt/utils.py:447](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/utils.py:447) | QFont.Tag / setFeature feature checks: the PyQt6 minimum is now 6.7, so these guards and matching skips can be removed for supported environments. Matching skips: _qt/_tests/test_app.py:98 and test_qt_utils.py:215. |
| [src/napari/_qt/_qapp_model/_tests/test_view_menu.py:89](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_qapp_model/_tests/test_view_menu.py:89) | Qt >= 6.9 + Windows test skip for a maximized-window bug. Retain until that bug is resolved. |
| [src/napari/_qt/_qapp_model/_tests/test_view_menu.py:143](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_qapp_model/_tests/test_view_menu.py:143) | Qt >= 6.9 test skip for the same bug. Retain until resolved. |
| [src/napari/_qt/utils.py:139](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/utils.py:139) | PySide vs PyQt QImage buffer conversion; both Qt6 bindings still differ. Retain. |
| [src/napari/_qt/utils.py:166](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/utils.py:166) | pyqtRemoveInputHook / pyqtRestoreInputHook feature checks (line 171); binding-specific, not Qt5-specific. |
| [src/napari/_qt/utils.py:407](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/utils.py:407) | Qt.mightBeRichText with AttributeError fallback; binding API availability, not an explicit major-version check. |
| [src/napari/_qt/_qapp_model/_tests/utils.py:39](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_qapp_model/_tests/utils.py:39) | PYQT6 branch: QMenu.menuInAction versus QAction.menu workaround. This is a binding workaround; review separately against the supported minimum versions. |
| [src/napari/_qt/layer_controls/_tests/test_qt_layer_controls.py:247](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/_tests/test_qt_layer_controls.py:247) | PyQt5 or PyQt6 + Python >= 3.11 segfault skips. Remove only the PyQt5 predicate/text; retain the PyQt6 protection. |
| [src/napari/utils/info.py:205](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/utils/info.py:205) | PySide6 vs PyQt5/PyQt6 binding-version selection. Remove PyQt5 from the set at line 207; retain the PySide6/PyQt6 distinction. |

## Deprecated Qt6 APIs

### Mouse position accessors: 9 calls

Qt deprecated QMouseEvent.pos() and globalPos() in 6.0. Replace with position().toPoint() and globalPosition().toPoint() to preserve the existing integer-coordinate semantics. Three calls are fallback-only; six are executed on Qt6. [Qt documentation](https://doc.qt.io/qt-6/qmouseevent-obsolete.html).

| Location | Usage |
| --- | --- |
| [src/napari/_qt/containers/_layer_delegate.py:239](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/containers/_layer_delegate.py:239) | `event.globalPos()` |
| [src/napari/_qt/containers/_layer_delegate.py:255](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/containers/_layer_delegate.py:255) | `event.pos()` |
| [src/napari/_qt/containers/_layer_delegate.py:282](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/containers/_layer_delegate.py:282) | `event.pos()` |
| [src/napari/_qt/containers/_layer_delegate.py:296](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/containers/_layer_delegate.py:296) | `event.pos()` |
| [src/napari/_qt/qt_main_window.py:306](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:306) | `e.globalPos()` |
| [src/napari/_qt/qt_main_window.py:362](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:362) | `event.globalPos()` |
| [src/napari/_qt/qt_main_window.py:369](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:369) | `event.globalPos()` |
| [src/napari/_qt/widgets/qt_highlight_preview.py:156](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/qt_highlight_preview.py:156) | `event.pos()` |
| [src/napari/_qt/widgets/qt_scrollbar.py:38](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/qt_scrollbar.py:38) | `event.pos()` |

### QLibraryInfo.location(): 1 fallback call

[src/napari/_wayland_fix.py:35](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_wayland_fix.py:35): Qt5 fallback. Keep `QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)`. Deprecated since Qt 6.0. [Qt documentation](https://doc.qt.io/qt-6/qlibraryinfo-obsolete.html).

### QCheckBox.stateChanged: connections in application, vendor, and example code

Deprecated since Qt 6.9. Prefer checkStateChanged for tri-state controls, or toggled for boolean controls. checkStateChanged was introduced in Qt 6.7 and is available under the updated PyQt6 minimum, so no fallback for earlier Qt6 releases is needed. It emits Qt.CheckState rather than int; review callbacks for integer comparisons, conversion, and truthiness. [Deprecation](https://doc.qt.io/qt-6/qcheckbox-obsolete.html), [replacement availability](https://doc.qt.io/qt-6/qcheckbox.html).

| Location | Usage |
| --- | --- |
| [examples/multiple_viewer_widget.py:149](/Users/grzegorzbokota/Documents/Projekty/napari/examples/multiple_viewer_widget.py:149) | `self.stateChanged` |
| [src/napari/_qt/layer_controls/dynamic/widgets/_labels/qt_contiguous_checkbox.py:64](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/dynamic/widgets/_labels/qt_contiguous_checkbox.py:64) | `contig_cb.stateChanged` |
| [src/napari/_qt/layer_controls/dynamic/widgets/_labels/qt_display_selected_label_checkbox.py:61](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/dynamic/widgets/_labels/qt_display_selected_label_checkbox.py:61) | `selected_color_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/dynamic/widgets/_labels/qt_preserve_labels_checkbox.py:63](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/dynamic/widgets/_labels/qt_preserve_labels_checkbox.py:63) | `preserve_labels_cb.stateChanged` |
| [src/napari/_qt/layer_controls/dynamic/widgets/_tracks/qt_graph_checkbox.py:55](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/dynamic/widgets/_tracks/qt_graph_checkbox.py:55) | `self.graph_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/dynamic/widgets/_tracks/qt_hide_completed_tracks_checkbox.py:62](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/dynamic/widgets/_tracks/qt_hide_completed_tracks_checkbox.py:62) | `self.hide_completed_tracks_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/dynamic/widgets/_tracks/qt_id_checkbox.py:54](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/dynamic/widgets/_tracks/qt_id_checkbox.py:54) | `self.display_id_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/dynamic/widgets/_tracks/qt_tail_control.py:181](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/dynamic/widgets/_tracks/qt_tail_control.py:181) | `self.tail_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/dynamic/widgets/qt_text_visibility.py:55](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/dynamic/widgets/qt_text_visibility.py:55) | `text_disp_cb.stateChanged` |
| [src/napari/_qt/layer_controls/widgets/_labels/qt_contiguous_checkbox.py:50](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/widgets/_labels/qt_contiguous_checkbox.py:50) | `contig_cb.stateChanged` |
| [src/napari/_qt/layer_controls/widgets/_labels/qt_display_selected_label_checkbox.py:50](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/widgets/_labels/qt_display_selected_label_checkbox.py:50) | `selected_color_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/widgets/_labels/qt_preserve_labels_checkbox.py:52](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/widgets/_labels/qt_preserve_labels_checkbox.py:52) | `preserve_labels_cb.stateChanged` |
| [src/napari/_qt/layer_controls/widgets/_tracks/qt_graph_checkbox.py:44](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/widgets/_tracks/qt_graph_checkbox.py:44) | `self.graph_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/widgets/_tracks/qt_hide_completed_tracks_checkbox.py:50](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/widgets/_tracks/qt_hide_completed_tracks_checkbox.py:50) | `self.hide_completed_tracks_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/widgets/_tracks/qt_id_checkbox.py:43](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/widgets/_tracks/qt_id_checkbox.py:43) | `self.id_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/widgets/_tracks/qt_tail_control.py:156](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/widgets/_tracks/qt_tail_control.py:156) | `self.tail_checkbox.stateChanged` |
| [src/napari/_qt/layer_controls/widgets/qt_text_visibility.py:47](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/layer_controls/widgets/qt_text_visibility.py:47) | `text_disp_cb.stateChanged` |
| [src/napari/_qt/widgets/qt_dims_slider.py:222](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/qt_dims_slider.py:222) | `play_button.reverse_check.stateChanged` |
| [src/napari/_qt/widgets/qt_viewer_buttons.py:561](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/qt_viewer_buttons.py:561) | `self.camera_synced_checkbox.stateChanged` |
| [src/napari/_vendor/qt_json_builder/qt_jsonschema_form/widgets.py:132](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_vendor/qt_json_builder/qt_jsonschema_form/widgets.py:132) | `self.stateChanged` |

Total: 20 references, including both the regular and dynamic controls.

### exec_(): legacy Python alias

Use exec() for QApplication, QDialog, QMenu, and QDrag. This is a Python-binding legacy alias, distinct from a deprecated C++ Qt method. Qt for Python recommends exec() since 6.1. The inventory includes test mocks and documentation that must change together with the calls. [Qt for Python announcement](https://www.qt.io/blog/qt-for-python-6.1).

| Location | Call |
| --- | --- |
| [examples/inherit_viewer_style.py:73](/Users/grzegorzbokota/Documents/Projekty/napari/examples/inherit_viewer_style.py:73) | `dialog.exec_()` |
| [examples/multithreading_simple_.py:54](/Users/grzegorzbokota/Documents/Projekty/napari/examples/multithreading_simple_.py:54) | `app.exec_()` |
| [src/napari/_qt/_qapp_model/qactions/_plugins.py:37](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_qapp_model/qactions/_plugins.py:37) | `window._qt_window._plugin_manager_dialog.exec_()` |
| [src/napari/_qt/_tests/test_sigint_interupt.py:30](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_tests/test_sigint_interupt.py:30) | `qapp.exec_()` |
| [src/napari/_qt/containers/_layer_delegate.py:353](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/containers/_layer_delegate.py:353) | `self._context_menu.exec_(pos)` |
| [src/napari/_qt/dialogs/qt_reader_dialog.py:139](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/dialogs/qt_reader_dialog.py:139) | `self.exec_()` |
| [src/napari/_qt/qt_event_loop.py:447](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_event_loop.py:447) | `app.exec_()` |
| [src/napari/_qt/qt_main_window.py:497](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:497) | `ConfirmCloseDialog(self, quit_app).exec_()` |
| [src/napari/_qt/qt_main_window.py:608](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:608) | `ConfirmCloseDialog(self, close_app=False, extra_info='\n'.join(task_status), display_checkbox=False).exec_()` |
| [src/napari/_qt/qt_main_window.py:619](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:619) | `ConfirmCloseDialog(self, close_app=False).exec_()` |
| [src/napari/_qt/qt_main_window.py:1905](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:1905) | `dial.exec_()` |
| [src/napari/_qt/utils.py:489](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/utils.py:489) | `dlg.exec_()` |
| [src/napari/_qt/widgets/qt_keyboard_settings.py:569](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/qt_keyboard_settings.py:569) | `self._warn_dialog.exec_()` |
| [src/napari/_vendor/qt_json_builder/qt_jsonschema_form/widgets.py:285](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_vendor/qt_json_builder/qt_jsonschema_form/widgets.py:285) | `dlg.exec_()` |

Total: 14 calls.

Other exec_ references (mocks, docstrings, and a commented example):

- [src/napari/_qt/_qapp_model/_tests/test_file_menu.py:412](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_qapp_model/_tests/test_file_menu.py:412): `'napari._qt.dialogs.screenshot_dialog.ScreenshotDialog.exec_',`
- [src/napari/_qt/_tests/test_app.py:53](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_tests/test_app.py:53): `m.setattr(qapp, 'exec_', mock_exec)`
- [src/napari/_qt/_tests/test_qt_utils.py:168](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_tests/test_qt_utils.py:168): `def _mock_exec_(self):`
- [src/napari/_qt/_tests/test_qt_utils.py:169](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_tests/test_qt_utils.py:169): `"""Mock exec_ method to always return Accepted."""`
- [src/napari/_qt/_tests/test_qt_utils.py:176](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_tests/test_qt_utils.py:176): `monkeypatch.setattr(QColorDialog, 'exec_', _mock_exec_)`
- [src/napari/_qt/_tests/test_qt_utils.py:200](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_tests/test_qt_utils.py:200): `def _mock_exec_(self):`
- [src/napari/_qt/_tests/test_qt_utils.py:201](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_tests/test_qt_utils.py:201): `"""Mock exec_ method to always return Accepted."""`
- [src/napari/_qt/_tests/test_qt_utils.py:208](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/_tests/test_qt_utils.py:208): `monkeypatch.setattr(QColorDialog, 'exec_', _mock_exec_)`
- [src/napari/_qt/containers/_tests/test_qt_layer_list.py:166](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/containers/_tests/test_qt_layer_list.py:166): `'app_model.backends.qt.QModelMenu.exec_', lambda self, x: x`
- [src/napari/_qt/containers/_tests/test_qt_layer_list.py:201](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/containers/_tests/test_qt_layer_list.py:201): `'app_model.backends.qt.QModelMenu.exec_', lambda self, x: x`
- [src/napari/_qt/qt_event_loop.py:317](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_event_loop.py:317): `# the event loop is restarted with app.exec_().  So rather than`
- [src/napari/_qt/qt_event_loop.py:397](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_event_loop.py:397): `time QApplication.exec_() is called, Qt enters the event loop,`
- [src/napari/_qt/qt_event_loop.py:399](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_event_loop.py:399): `This function will prevent calling exec_() if the application already`
- [src/napari/_qt/utils.py:215](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/utils.py:215): `...         drag.exec_(supportedActions, Qt.MoveAction)`
- [src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:95](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:95): `with mock_qt_method_ctx(WarnPopup, 'exec_') as mock:`
- [src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:98](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:98): `with mock_qt_method_ctx(WarnPopup, 'exec_') as mock:`
- [src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:101](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:101): `with mock_qt_method_ctx(WarnPopup, 'exec_') as mock:`
- [src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:105](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:105): `with mock_qt_method_ctx(WarnPopup, 'exec_') as mock:`
- [src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:108](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:108): `with mock_qt_method_ctx(WarnPopup, 'exec_') as mock:`
- [src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:186](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:186): `mock = mock_qt_method(WarnPopup, 'exec_')`
- [src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:256](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/widgets/_tests/test_shortcut_editor_widget.py:256): `with mock_qt_method_ctx(WarnPopup, 'exec_') as mock:`
- [src/napari/_tests/test_cli.py:93](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_tests/test_cli.py:93): `'qtpy.QtWidgets.QApplication.exec_', lambda *_: None`

## PySide6 stubs and false positives

The locally installed PySide6 is 6.9.0. Its stubs and runtime include QMouseEvent.pos/globalPos, QLibraryInfo.location, QCheckBox.stateChanged, and exec_ on QDialog/QApplication/QMenu. Thus deprecated APIs are not universally omitted from PySide6 stubs. This does not establish their presence in newer releases; the audit uses official Qt deprecation documentation rather than stub presence as the authority. QMouseEvent.position/globalPosition are inherited from QSinglePointEvent; they should not be diagnosed as missing simply because they are not declared directly on QMouseEvent.

The following uses were inspected and are not deprecated overloads:

- QMouseEvent constructors in the view-menu and dynamic-button tests include explicit global positions; they are not the local-position-only constructor deprecated in Qt 6.4.
- QCursor.pos(), QWidget.pos(), QWidget.fontMetrics(), no-argument itemDelegate(), icon pixmap(size) and pixmap(width, height), and enum-based setTextAlignment() use valid APIs.
- QMenu.addAction(action) is not one of the deprecated callback/shortcut overloads.
- QMessageBox calls use StandardButton(s), not deprecated separate integer button arguments.
- QTimer.singleShot(milliseconds, callable) is not the deprecated receiver/member-string overload.
- utils.py:374 connects QSocketNotifier.activated without explicitly selecting the deprecated int overload; the local PySide6 default is QSocketDescriptor/QSocketNotifier.Type. Do not blindly rename this signal. [Qt overload documentation](https://doc.qt.io/qt-6/qsocketnotifier-obsolete.html).
- Qt5-only high-DPI attribute calls in qt_event_loop.py and conftest.py are legacy configuration to remove with their branches, not calls currently executed under Qt6.

## Other remaining Qt5 references

| Location | Finding / action |
| --- | --- |
| [src/napari/_qt/__init__.py:41](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/__init__.py:41) | Remove PyQt5 from the import-error diagnostic mapping. |
| [src/napari/_qt/__init__.py:74](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/__init__.py:74) | Remove PyQt5 from the recommended bindings and the napari[pyqt5] installation instruction at line 78. |
| [src/napari/utils/_env_detection.py:88](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/utils/_env_detection.py:88) | Remove detection of PyQt5, or explicitly decide whether reporting unsupported installed bindings remains useful. |
| [pyproject.toml:526](/Users/grzegorzbokota/Documents/Projekty/napari/pyproject.toml:526) | System-theme warning suppression explicitly marked for deletion when Qt5 support is dropped; remove together with the theme.py branch. |
| [pyproject.toml:691](/Users/grzegorzbokota/Documents/Projekty/napari/pyproject.toml:691) | PyQt5 in forbidden_modules is an import-linter prohibition, not supported dependency configuration. Keeping it prevents direct legacy imports. |
| [binder/apt.txt:17](/Users/grzegorzbokota/Documents/Projekty/napari/binder/apt.txt:17) | Qt5 development package libqt5x11extras5-dev remains in the Binder image. Review/remove if unnecessary for other image dependencies. |
| [.github/ISSUE_TEMPLATE/bug_report.yml:62](/Users/grzegorzbokota/Documents/Projekty/napari/.github/ISSUE_TEMPLATE/bug_report.yml:62) | Example environment still reports PyQt5 5.15.10; update to a Qt6 example. |
| [examples/mpl_plot_.py:10](/Users/grzegorzbokota/Documents/Projekty/napari/examples/mpl_plot_.py:10) | Matplotlib backend_qt5agg import; replace with backend_qtagg for the binding-neutral Qt backend. |
| [src/napari/_qt/perf/qt_event_tracing.py:45](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/perf/qt_event_tracing.py:45) | EventTypes docstring uses PySide2/PyQt5 and has a stale PySide6 TODO at line 56. Revalidate enum mapping before simplifying. |
| [src/napari/_qt/utils.py:163](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/utils.py:163) | Input-hook docstring says PyQt5; update to PyQt. |
| [src/napari/_qt/utils.py:446](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/utils.py:446) | Font-feature comment says PyQt5 is supported; remove it when simplifying the now-unnecessary Qt < 6.7 guard. |
| [src/napari/_vispy/canvas.py:1357](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_vispy/canvas.py:1357) | Comment references Ubuntu py3.11 PyQt5 tests; historical context to review. |
| [src/napari/_qt/qt_main_window.py:979](/Users/grzegorzbokota/Documents/Projekty/napari/src/napari/_qt/qt_main_window.py:979) | StackOverflow URL contains pyqt5; historical reference, not a dependency or branch. |

## Verification

- pyproject.toml, tox.ini, and every workflow YAML file parse successfully.
- No PyQt5/PySide2 references remain in tox.ini or workflow files; pyqt5 is absent from optional dependencies.
- tox list succeeds with PyQt6/PySide6 GUI environments and headless environments.
- Dependency-update helper accepts PyQt6/PySide6 changes and excludes PyQt5 without raising a deleted-extra KeyError.
- Ruff passes for the changed Python helper; git diff --check passes.
- No GUI suite was run: application runtime code is unchanged. Actual workflow jobs and installation across the CI platform matrix require CI.

This is a static source audit, not proof that every deprecated overload can never be selected dynamically or inside third-party dependencies. The listed calls were checked against their receiver/context to avoid common name-only false positives.

import sys
from copy import deepcopy
from enum import Enum

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QLabel,
    QFrame,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QTabWidget,
    QLineEdit,
    QCheckBox,
    QSlider,
    QDialog,
    QGridLayout,
    QStackedWidget,
    QProgressBar,
    QDialogButtonBox,
)

from PySide6 import QtCore
from PySide6.QtCore import Qt, QSize, QRect, QTimer, QEvent
from PySide6.QtGui import QPaintEvent, QPainter, QImage

from mediapipe import solutions
import numpy as np
import cv2

from aethervr.config import *
from aethervr.tracking_state import TrackingState
from aethervr.input_state import ControllerButton
from aethervr.runtime_connection import RuntimeConnection, RegisterImageData, PresentImageData
from aethervr.system_openxr_config import SystemOpenXRConfig
from aethervr.display_surface import DisplaySurface
from aethervr.camera_capture import CameraCapture
from aethervr.camera_capture2 import Camera, CameraCapture2
from aethervr import platform


STYLESHEET = """
.StatusBar {
    padding: 6px;
}

.ConfigPanel {
    padding: 8pt;
    border-right: 1px solid black;
}
"""


class Window(QMainWindow):

    def __init__(
        self,
        config: Config,
        system_openxr_config: SystemOpenXRConfig,
        connection: RuntimeConnection,
        camera_capture: CameraCapture,
        camera_capture2: CameraCapture2,
    ):
        super().__init__()

        self.config = config
        self.system_openxr_config = system_openxr_config
        self.connection = connection
        self.camera_capture = camera_capture
        self.camera_capture2 = camera_capture2

        self.camera_view = None
        self.frame_view = None

        self.setWindowTitle("AetherVR Tracker")
        self.resize(QSize(1280, 640))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._create_horizontal_widget())
        layout.addWidget(StatusBar(connection))

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def _create_horizontal_widget(self):
        widget = QWidget()

        self.camera_view = CameraView()
        self.frame_view = FrameView(self.connection)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)

        tab_widget = QTabWidget()
        tab_widget.setContentsMargins(10, 10, 10, 10)
        tab_widget.addTab(self._create_camera_tab(), "Camera")
        tab_widget.addTab(self._create_application_tab(), "Application")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(ConfigPanel(self.config, self.system_openxr_config, self.camera_capture, self.camera_capture2))
        layout.addWidget(separator)
        layout.addWidget(tab_widget)
        widget.setLayout(layout)

        size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(1)
        widget.setSizePolicy(size_policy)

        return widget

    def _create_camera_tab(self):
        return self.camera_view

    def _create_application_tab(self):
        widget = QWidget()

        layout = QHBoxLayout()
        layout.addWidget(self.frame_view, Qt.AlignmentFlag.AlignCenter)
        widget.setLayout(layout)
        
        return widget

    def show_download_dialog(self, on_download) -> bool:
        response = QMessageBox.question(
            self,
            "MediaPipe Models",
            "The AetherVR tracker requires two MediaPipe machine learning models in order to run. "
            "These files are downloaded from Google's servers and placed in the `mp_models` directory.\n\n"
            "Would you like to continue and start the download?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Close,
            QMessageBox.StandardButton.Yes,
        )

        if response == QMessageBox.StandardButton.Yes:
            dialog = DownloadDialog(self)
            on_download(dialog.close_remotely, dialog.close_with_error_remotely)
            dialog.exec()
            return True
        else:
            return False

    def update_camera_frame(self, frame):
        self.camera_view.update_frame(frame)

    def update_camera_overlay(self, tracking_state: TrackingState):
        self.camera_view.update_overlay(tracking_state)

    def clear_camera_overlay(self):
        self.camera_view.clear_overlay()

    def display_camera_error(self):
        self.camera_view.display_camera_error()


class ConfigPanel(QWidget):

    def __init__(
        self,
        config: Config,
        system_openxr_config: SystemOpenXRConfig,
        camera_capture: CameraCapture,
        camera_capture2: CameraCapture2,
    ):
        super().__init__()
        self.config = config

        reset_button = QPushButton("Reset Configuration")
        reset_button.clicked.connect(self._on_config_reset)

        layout = QVBoxLayout()
        layout.addWidget(OpenXRConfigGroup(system_openxr_config))
        layout.addWidget(TrackingConfigGroup(config, camera_capture, camera_capture2))
        layout.addWidget(GeneralInputMappingGroup(config))
        layout.addWidget(ControllerConfigGroup(config))
        layout.addWidget(reset_button)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        self.setMinimumWidth(320)
    
    def _on_config_reset(self):
        self.config.set_to_default()
        self.config.on_updated.trigger()


class OpenXRConfigGroup(QGroupBox):

    def __init__(self, system_openxr_config: SystemOpenXRConfig):
        super().__init__("OpenXR")
        self.system_openxr_config = system_openxr_config

        self.current_label = QLabel()

        self.set_button = QPushButton("Set AetherVR as OpenXR Runtime")
        self.set_button.clicked.connect(self._activate_aethervr)

        self.incompatible_label = QLabel(
            "Warning: The current AetherVR runtime has a different version than this tracker and might "
            "not be compatible! Click 'Set' to replace the current AetherVR runtime with the right version."
        )
        self.incompatible_label.setWordWrap(True)
        self.incompatible_label.setStyleSheet("QLabel { color: #dec60f; }")

        self.unavailable_label = QLabel("OpenXR system configuration is unavailable on macOS.")
        self.unavailable_label.setWordWrap(True)

        layout = QFormLayout()
        
        if not platform.is_macos:
            layout.addRow(QLabel("Current OpenXR Runtime:"), self.current_label)
            layout.addRow(self.incompatible_label)
            layout.addRow(self.set_button)
        else:
            layout.addRow(self.unavailable_label)
        
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(2000)

        self._refresh()

    def _activate_aethervr(self):
        if self.system_openxr_config.activate_aethervr():
            self._refresh()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to set AetherVR as the system OpenXR runtime. "
                "Please make sure you're running AetherVR as an administrator.",
            )

    def _refresh(self):
        active_runtime = self.system_openxr_config.active_runtime_name()
        self.current_label.setText("None" if active_runtime is None else active_runtime)

        status = self.system_openxr_config.status()
        self.incompatible_label.setVisible(status == SystemOpenXRConfig.Status.DIFFERENT_VERSION)
        self.set_button.setEnabled(status != SystemOpenXRConfig.Status.OK)


class TrackingConfigGroup(QGroupBox):

    def __init__(self, config: Config, camera_capture: CameraCapture, camera_capture2: CameraCapture2):
        super().__init__("Tracking")

        self.config = config
        self.camera_capture = camera_capture
        self.camera_capture2 = camera_capture2

        self.tracking_label = QLabel()
        self.tracking_button = QPushButton()
        self.tracking_button.clicked.connect(self._on_tracking_button_clicked)

        self.fps_input = QLineEdit()
        self.fps_input.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.fps_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_input.editingFinished.connect(self._on_fps_input_changed)

        self.capture_label = QLabel()

        self.capture_config_button = QPushButton("Configure")
        self.capture_config_button.clicked.connect(self._open_capture_config_dialog)

        layout = QFormLayout()
        layout.addRow(self.tracking_label, self.tracking_button)
        layout.addRow(self.capture_label, self.capture_config_button)
        layout.addRow("Max. Frames per Second:", self.fps_input)
        self.setLayout(layout)

        self._update_tracking_status()
        self._update_capture_status()
        self._update_fps_input()

        config.on_updated.subscribe(self._update_fps_input)

    def _on_tracking_button_clicked(self):
        self.config.tracking_running = not self.config.tracking_running
        self._update_tracking_status()

    def _open_capture_config_dialog(self):
        dialog = CaptureConfigDialog(self, self.config, self.camera_capture, self.camera_capture2)
        dialog.show()
        dialog.exec_()
        self._update_capture_status()

    def _on_fps_input_changed(self):
        try:
            value = int(self.fps_input.text())
            
            if value > 0:
                self.config.tracking_fps_cap = value
        except ValueError:
            pass

        self._update_fps_input()

    def _update_tracking_status(self):
        if self.config.tracking_running:
            self.tracking_label.setText("Status: Running")
            self.tracking_button.setText("Stop")
        else:
            self.tracking_label.setText("Status: <span style=\"color: #cc3d3d\">Stopped</span>")
            self.tracking_button.setText("Start")

    def _update_capture_status(self):
        config = self.config.capture_config

        if config.camera:
            self.capture_label.setText(f"{config.camera.name} ({config.frame_width}x{config.frame_height})")
        else:
            self.capture_label.setText(f"Camera not configured")

    def _update_fps_input(self):
        self.fps_input.setText(str(self.config.tracking_fps_cap))


class CaptureConfigDialog(QDialog):

    def __init__(self, parent: QWidget, config: Config, capture: CameraCapture, capture2: CameraCapture2):
        super().__init__(parent)

        self.capture_config = config.capture_config
        self.capture = capture
        self.capture2 = capture2

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Camera Capture Configuration")
        self.setMinimumWidth(320)

        self.camera_input = QComboBox()

        for camera in self.capture2.cameras:
            self.camera_input.addItem(camera.name, camera)

        self.camera_input.currentIndexChanged.connect(self.update_resolutions)

        self.resolution_input = QComboBox()
        
        self.button_box = QDialogButtonBox()
        self.apply_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.cancel_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.button_box.clicked.connect(self.on_button_clicked)

        layout = QFormLayout()
        layout.addRow("Camera:", self.camera_input)
        layout.addRow("Resolution:", self.resolution_input)
        layout.addRow(self.button_box)
        self.setLayout(layout)

        self.update_resolutions()

        current_name = None
        current_width = self.capture_config.frame_width
        current_height = self.capture_config.frame_height

        if type(self.capture_config.camera) is Camera:
            current_name = self.capture_config.camera.name
        elif type(self.capture_config.camera) is str:
            current_name = self.capture_config.camera

        for i in range(self.camera_input.count()):
            camera = self.camera_input.itemData(i)

            if camera.name == current_name:
                self.resolution_input.setCurrentIndex(i)
                break

        for i in range(self.resolution_input.count()):
            resolution = self.resolution_input.itemData(i)
            width, height = resolution.width, resolution.height

            if width == current_width and height == current_height:
                self.resolution_input.setCurrentIndex(i)
                break

    def on_button_clicked(self, button):
        if button == self.apply_button:
            camera = self.camera_input.currentData()
            resolution = self.resolution_input.currentData()

            self.capture_config.camera = camera
            self.capture_config.frame_width = resolution.width
            self.capture_config.frame_height = resolution.height

            self.capture2.start()
        
        self.close()

    def update_resolutions(self):
        camera = self.camera_input.currentData()

        self.resolution_input.clear()

        for resolution in camera.resolutions:
            self.resolution_input.addItem(f"{resolution.width} x {resolution.height}", resolution)


class GeneralInputMappingGroup(QGroupBox):

    def __init__(self, config: Config):
        super().__init__("General Input Mapping")

        self.config = config

        self.headset_pitch_deadzone = DeadzoneInput(self._update_headset_pitch_deadzone)
        self.headset_yaw_deadzone = DeadzoneInput(self._update_headset_yaw_deadzone)

        self.hand_tracking_mode_input = QComboBox()
        self.hand_tracking_mode_input.addItem("Direct (more responsive)", HandTrackingMode.DIRECT)
        self.hand_tracking_mode_input.addItem("Smooth (more stable)", HandTrackingMode.SMOOTH)
        self.hand_tracking_mode_input.currentIndexChanged.connect(self._on_hand_tracking_mode_selected)

        controller_pose_button = QPushButton("Configure Controller Pose")
        controller_pose_button.clicked.connect(self._show_controller_pose_dialog)

        layout = QFormLayout()
        layout.addRow("Headset Pitch Deadzone:", self.headset_pitch_deadzone)
        layout.addRow("Headset Yaw Deadzone:", self.headset_yaw_deadzone)
        layout.addRow("Hand Tracking Mode:", self.hand_tracking_mode_input)
        layout.addRow(controller_pose_button)
        self.setLayout(layout)

        self.config.on_updated.subscribe(self.sync_values)
        self.sync_values()

    def sync_values(self):
        self.headset_pitch_deadzone.set_value(self.config.headset_pitch_deadzone)
        self.headset_yaw_deadzone.set_value(self.config.headset_yaw_deadzone)

        hand_tracking_mode_index = self.hand_tracking_mode_input.findData(self.config.hand_tracking_mode)
        self.hand_tracking_mode_input.setCurrentIndex(hand_tracking_mode_index)

    def _update_headset_pitch_deadzone(self, value: int):
        self.config.headset_pitch_deadzone = value
    
    def _update_headset_yaw_deadzone(self, value: int):
        self.config.headset_yaw_deadzone = value

    def _on_hand_tracking_mode_selected(self, index: int):
        mode = self.hand_tracking_mode_input.itemData(index)
        self.config.hand_tracking_mode = mode

    def _show_controller_pose_dialog(self):
        dialog = ControllerPoseDialog(self, self.config)
        dialog.show()


class ControllerConfigGroup(QTabWidget):

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

        self.left_controller_tab = ControllerConfigTab(config.left_controller_config)
        self.right_controller_tab = ControllerConfigTab(config.right_controller_config)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.addTab(self.left_controller_tab, "Left Controller")
        self.addTab(self.right_controller_tab, "Right Controller")

        config.on_updated.subscribe(self.sync_values)

    def sync_values(self):
        self.left_controller_tab.sync_values()
        self.right_controller_tab.sync_values()


class ControllerConfigTab(QWidget):

    def __init__(self, config: ControllerConfig):
        super().__init__()
        self.config = config

        self.pinch_binding_dropdown = ButtonBindingDropdown(config, Gesture.PINCH)
        self.palm_pinch_binding_dropdown = ButtonBindingDropdown(config, Gesture.PALM_PINCH)
        self.middle_pinch_binding_dropdown = MiddlePinchBindingDropdown(config)
        self.fist_binding_dropdown = ButtonBindingDropdown(config, Gesture.FIST)

        self.press_thumbstick_checkbox = QCheckBox("Press Thumbstick During Use")
        self.press_thumbstick_checkbox.setChecked(config.press_thumbstick)
        self.press_thumbstick_checkbox.checkStateChanged.connect(self._update_press_thumbstick)

        layout = QFormLayout()
        layout.addRow("Pinch:", self.pinch_binding_dropdown)
        layout.addRow("Palm Pinch:", self.palm_pinch_binding_dropdown)
        layout.addRow("Middle Pinch:", self.middle_pinch_binding_dropdown)
        layout.addRow("Fist:", self.fist_binding_dropdown)
        layout.addRow(self.press_thumbstick_checkbox)
        self.setLayout(layout)

    def sync_values(self):
        self.pinch_binding_dropdown.sync_value()
        self.palm_pinch_binding_dropdown.sync_value()
        self.middle_pinch_binding_dropdown.sync_value()
        self.fist_binding_dropdown.sync_value()

        self.press_thumbstick_checkbox.setChecked(self.config.press_thumbstick)

    def _update_press_thumbstick(self, state):
        self.config.press_thumbstick = state == Qt.CheckState.Checked


class DeadzoneInput(QWidget):

    def __init__(self, on_value_changed):
        super().__init__()

        self.value = 0.0
        self.on_value_changed = on_value_changed

        self.input = QLineEdit()
        self.input.setFixedWidth(60)
        self.input.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.input.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.input.editingFinished.connect(self._on_editing_finished)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.input)
        layout.addWidget(QLabel("degrees"))

        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        self.setLayout(layout)

    def set_value(self, value: float):
        self.value = value
        self.input.setText(str(value))

    def _on_editing_finished(self):
        try:
            self.value = int(self.input.text())
            self.value = max(min(self.value, 45), -45)
            self.on_value_changed(self.value)
        except ValueError:
            pass
        
        self.input.setText(str(self.value))


class ControllerPoseDialog(QDialog):

    def __init__(self, parent: QWidget, config: Config):
        super().__init__(parent)

        self.config = config

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Controller Pose")
        self.setMinimumWidth(480)        

        layout = QGridLayout()
        layout.addWidget(QLabel("Pitch:"), 0, 0)
        layout.addWidget(AngleSlider(config.controller_pitch, self._update_pitch), 0, 1)
        layout.addWidget(QLabel("Yaw:"), 1, 0)
        layout.addWidget(AngleSlider(config.controller_yaw, self._update_yaw), 1, 1)
        layout.addWidget(QLabel("Roll:"), 2, 0)
        layout.addWidget(AngleSlider(config.controller_roll, self._update_roll), 2, 1)
        layout.addWidget(QLabel("Depth Offset:"), 3, 0)
        layout.addWidget(Slider(config.controller_depth_offset, -5, 5, 1, 0.1, "{:.1f}m", self._update_offset), 3, 1)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        self.setLayout(layout)

    def _update_pitch(self, pitch: float):
        self.config.controller_pitch = pitch

    def _update_yaw(self, yaw: float):
        self.config.controller_yaw = yaw

    def _update_roll(self, roll: float):
        self.config.controller_roll = roll

    def _update_offset(self, offset: float):
        self.config.controller_depth_offset = offset


class Slider(QWidget):

    def __init__(
        self,
        initial_value: float,
        min: int,
        max: int,
        tick_interval: int,
        scale: int,
        format_template: str,
        on_value_changed,
    ):
        super().__init__()

        self.value = initial_value
        self.scale = scale
        self.format_template = format_template
        self.on_value_changed = on_value_changed

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(tick_interval)
        slider.setValue(int(initial_value / scale))
        slider.valueChanged.connect(self._on_value_changed)

        self.label = QLabel()
        self.label.setFixedWidth(40)
        self.label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QHBoxLayout()
        layout.addWidget(slider)
        layout.addWidget(self.label)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.setLayout(layout)

        self._update_label()

    def _on_value_changed(self, value: int):
        self.value = self.scale * value
        self.on_value_changed(float(self.value))
        self._update_label()

    def _update_label(self):
        self.label.setText(self.format_template.format(self.value))


class AngleSlider(Slider):
    
    def __init__(self, initial_angle: float, on_angle_changed):
        super().__init__(initial_angle, -12, 12, 3, 15, "{:.0f}°", on_angle_changed)


class ButtonBindingDropdown(QComboBox):

    def __init__(self, config: ControllerConfig, gesture: Gesture):
        super().__init__()
        self.config = config
        self.gesture = gesture

        self.addItem("None", None)
        self.addItem("Trigger", ControllerButton.TRIGGER)
        self.addItem("Squeeze", ControllerButton.SQUEEZE)
        self.addItem("A", ControllerButton.A_BUTTON)
        self.addItem("B", ControllerButton.B_BUTTON)
        self.addItem("X", ControllerButton.X_BUTTON)
        self.addItem("Y", ControllerButton.Y_BUTTON)
        self.addItem("Menu", ControllerButton.MENU)
        self.addItem("System", ControllerButton.SYSTEM)
        self.currentIndexChanged.connect(self._on_selected)

        self.sync_value()

    def sync_value(self):
        value = self.config.gesture_mappings[self.gesture]
        self.setCurrentIndex(self.findData(value))

    def _on_selected(self, index: int):
        button = self.itemData(index)
        self.config.gesture_mappings[self.gesture] = button


class MiddlePinchBindingDropdown(QComboBox):

    def __init__(self, config: ControllerConfig):
        super().__init__()
        self.config = config

        self.addItem("None", False)
        self.addItem("Thumbstick", True)
        self.currentIndexChanged.connect(self._on_selected)

        self.sync_value()

    def sync_value(self):
        value = self.config.thumbstick_enabled
        self.setCurrentIndex(self.findData(value))

    def _on_selected(self, index: int):
        value = self.itemData(index)
        self.config.thumbstick_enabled = value


class CameraView(QLabel):

    HEAD_CONTOUR_LANDMARK_INDICES = [
        10, 338, 297, 332, 284, 251, 389, 356,
        454, 366, 323, 401, 361, 435, 288, 397,
        365, 379, 378, 400, 377, 152, 148, 176,
        149, 150, 136, 172, 58, 132, 93, 234,
        127, 162, 21, 54, 103, 67, 109,
    ]

    HEAD_OTHER_LANDMARK_INDICES = [
        468, 473, 4
    ]

    MIN_IMAGE_PADDING = 20

    def __init__(self):
        super().__init__("Starting camera capture...")

        self.frame = None
        self.overlay = None

        size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        size_policy.setHorizontalStretch(2)
        self.setSizePolicy(size_policy)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_frame(self, frame):
        self.setText("")

        self.frame = frame
        self.update()

    def clear_overlay(self):
        self.overlay = None
        self.update()

    def display_camera_error(self):
        self.setText("Failed to start camera capture.")
        self.frame = None
        self.overlay = None
        self.update()

    def update_overlay(self, tracking_state: TrackingState):
        height, width, _ = self.frame.shape
        overlay = np.zeros((height, width, 4), np.uint8)

        if tracking_state.head.visible:
            landmarks = tracking_state.head.landmarks

            for i in range(len(CameraView.HEAD_CONTOUR_LANDMARK_INDICES)):
                a = CameraView.HEAD_CONTOUR_LANDMARK_INDICES[i]
                b = CameraView.HEAD_CONTOUR_LANDMARK_INDICES[(i + 1) % len(CameraView.HEAD_CONTOUR_LANDMARK_INDICES)]

                x1 = int(width * landmarks[a].x)
                y1 = int(height * landmarks[a].y)
                x2 = int(width * landmarks[b].x)
                y2 = int(height * landmarks[b].y)
                cv2.line(overlay, (x1, y1), (x2, y2), (0, 255, 0, 255), 2)

            for index in CameraView.HEAD_CONTOUR_LANDMARK_INDICES + CameraView.HEAD_OTHER_LANDMARK_INDICES:
                landmark = landmarks[index]
                x = int(width * landmark.x)
                y = int(height * landmark.y)
                cv2.circle(overlay, (x, y), 4, (255, 0, 0, 255), -1)

        # x = int(0.5 * width)
        # y = int(0.2 * height)
        # cv2.circle(new_overlay, (x, y), 8, (255, 255, 255, 255), -1)

        if tracking_state.left_hand.visible:
            x1 = int(LEFT_HAND_TRACKING_ORIGIN[0] * width)
            y1 = int(LEFT_HAND_TRACKING_ORIGIN[1] * height)
            x2 = int(width * tracking_state.left_hand.landmarks[0].x)
            y2 = int(height * tracking_state.left_hand.landmarks[0].y)
            cv2.line(overlay, (x1, y1), (x2, y2), (255, 255, 255, 255), 2)
            cv2.circle(overlay, (x1, y1), 8, (255, 255, 255, 255), -1)
        
        if tracking_state.right_hand.visible:
            x1 = int(RIGHT_HAND_TRACKING_ORIGIN[0] * width)
            y1 = int(RIGHT_HAND_TRACKING_ORIGIN[1] * height)
            x2 = int(width * tracking_state.right_hand.landmarks[0].x)
            y2 = int(height * tracking_state.right_hand.landmarks[0].y)
            cv2.line(overlay, (x1, y1), (x2, y2), (255, 255, 255, 255), 2)
            cv2.circle(overlay, (x1, y1), 8, (255, 255, 255, 255), -1)

        for hand_state in [tracking_state.left_hand, tracking_state.right_hand]:
            if not hand_state.visible:
                continue

            landmarks = hand_state.landmarks

            for a, b in solutions.hands_connections.HAND_CONNECTIONS:
                if hand_state.gesture is None:
                    color = (0, 255, 0, 255)
                elif hand_state.gesture == Gesture.PINCH:
                    color = (255, 255, 0, 255)
                elif hand_state.gesture == Gesture.PALM_PINCH:
                    color = (255, 0, 255, 255)
                elif hand_state.gesture == Gesture.MIDDLE_PINCH:
                    color = (0, 255, 255, 255)
                elif hand_state.gesture == Gesture.FIST:
                    color = (0, 0, 255, 255)

                x1 = int(width * landmarks[a].x)
                y1 = int(height * landmarks[a].y)
                x2 = int(width * landmarks[b].x)
                y2 = int(height * landmarks[b].y)
                cv2.line(overlay, (x1, y1), (x2, y2), color, 2)

            for landmark in landmarks:
                x = int(width * landmark.x)
                y = int(height * landmark.y)
                cv2.circle(overlay, (x, y), 4, (255, 0, 0, 255), -1)

        self.overlay = overlay
        self.update()

    def paintEvent(self, e: QPaintEvent):
        if self.frame is None:
            return super().paintEvent(e)

        canvas_width, canvas_height = self.width(), self.height()
        max_width = canvas_width - CameraView.MIN_IMAGE_PADDING
        max_height = canvas_height - CameraView.MIN_IMAGE_PADDING

        height, width, _ = self.frame.shape
        aspect_ratio = width / height

        if width > max_width:
            paint_width = max_width
            paint_height = paint_width / aspect_ratio
        elif height > max_height:
            paint_height = max_height
            paint_width = paint_height / aspect_ratio
        else:
            paint_width = width
            paint_height = height

        x = (canvas_width - paint_width) / 2
        y = (canvas_height - paint_height) / 2
        rect = QRect(x, y, paint_width, paint_height)

        painter = QPainter(self)

        image = QImage(self.frame, width, height, QImage.Format.Format_RGB888)
        painter.drawImage(rect, image)

        if self.overlay is not None:
            image = QImage(self.overlay, width, height, QImage.Format.Format_RGBA8888)
            painter.drawImage(rect, image)

        painter.end()

        return super().paintEvent(e)


class FrameView(QStackedWidget):
    
    class Status(Enum):
        DISCONNECTED = 0
        AWAITING_FRAME = 1
        PRESENTING = 2
        VULKAN_UNSUPPORTED = 3
        METAL_UNSUPPORTED = 4

    _set_status_signal = QtCore.Signal(Status)
    _connected_signal = QtCore.Signal()
    _disconnected_signal = QtCore.Signal()
    _present_image_signal = QtCore.Signal(PresentImageData)

    def __init__(self, connection: RuntimeConnection):
        super().__init__()

        self.status = FrameView.Status.DISCONNECTED
        self.surface_window = DisplaySurfaceWindow()
        self.surface = DisplaySurface()
        self.graphics_api = None

        self.info_widget = QLabel()
        self.info_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_widget.setStyleSheet("QLabel { color: white; background-color: #222222; }")

        self.addWidget(self.surface_window)
        self.addWidget(self.info_widget)
        self.setFixedWidth(640)
        self.setFixedHeight(640)

        self._set_status_signal.connect(self._set_status_slot)
        self._connected_signal.connect(self._connected_slot)
        self._disconnected_signal.connect(self._disconnected_slot)
        self._present_image_signal.connect(self._present_image_slot)

        connection.on_connected.subscribe(self._connected_signal.emit)
        connection.on_disconnected.subscribe(self._disconnected_signal.emit)
        connection.on_runtime_info.subscribe(self._on_runtime_info)
        connection.on_register_image.subscribe(self._register_image)
        connection.on_present_image.subscribe(self._present_image_signal.emit)

        self._set_status_signal.emit(FrameView.Status.DISCONNECTED)

    def _on_runtime_info(self, _: str, graphics_api: int):
        display = 0
        self.surface.create(graphics_api, display, self.surface_window.window_id)
        self.graphics_api = graphics_api

    def _register_image(self, data: RegisterImageData):
        self.surface.register_image(data)

    @QtCore.Slot(Status)
    def _set_status_slot(self, status: Status):
        if status == FrameView.Status.DISCONNECTED:
            self.info_widget.setText("No application connected.")
            self.setCurrentIndex(1)
        elif status == FrameView.Status.AWAITING_FRAME:
            self.info_widget.setText("Waiting for application to submit frames...")
            self.setCurrentIndex(1)
        elif status == FrameView.Status.PRESENTING:
            self.setCurrentIndex(0)
        elif status == FrameView.Status.VULKAN_UNSUPPORTED:
            self.info_widget.setText("Presenting Vulkan images is currently unsupported.")
            self.setCurrentIndex(1)
        elif status == FrameView.Status.METAL_UNSUPPORTED:
            self.info_widget.setText("Presenting Metal images is currently unsupported.")
            self.setCurrentIndex(1)

    @QtCore.Slot(PresentImageData)
    def _connected_slot(self):
        self._set_status_signal.emit(FrameView.Status.AWAITING_FRAME)

    @QtCore.Slot(PresentImageData)
    def _disconnected_slot(self):
        self._set_status_signal.emit(FrameView.Status.DISCONNECTED)

    @QtCore.Slot(PresentImageData)
    def _present_image_slot(self, data: PresentImageData):
        if self.graphics_api == 0:
            self._set_status_signal.emit(FrameView.Status.VULKAN_UNSUPPORTED)
        elif self.graphics_api == 1:
            self._set_status_signal.emit(FrameView.Status.PRESENTING)
            self.surface.present_image(data)
        elif self.graphics_api == 2:
            self._set_status_signal.emit(FrameView.Status.METAL_UNSUPPORTED)


class DisplaySurfaceWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.window_id = self.winId()
    
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.WinIdChange:
            self.window_id = self.winId()
        
        return super().event(event)


class StatusBar(QLabel):

    OPENCOMPOSITE_PREFIX = "OpenComposite_"

    _build_signal = QtCore.Signal()

    def __init__(self, connection: RuntimeConnection):
        super().__init__()

        self._build_signal.connect(self.build)

        self.connection = connection
        self.connection.on_connected.subscribe(lambda: self.set_state(True))
        self.connection.on_disconnected.subscribe(lambda: self.set_state(False))
        self.connection.on_runtime_info.subscribe(self.update_runtime_info)

        self.connected = False
        self.application_name = None
        self.graphics_api = None
        self.build()

    def set_state(self, connected: bool):
        self.connected = connected

        if not connected:
            self.application_name = None
            self.graphics_api = None

        self._build_signal.emit()

    def update_runtime_info(self, application_name: str, graphics_api: int):
        self.application_name = application_name
        self.graphics_api = graphics_api

        self._build_signal.emit()

    @QtCore.Slot()
    def build(self):
        if self.connected:
            text = "Connected"
            color = "#098226"
        else:
            text = "Disconnected"
            color = "#636363"
        
        if self.application_name is not None:
            text += " | "
            
            if self.application_name.startswith(StatusBar.OPENCOMPOSITE_PREFIX):
                text += self.application_name[len(StatusBar.OPENCOMPOSITE_PREFIX):]
                text += " (OpenComposite)"
            else:
                text += self.application_name

        if self.graphics_api is not None:
            text += " | "

            if self.graphics_api == 0:
                text += "Vulkan"
            elif self.graphics_api == 1:
                text += "Direct3D 11"
            elif self.graphics_api == 2:
                text += "Metal"
            else:
                text += "Unknown Graphics API"

        self.setText(text)
        self.setStyleSheet("QLabel { color: white; background-color: " + color + "; }")


class DownloadDialog(QDialog):

    _close_signal = QtCore.Signal()
    _close_with_error_signal = QtCore.Signal(str)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setWindowTitle("MediaPipe Model Download")
        self.setFixedWidth(480)

        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(0)
        progress_bar.setValue(0)
        progress_bar.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Downloading MediaPipe models..."))
        layout.addWidget(progress_bar)
        self.setLayout(layout)

        self._close_signal.connect(self._close_slot)
        self._close_with_error_signal.connect(self._close_with_error_slot)

    def close_remotely(self):
        self._close_signal.emit()

    def close_with_error_remotely(self, message: str):
        self._close_with_error_signal.emit(message)

    @QtCore.Slot()
    def _close_slot(self):
        self.close()

    @QtCore.Slot()
    def _close_with_error_slot(self, message: str):
        text = "Failed to download MediaPipe ML models.\n\nMessage: " + message
        QMessageBox.critical(self, "Error", text)
        self.close()


class GUI:

    def __init__(
        self,
        config: Config,
        system_openxr_config: SystemOpenXRConfig,
        connection: RuntimeConnection,
        camera_capture: CameraCapture,
        camera_capture2: CameraCapture2,
    ):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLESHEET)

        self.window = Window(config, system_openxr_config, connection, camera_capture, camera_capture2)
        self.window.show()

    def show_download_dialog(self, on_download) -> bool:
        return self.window.show_download_dialog(on_download)

    def update_camera_frame(self, frame):
        self.window.update_camera_frame(frame)

    def update_camera_overlay(self, tracking_state: TrackingState):
        self.window.update_camera_overlay(tracking_state)

    def clear_camera_overlay(self):
        self.window.clear_camera_overlay()

    def display_camera_error(self):
        self.window.display_camera_error()

    def run(self):
        self.app.exec()
    
    def close(self):
        self.window.close()

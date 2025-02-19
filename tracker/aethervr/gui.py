import sys

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
from aethervr import platform


STYLESHEET = """
.CameraView {

}

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
    ):
        super().__init__()

        self.config = config
        self.system_openxr_config = system_openxr_config
        self.connection = connection
        self.camera_capture = camera_capture

        self.camera_view = None
        self.frame_view = None

        self.setWindowTitle("AetherVR Tracker")
        self.resize(QSize(1280, 720))

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
        layout.addWidget(ConfigPanel(self.config, self.system_openxr_config, self.camera_capture))
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

    def update_camera_frame(self, frame):
        self.camera_view.update_frame(frame)

    def update_camera_overlay(self, tracking_state: TrackingState):
        self.camera_view.update_overlay(tracking_state)

    def clear_camera_overlay(self):
        self.camera_view.clear_overlay()


class ConfigPanel(QWidget):

    def __init__(
        self,
        config: Config,
        system_openxr_config: SystemOpenXRConfig,
        camera_capture: CameraCapture,
    ):
        super().__init__()
        self.config = config

        layout = QVBoxLayout()
        layout.addWidget(OpenXRConfigGroup(system_openxr_config))
        layout.addWidget(TrackingConfigGroup(config, camera_capture))
        layout.addWidget(GeneralInputMappingGroup(config))
        layout.addWidget(self._build_controller_group("Left Controller", config.left_controller_config))
        layout.addWidget(self._build_controller_group("Right Controller", config.right_controller_config))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        self.setMinimumWidth(320)

    def _build_controller_group(self, label: str, config: ControllerConfig):
        group = QGroupBox(label)

        press_thumbstick_checkbox = QCheckBox("Press Thumbstick During Use")
        press_thumbstick_checkbox.setChecked(config.press_thumbstick)
        press_thumbstick_checkbox.checkStateChanged.connect(lambda value: ConfigPanel._on_press_thumbstick_changed(config, value))

        layout = QFormLayout()
        layout.addRow("Pinch:", ButtonBindingDropdown(config, Gesture.PINCH))
        layout.addRow("Palm Pinch:", ButtonBindingDropdown(config, Gesture.PALM_PINCH))
        layout.addRow("Middle Pinch:", MiddlePinchBindingDropdown(config))
        layout.addRow("Fist:", ButtonBindingDropdown(config, Gesture.FIST))
        layout.addRow(press_thumbstick_checkbox)
        group.setLayout(layout)

        return group
    
    def _on_press_thumbstick_changed(config: ControllerConfig, state: Qt.CheckState):
        config.press_thumbstick = state == Qt.CheckState.Checked


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

        layout = QFormLayout()
        layout.addRow(QLabel("Current OpenXR Runtime:"), self.current_label)
        layout.addRow(self.incompatible_label)
        layout.addRow(self.set_button)
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

    def __init__(self, config: Config, camera_capture: CameraCapture):
        super().__init__("Tracking")

        self.config = config
        self.camera_capture = camera_capture

        self.tracking_label = QLabel()
        self.tracking_button = QPushButton()
        self.tracking_button.clicked.connect(self.on_tracking_button_clicked)

        self.camera_index_input = QComboBox()
        self.camera_index_input.addItem("Camera 0")
        self.camera_index_input.addItem("Camera 1")
        self.camera_index_input.addItem("Camera 2")
        self.camera_index_input.addItem("Camera 3")
        self.camera_index_input.addItem("Camera 4")
        self.camera_index_input.currentIndexChanged.connect(self.on_capture_config_changed)

        self.frame_width_input = QLineEdit("640")
        self.frame_width_input.setFixedWidth(80)
        self.frame_width_input.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.frame_width_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_width_input.editingFinished.connect(self.on_capture_config_changed)

        self.frame_height_input = QLineEdit("640")
        self.frame_height_input.setFixedWidth(80)
        self.frame_height_input.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.frame_height_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_height_input.editingFinished.connect(self.on_capture_config_changed)

        camera_resolution_x_label = QLabel("x")
        camera_resolution_x_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_resolution_x_label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))

        camera_resolution_row = QHBoxLayout()
        camera_resolution_row.addWidget(self.frame_width_input)
        camera_resolution_row.addWidget(camera_resolution_x_label)
        camera_resolution_row.addWidget(self.frame_height_input)

        self.fps_input = QLineEdit()
        self.fps_input.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.fps_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_input.editingFinished.connect(self.on_fps_input_changed)

        layout = QFormLayout()
        layout.addRow(self.tracking_label, self.tracking_button)
        layout.addRow("Camera Index:", self.camera_index_input)
        layout.addRow("Camera Resolution:", camera_resolution_row)
        layout.addRow("Max. Frames per Second:", self.fps_input)
        self.setLayout(layout)

        self.update_tracking_status()
        self.update_capture_config_inputs()
        self.update_fps_input()

    def on_tracking_button_clicked(self):
        self.config.tracking_running = not self.config.tracking_running
        self.update_tracking_status()

    def on_capture_config_changed(self):
        self.config.capture_config.camera_index = self.camera_index_input.currentIndex()
        
        try:
            value = int(self.frame_width_input.text())
            value = max(value, 320)
            self.config.capture_config.frame_width = value
        except ValueError:
            pass

        try:
            value = int(self.frame_height_input.text())
            value = max(value, 320)
            self.config.capture_config.frame_height = value
        except ValueError:
            pass
        
        self.camera_capture.restart()
        self.update_capture_config_inputs()

    def on_fps_input_changed(self):
        try:
            value = int(self.fps_input.text())
            
            if value > 0:
                self.config.tracking_fps_cap = value
        except ValueError:
            pass

        self.update_fps_input()

    def update_tracking_status(self):
        if self.config.tracking_running:
            self.tracking_label.setText('Status: Running')
            self.tracking_button.setText("Stop")
        else:
            self.tracking_label.setText("Status: Stopped")
            self.tracking_button.setText("Start")

    def update_capture_config_inputs(self):
        self.camera_index_input.setCurrentIndex(self.config.capture_config.camera_index)
        self.frame_width_input.setText(str(self.config.capture_config.frame_width))
        self.frame_height_input.setText(str(self.config.capture_config.frame_height))

    def update_fps_input(self):
        self.fps_input.setText(str(self.config.tracking_fps_cap))


class GeneralInputMappingGroup(QGroupBox):

    def __init__(self, config: Config):
        super().__init__("General Input Mapping")

        self.config = config

        set_controller_rotation_button = QPushButton("Set Controller Rotation")
        set_controller_rotation_button.clicked.connect(self._show_controller_rotation_dialog)

        layout = QFormLayout()
        layout.addRow(set_controller_rotation_button)
        self.setLayout(layout)

    def _show_controller_rotation_dialog(self):
        dialog = ControllerRotationDialog(self.config)
        dialog.show()


class ControllerRotationDialog(QDialog):

    def __init__(self, config: Config):
        super().__init__()

        self.config = config

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Controller Rotation")
        self.setMinimumWidth(360)        

        layout = QGridLayout()
        layout.addWidget(QLabel("Pitch:"), 0, 0)
        layout.addWidget(AngleSlider(config.controller_pitch, self._update_pitch), 0, 1)
        layout.addWidget(QLabel("Yaw:"), 1, 0)
        layout.addWidget(AngleSlider(config.controller_yaw, self._update_yaw), 1, 1)
        layout.addWidget(QLabel("Roll:"), 2, 0)
        layout.addWidget(AngleSlider(config.controller_roll, self._update_roll), 2, 1)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        self.setLayout(layout)

    def _update_pitch(self, pitch: float):
        self.config.controller_pitch = pitch

    def _update_yaw(self, yaw: float):
        self.config.controller_yaw = yaw

    def _update_roll(self, roll: float):
        self.config.controller_roll = roll


class AngleSlider(QWidget):

    def __init__(self, initial_angle: float, on_angle_changed):
        super().__init__()

        self.angle = int(initial_angle)
        self.on_angle_changed = on_angle_changed

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        slider.setMinimum(-12)
        slider.setMaximum(12)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(3)
        slider.valueChanged.connect(self._on_value_changed)

        self.label = QLabel()
        self.label.setFixedWidth(30)
        self.label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QHBoxLayout()
        layout.addWidget(slider)
        layout.addWidget(self.label)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.setLayout(layout)

        self._update_label()

    def _on_value_changed(self, value: int):
        self.angle = 15 * value
        self.on_angle_changed(float(self.angle))
        self._update_label()

    def _update_label(self):
        self.label.setText(f"{self.angle}°")


class ButtonBindingDropdown(QComboBox):

    def __init__(self, config: ControllerConfig, gesture: Gesture):
        super().__init__()
        self.config = config
        self.gesture = gesture

        initial_value = config.gesture_mappings[gesture]

        self.addItem("Trigger", ControllerButton.TRIGGER)
        self.addItem("Squeeze", ControllerButton.SQUEEZE)
        self.addItem("A", ControllerButton.A_BUTTON)
        self.addItem("B", ControllerButton.B_BUTTON)
        self.addItem("X", ControllerButton.X_BUTTON)
        self.addItem("Y", ControllerButton.Y_BUTTON)
        self.addItem("Menu", ControllerButton.MENU)
        self.addItem("System", ControllerButton.SYSTEM)
        self.setCurrentIndex(self.findData(initial_value))

        self.currentIndexChanged.connect(self.on_selected)

    def on_selected(self, index: int):
        button = self.itemData(index)
        self.config.gesture_mappings[self.gesture] = button


class MiddlePinchBindingDropdown(QComboBox):

    def __init__(self, config: ControllerConfig):
        super().__init__()
        self.config = config

        initial_value = config.thumbstick_enabled

        self.addItem("None", False)
        self.addItem("Thumbstick", True)
        self.setCurrentIndex(self.findData(initial_value))

        self.currentIndexChanged.connect(self.on_selected)

    def on_selected(self, index: int):
        value = self.itemData(index)
        self.config.thumbstick_enabled = value


class CameraView(QLabel):

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

    def update_overlay(self, tracking_state: TrackingState):
        height, width, _ = self.frame.shape
        self.overlay = np.zeros((height, width, 4), np.uint8)

        if tracking_state.head.visible:
            x = int(0.5 * width)
            y = int(0.2 * height)
            cv2.circle(self.overlay, (x, y), 8, (255, 255, 255, 255), -1)

        if tracking_state.left_hand.visible:
            x1 = int(LEFT_HAND_TRACKING_ORIGIN[0] * width)
            y1 = int(LEFT_HAND_TRACKING_ORIGIN[1] * height)
            x2 = int(width * tracking_state.left_hand.landmarks[0].x)
            y2 = int(height * tracking_state.left_hand.landmarks[0].y)
            cv2.line(self.overlay, (x1, y1), (x2, y2), (255, 255, 255, 255), 2)
            cv2.circle(self.overlay, (x1, y1), 8, (255, 255, 255, 255), -1)
        if tracking_state.right_hand.visible:
            x1 = int(RIGHT_HAND_TRACKING_ORIGIN[0] * width)
            y1 = int(RIGHT_HAND_TRACKING_ORIGIN[1] * height)
            x2 = int(width * tracking_state.right_hand.landmarks[0].x)
            y2 = int(height * tracking_state.right_hand.landmarks[0].y)
            cv2.line(self.overlay, (x1, y1), (x2, y2), (255, 255, 255, 255), 2)
            cv2.circle(self.overlay, (x1, y1), 8, (255, 255, 255, 255), -1)

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
                cv2.line(self.overlay, (x1, y1), (x2, y2), color, 2)

            for landmark in landmarks:
                x = int(width * landmark.x)
                y = int(height * landmark.y)
                cv2.circle(self.overlay, (x, y), 4, (255, 0, 0, 255), -1)

        self.update()

    def paintEvent(self, e: QPaintEvent):
        if self.frame is None:
            return super().paintEvent(e)

        canvas_width, canvas_height = self.width(), self.height()

        height, width, _ = self.frame.shape
        x = (canvas_width - width) / 2
        y = (canvas_height - height) / 2
        rect = QRect(x, y, width, height)

        painter = QPainter(self)

        image = QImage(self.frame, width, height, QImage.Format.Format_RGB888)
        painter.drawImage(rect, image)

        if self.overlay is not None:
            image = QImage(self.overlay, width, height, QImage.Format.Format_RGBA8888)
            painter.drawImage(rect, image)

        painter.end()

        return super().paintEvent(e)


class FrameView(QLabel):
    
    _present_image_signal = QtCore.Signal(PresentImageData)

    def __init__(self, connection: RuntimeConnection):
        super().__init__()

        self.window_id = self.winId()
        self.surface = DisplaySurface()
        self.image_data = None

        self.setFixedWidth(640)
        self.setFixedHeight(640)

        self._present_image_signal.connect(self._present_image_slot)

        connection.on_runtime_info.subscribe(self._on_runtime_info)
        connection.on_register_image.subscribe(self._register_image)
        connection.on_present_image.subscribe(self._present_image_signal.emit)
    
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.WinIdChange:
            self.window_id = self.winId()
        
        return super().event(event)

    def _on_runtime_info(self, _: str, graphics_api: int):
        native_interface = QApplication.instance().nativeInterface()

        if platform.is_linux:
            display = native_interface.display()
        else:
            display = 0

        self.surface.create(graphics_api, display, self.window_id)

    def _register_image(self, data: RegisterImageData):
        self.surface.register_image(data)

    @QtCore.Slot(PresentImageData)
    def _present_image_slot(self, data: PresentImageData):
        self.surface.present_image(data)


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
            color = "#00a426"
        else:
            text = "Disconnected"
            color = "#575757"
        
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
        self.setStyleSheet("QLabel { background-color: " + color + "; }")


class GUI:

    def __init__(
        self,
        config: Config,
        system_openxr_config: SystemOpenXRConfig,
        connection: RuntimeConnection,
        camera_capture: CameraCapture,
    ):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLESHEET)

        self.window = Window(config, system_openxr_config, connection, camera_capture)
        self.window.show()

    def update_camera_frame(self, frame):
        self.window.update_camera_frame(frame)

    def update_camera_overlay(self, tracking_state: TrackingState):
        self.window.update_camera_overlay(tracking_state)

    def clear_camera_overlay(self):
        self.window.clear_camera_overlay()

    def run(self):
        self.app.exec()

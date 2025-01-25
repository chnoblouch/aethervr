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
)

from PySide6.QtCore import QEvent, Qt, QSize, QEvent, QRect, QTimer
from PySide6.QtGui import QPaintEvent, QColor, QPainter, QBrush, QImage
from mediapipe import solutions
import numpy as np
import cv2

from aethervr.config import *
from aethervr.tracking_state import TrackingState
from aethervr.input_state import ControllerButton
from aethervr.runtime_connection import RuntimeConnection
from aethervr.system_openxr_config import SystemOpenXRConfig
from aethervr.display_surface import DisplaySurface


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

    def __init__(self, config: Config, connection: RuntimeConnection, system_openxr_config: SystemOpenXRConfig):
        super().__init__()
        self.config = config
        self.connection = connection
        self.system_openxr_config = system_openxr_config

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
        self.frame_view = FrameView()

        self.connection.on_register_image = self.frame_view.register_image
        self.connection.on_present_image = self.frame_view.present_image

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
        layout.addWidget(ConfigPanel(self.config, self.system_openxr_config))
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


class ConfigPanel(QWidget):

    def __init__(self, config: Config, system_openxr_config: SystemOpenXRConfig):
        super().__init__()
        self.config = config

        layout = QVBoxLayout()
        layout.addWidget(OpenXRConfigGroup(system_openxr_config))
        layout.addWidget(self._build_tracking_group(config))
        layout.addWidget(self._build_controller_group("Left Controller", config.left_controller_config))
        layout.addWidget(self._build_controller_group("Right Controller", config.right_controller_config))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        self.setMinimumWidth(320)

    def _build_tracking_group(self, config: Config):
        group = QGroupBox("Tracking")

        fps_input = QLineEdit()
        fps_input.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Ignored))

        layout = QFormLayout()
        layout.addRow(QLabel("Max. Frames per Second:"), fps_input)
        group.setLayout(layout)

        def update_fps_input():
            fps_input.setText(str(config.tracking_fps_cap))

        def on_fps_input_changed():
            try:
                value = int(fps_input.text())
                
                if value > 0:
                    config.tracking_fps_cap = value
            except ValueError:
                pass

            update_fps_input()

        update_fps_input()
        fps_input.editingFinished.connect(on_fps_input_changed)

        return group

    def _build_controller_group(self, label: str, config: ControllerConfig):
        group = QGroupBox(label)

        layout = QFormLayout()
        layout.addRow(QLabel("Pinch:"), ButtonBindingDropdown(config, Gesture.PINCH))
        layout.addRow(QLabel("Palm Pinch:"), ButtonBindingDropdown(config, Gesture.PALM_PINCH))
        layout.addRow(QLabel("Fist:"), ButtonBindingDropdown(config, Gesture.FIST))
        group.setLayout(layout)

        return group


class OpenXRConfigGroup(QGroupBox):

    def __init__(self, system_openxr_config: SystemOpenXRConfig):
        super().__init__("OpenXR")
        self.system_openxr_config = system_openxr_config

        self.current_label = QLabel()

        self.set_button = QPushButton("Set AetherVR as OpenXR Runtime")
        self.set_button.clicked.connect(self._activate_aethervr)

        layout = QFormLayout()
        layout.addRow(QLabel("Current OpenXR Runtime:"), self.current_label)
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
                + "Please make sure you're running AetherVR as an administrator.",
            )

    def _refresh(self):
        active_runtime = self.system_openxr_config.active_runtime_name()
        is_aethervr = self.system_openxr_config.is_aethervr(active_runtime)

        self.current_label.setText("None" if active_runtime is None else active_runtime)
        self.set_button.setEnabled(not is_aethervr)


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


class CameraView(QLabel):

    def __init__(self):
        super().__init__()

        self.frame = None
        self.overlay = None

        size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )

        size_policy.setHorizontalStretch(2)
        self.setSizePolicy(size_policy)

    def update_frame(self, frame):
        self.frame = frame
        self.update()

    def update_overlay(self, tracking_state: TrackingState):
        height, width, _ = self.frame.shape
        self.overlay = np.zeros((height, width, 4), np.uint8)

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
                elif hand_state.gesture == Gesture.FIST:
                    color = (0, 0, 255, 255)
                elif hand_state.gesture == Gesture.USING_THUMBSTICK:
                    color = (0, 255, 255, 255)

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

    def __init__(self):
        super().__init__()

        self.surface = DisplaySurface(self.winId())
        self.image_id = None

        self.setFixedWidth(640)
        self.setFixedHeight(640)
    
    def register_image(self, image_id: int, process_id: int, texture_handle: int):
        self.surface.register_image(image_id, process_id, texture_handle)

    def present_image(self, image_id: int):
        self.image_id = image_id
        self.update()

    def paintEvent(self, e: QPaintEvent):
        if self.image_id is not None:
            self.surface.present_image(self.image_id)


class StatusBar(QLabel):

    OPENCOMPOSITE_PREFIX = "OpenComposite_"

    def __init__(self, connection: RuntimeConnection):
        super().__init__()

        self.connection = connection
        self.connection.on_connected = lambda: self.set_state(True)
        self.connection.on_disconnected = lambda: self.set_state(False)
        self.connection.on_runtime_info = self.update_runtime_info

        self.connected = False
        self.application_name = None
        self.graphics_api = None
        self.build()

    def set_state(self, connected: bool):
        self.connected = connected

        if not connected:
            self.application_name = None
            self.graphics_api = None

        self.build()

    def update_runtime_info(self, application_name: str, graphics_api: int):
        self.application_name = application_name
        self.graphics_api = graphics_api
        self.build()

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

    def __init__(self, config: Config, connection: RuntimeConnection, system_openxr_config: SystemOpenXRConfig):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLESHEET)

        self.window = Window(config, connection, system_openxr_config)
        self.window.show()

    def update_camera_frame(self, frame):
        self.window.update_camera_frame(frame)

    def update_camera_overlay(self, tracking_state: TrackingState):
        self.window.update_camera_overlay(tracking_state)

    def run(self):
        self.app.exec()

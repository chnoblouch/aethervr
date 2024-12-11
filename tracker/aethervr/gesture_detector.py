import math

from aethervr.tracking_state import TrackingState, HandState
from aethervr.input_state import InputState, ControllerState, ControllerButton
from aethervr.config import Config, ControllerConfig, Gesture


class GestureDetector:

    def __init__(self, config: Config, tracking_state: TrackingState, input_state: InputState):
        self.config = config
        self.tracking_state = tracking_state
        self.input_state = input_state

    def detect(self):
        GestureDetector.detect_on_hand(
            self.config.left_controller_config,
            self.tracking_state.left_hand,
            self.input_state.left_controller_state,
            False,
        )

        GestureDetector.detect_on_hand(
            self.config.right_controller_config,
            self.tracking_state.right_hand,
            self.input_state.right_controller_state,
            True,
        )

    @staticmethod
    def detect_on_hand(
        config: ControllerConfig,
        tracking_state: HandState,
        input_state: ControllerState,
        flipped: bool,
    ):
        input_state.buttons = {button: False for button in ControllerButton}

        if not tracking_state.visible:
            return

        if GestureDetector.is_fist(tracking_state.landmarks):
            tracking_state.gesture = Gesture.FIST
        elif GestureDetector.is_pinching(tracking_state.landmarks):
            if GestureDetector.is_front_facing(tracking_state.landmarks, flipped):
                tracking_state.gesture = Gesture.PINCH
            else:
                tracking_state.gesture = Gesture.PALM_PINCH
        else:
            tracking_state.gesture = None

        if tracking_state.gesture:
            mapping = config.gesture_mappings.get(tracking_state.gesture)

            if mapping is not None:
                input_state.buttons[mapping] = True

    @staticmethod
    def is_pinching(landmarks):
        tip1 = landmarks[4]
        tip2 = landmarks[8]
        return math.sqrt((tip2.x - tip1.x) ** 2 + (tip2.y - tip1.y) ** 2) < 0.06

    @staticmethod
    def is_fist(landmarks):
        tip = landmarks[12]
        wrist = landmarks[0]
        return math.sqrt((tip.x - wrist.x) ** 2 + (tip.y - wrist.y) ** 2) < 0.15

    @staticmethod
    def is_front_facing(landmarks, flipped: bool):
        result = landmarks[5].x - landmarks[17].x > 0
        return result if not flipped else not result

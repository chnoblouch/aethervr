import math

from aethervr.tracking_state import TrackingState, HandState, Gesture
from aethervr.input_state import InputState, ControllerState, ControllerButton
from aethervr.config import Config, ControllerConfig


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
        input_state.thumbstick_x = 0.0
        input_state.thumbstick_y = 0.0

        if not tracking_state.visible:
            return

        if GestureDetector.is_fist(tracking_state):
            tracking_state.gesture = Gesture.FIST
        elif GestureDetector.is_pinching(tracking_state):
            if GestureDetector.is_front_facing(tracking_state.landmarks, flipped):
                tracking_state.gesture = Gesture.PINCH
            else:
                tracking_state.gesture = Gesture.PALM_PINCH
        elif GestureDetector.is_middle_pinching(tracking_state):
            tracking_state.gesture = Gesture.MIDDLE_PINCH

            if config.thumbstick_enabled:
                if input_state.jostick_center is None:
                    input_state.jostick_center = tracking_state.position
                else:
                    dx = tracking_state.position.x - input_state.jostick_center.x
                    dy = -(tracking_state.position.z - input_state.jostick_center.z)
                    d = math.sqrt(dx * dx + dy * dy)

                    if d >= 0.075:
                        input_state.thumbstick_x = dx / d
                        input_state.thumbstick_y = dy / d
                    else:
                        input_state.thumbstick_x = 0.0
                        input_state.thumbstick_y = 0.0

                if config.press_thumbstick:
                    input_state.buttons[ControllerButton.THUMBSTICK] = True
        else:
            tracking_state.gesture = None

        if tracking_state.gesture:
            mapping = config.gesture_mappings.get(tracking_state.gesture)

            if mapping is not None:
                input_state.buttons[mapping] = True
        else:
            input_state.jostick_center = None

    @staticmethod
    def is_pinching(tracking_state: HandState):
        tip1 = tracking_state.landmarks[4]
        tip2 = tracking_state.landmarks[8]
        max_distance = 0.1 if tracking_state.previous_gesture == Gesture.PINCH else 0.06
        return GestureDetector.calc_distance(tip1, tip2) < max_distance

    @staticmethod
    def is_middle_pinching(tracking_state: HandState):
        tip1 = tracking_state.landmarks[4]
        tip2 = tracking_state.landmarks[12]
        max_distance = 0.1 if tracking_state.previous_gesture == Gesture.MIDDLE_PINCH else 0.06
        return GestureDetector.calc_distance(tip1, tip2) < max_distance

    @staticmethod
    def is_fist(tracking_state: HandState):
        tip0 = tracking_state.landmarks[4]
        tip1 = tracking_state.landmarks[8]
        tip2 = tracking_state.landmarks[12]
        tip3 = tracking_state.landmarks[16]
        tip4 = tracking_state.landmarks[20]
        wrist = tracking_state.landmarks[0]

        return (
            GestureDetector.calc_distance(tip0, wrist) < 0.25
            and GestureDetector.calc_distance(tip1, wrist) < 0.25
            and GestureDetector.calc_distance(tip2, wrist) < 0.15
            and GestureDetector.calc_distance(tip3, wrist) < 0.25
            and GestureDetector.calc_distance(tip4, wrist) < 0.25
        )

    @staticmethod
    def calc_distance(landmark_a, landmark_b):
        return math.sqrt((landmark_a.x - landmark_b.x) ** 2 + (landmark_a.y - landmark_b.y) ** 2)

    @staticmethod
    def is_front_facing(landmarks, flipped: bool):
        result = landmarks[5].x - landmarks[17].x > 0
        return result if not flipped else not result

import cv2

from aether.head_tracker import HeadTracker
from aether.hand_tracker import HandTracker
from aether.runtime_connection import RuntimeConnection, Keys


head_tracker = None
hand_tracker = None
connection = None
capture = None


def process_head_tracking_results(results):
    connection.set_state(Keys.HEAD_PITCH, float(results.pitch))
    connection.set_state(Keys.HEAD_YAW, -float(results.yaw))

    connection.set_state(Keys.HEAD_X, results.position.x)
    connection.set_state(Keys.HEAD_Y, results.position.y)
    connection.set_state(Keys.HEAD_Z, results.position.z)


def process_hand_tracking_results(results):
    connection.set_state(Keys.LEFT_HAND_ORIENTATION_X, results.left.orientation.x)
    connection.set_state(Keys.LEFT_HAND_ORIENTATION_Y, results.left.orientation.y)
    connection.set_state(Keys.LEFT_HAND_ORIENTATION_Z, results.left.orientation.z)
    connection.set_state(Keys.LEFT_HAND_ORIENTATION_W, results.left.orientation.w)
    connection.set_state(Keys.LEFT_HAND_SELECT, results.left.select)

    connection.set_state(Keys.LEFT_HAND_POSITION_X, results.left.position.x)
    connection.set_state(Keys.LEFT_HAND_POSITION_Y, results.left.position.y)
    connection.set_state(Keys.LEFT_HAND_POSITION_Z, results.left.position.z)

    connection.set_state(Keys.RIGHT_HAND_ORIENTATION_X, results.right.orientation.x)
    connection.set_state(Keys.RIGHT_HAND_ORIENTATION_Y, results.right.orientation.y)
    connection.set_state(Keys.RIGHT_HAND_ORIENTATION_Z, results.right.orientation.z)
    connection.set_state(Keys.RIGHT_HAND_ORIENTATION_W, results.right.orientation.w)
    connection.set_state(Keys.RIGHT_HAND_SELECT, results.right.select)

    connection.set_state(Keys.RIGHT_HAND_POSITION_X, results.right.position.x)
    connection.set_state(Keys.RIGHT_HAND_POSITION_Y, results.right.position.y)
    connection.set_state(Keys.RIGHT_HAND_POSITION_Z, results.right.position.z)


def run():
    global head_tracker, hand_tracker, connection, capture, frame

    head_tracker = HeadTracker(detection_callback=process_head_tracking_results)
    hand_tracker = HandTracker(detection_callback=process_hand_tracking_results)

    print("Opening capture device...")

    capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not capture.isOpened():
        print("Failed to open capture device")
        exit(1)

    print("Capture device opened")

    connection = RuntimeConnection(38057)
    connection.run()

    while capture.isOpened():
        try:
            ret, frame = capture.read()
            if not ret:
                raise Exception()

            cv2.flip(frame, 1, frame)

            mp_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            head_tracker.detect(mp_frame)
            hand_tracker.detect(mp_frame)
            hand_tracker.draw(frame)

            cv2.imshow("AetherVR Tracker", frame)

            if cv2.waitKey(1) == 27:
                break
        except KeyboardInterrupt:
            print("Interrupt received")
            break
        except Exception as e:
            print(e)
            break

    connection.close()
    head_tracker.close()
    hand_tracker.close()
    capture.release()
    print("Capture device closed")
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()

import cv2

from aether.head_tracker import HeadTracker
from aether.hand_tracker import HandTracker
from aether.runtime_connection import RuntimeConnection


head_tracker = None
hand_tracker = None
connection = None
capture = None


def process_head_tracking_results(results):
    connection.lock.acquire()

    connection.state.head.position = results.position
    connection.state.head.pitch = float(results.pitch)
    connection.state.head.yaw = -float(results.yaw)

    connection.lock.release()


def process_hand_tracking_results(results):
    connection.lock.acquire()

    connection.state.left_hand.add_snapshot(results.left.position, results.left.orientation)
    connection.state.left_hand.pinching = results.left.select

    connection.state.right_hand.add_snapshot(results.right.position, results.right.orientation)
    connection.state.right_hand.pinching = results.right.select

    connection.lock.release()


def run():
    global head_tracker, hand_tracker, connection, capture, frame

    head_tracker = HeadTracker(detection_callback=process_head_tracking_results)
    hand_tracker = HandTracker(head_tracker, detection_callback=process_hand_tracking_results)

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

            key = cv2.waitKey(1)
            if key == 27:
                break
            elif key == ord('c'):
                head_tracker.calibrate_next_frame = True
            
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

import rclpy
import time

from picamera2 import Picamera2
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class CameraNode(Node):
    def __init__(self):
        super().__init__("camera_node")

        COOLDOWN_S = 5.5

        self.publisher = self.create_publisher(
            Image,
            "/camera/image",
            10,
        )

        self.bridge = CvBridge()
        self.camera = Picamera2()

        config = self.camera.create_video_configuration(
            main={
                "size": (640, 480),
                "format": "RGB888"
            }
        )

        self.camera.configure(config)
        self.camera.start()
        time.sleep(1)

        self.timer = self.create_timer(
            COOLDOWN_S, self.publish_frame
        )

    def publish_frame(self):
        frame = self.camera.capture_array()
        msg = self.bridge.cv2_to_imgmsg(
            frame, encoding="rgb8"
        )

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera"

        self.publisher.publish(msg)
        self.get_logger().info(f"Published camera frame")

    def destroy_node(self):
        self.camera.stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    node = CameraNode()

    try:
        print("RUNNING: Camera Node")
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nProgram stopped safely by the user")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        print("Cleaned resources and exited")


if __name__ == "__main__":
    main()
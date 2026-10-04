import argparse
import cv2
import rclpy

from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class TestVisualLocalizationNode(Node):
    """
    TEST CLASS
    ==========
    Integration test:
    This test class mocks a camera by constantly reading an image file.
    This class is meant to check ROS implementation works as expected.
    """
    def __init__(self, pi: bool = False):
        super().__init__("test_visual_localization_node")

        if pi:
            # Takes ~5 seconds to process image on pi4
            COOLDOWN_S = 5.5
        else:
            COOLDOWN_S = 1.0

        self.publisher = self.create_publisher(
            Image,
            "/camera/image",
            10,
        )

        self.bridge = CvBridge()

        self.image = cv2.imread("data/query4.png")

        if self.image is None:
            raise FileExistsError("Could not load image")

        self.timer = self.create_timer(
            COOLDOWN_S,
            self.publish_image
        )

    def publish_image(self):
        msg = self.bridge.cv2_to_imgmsg(
            self.image,
            encoding="bgr8",
        )

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera"

        self.publisher.publish(msg)
        self.get_logger().info("Published test image")


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pi",
        action="store_true",
        help="Run in Raspberry Pi mode",
    )

    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)

    node = TestVisualLocalizationNode(pi=args.pi)

    print(f"RUNNING TEST ... pi={args.pi}")

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nProgram stopped safely by the user")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        print("Cleaned resources and exited")


if __name__ == "__main__":
    main()

import rclpy

from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from omegaconf.dictconfig import DictConfig
from px4_msgs.msg import VehicleGlobalPosition

from src.database.tile_db_manager import TileDatabaseManager
from src.inference.localizer import EstimatedGeoPosition, Localizer
from src.utils.config import load_config


class VisualLocalizationNode(Node):
    def __init__(
        self,
        model_config: DictConfig,
        preprocessing_config: DictConfig
    ):
        super().__init__("visual_localization_node")
        self.bridge = CvBridge()

        self.db_manager = TileDatabaseManager(
            db_path=preprocessing_config.output.db,
            faiss_path=preprocessing_config.output.faiss,
            embedding_dim=model_config.model.embedding_dim,
        )

        self.localizer = Localizer(
            model_config,
            self.db_manager,
        )

        self.subscription = self.create_subscription(
            Image,                      # message type
            "/camera/image",            # listen to this
            self.image_callback,        # call this as Image arrives
            10,                         # queue depth
        )

        self.publisher = self.create_publisher(
            VehicleGlobalPosition,
            "/fmu/in/aux_global_position",
            10,
        )

    def publish_position(
        self,
        image_time_stamp_microseconds: int, 
        estimate: EstimatedGeoPosition
    ):
        msg = VehicleGlobalPosition()

        msg.timestamp = self.get_clock().now().nanoseconds // 1_000
        msg.timestamp_sample = image_time_stamp_microseconds

        msg.lon = estimate.lon
        msg.lat = estimate.lat
        msg.eph = estimate.eph

        msg.lat_lon_valid = True
        msg.alt_valid = False
        msg.terrain_alt_valid = False

        self.publisher.publish(msg)

    def image_callback(self, msg: Image):
        """Called when message arrvies in the queue"""
        image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        predictions = self.localizer.predict(image)
        estimate = self.localizer.estimate_position(predictions)

        # no-op
        if not estimate.valid:
            return

        image_time_stamp = (
            msg.header.stamp.sec * 1_000_000
            + msg.header.stamp.nanosec // 1_000
        )

        self.publish_position(image_time_stamp, estimate)

        self.get_logger().info(
            f"Est Lon: {estimate.lon}, " 
            f"Est Lat: {estimate.lat}, "
            f"Est Error: {estimate.eph}"
        )

    def destroy_node(self):
        """Cleanup node"""
        self.db_manager.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
        
    model_config = load_config("src/config/default_onnx.yaml")
    preprocessing_config = load_config("src/config/preprocess.yaml")

    node = VisualLocalizationNode(model_config, preprocessing_config)

    try:
        print(f"RUNNING: Using {model_config.model.name} on {model_config.model.source}")
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nProgram stopped safely by the user")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        print("Cleaned resources and exited")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Masked PointCloud Publisher for HSR (ROS1 Noetic)
=================================================
Segmentation mask and organized scene point cloud are synchronized and the
masked points are republished as an unorganized PointCloud2.
"""

import numpy as np
import rospy
import message_filters
from sensor_msgs.msg import Image, PointCloud2


class MaskedPointCloudNode(object):
    def __init__(self):
        rospy.init_node("masked_pointcloud_node", anonymous=False)

        self.pointcloud_topic = rospy.get_param(
            "~pointcloud_topic",
            "/hsrb/head_rgbd_sensor/depth_registered/rectified_points",
        )
        self.mask_topic = rospy.get_param("~mask_topic", "/sam/mask")
        self.output_topic = rospy.get_param("~output_topic", "/object_pointcloud")
        self.sync_slop = float(rospy.get_param("~sync_slop", 0.1))
        self.sync_queue_size = int(rospy.get_param("~sync_queue_size", 10))
        self.mask_threshold = int(rospy.get_param("~mask_threshold", 128))

        rospy.loginfo("PointCloud topic : %s", self.pointcloud_topic)
        rospy.loginfo("Mask topic       : %s", self.mask_topic)
        rospy.loginfo("Output topic     : %s", self.output_topic)
        rospy.loginfo("Sync slop        : %.3fs", self.sync_slop)

        self.pc_pub = rospy.Publisher(self.output_topic, PointCloud2, queue_size=10)

        self.pc_sub = message_filters.Subscriber(PointCloud2, self.pointcloud_topic)
        self.mask_sub = message_filters.Subscriber(Image, self.mask_topic)
        self.sync = message_filters.ApproximateTimeSynchronizer(
            [self.pc_sub, self.mask_sub],
            queue_size=self.sync_queue_size,
            slop=self.sync_slop,
        )
        self.sync.registerCallback(self.synced_callback)

        rospy.loginfo("Masked PointCloud node is ready. Waiting for data...")

    def synced_callback(self, pc_msg, mask_msg):
        mask = self._image_to_numpy(mask_msg)
        if mask is None:
            rospy.logwarn("Failed to convert mask image.")
            return

        binary_mask = mask >= self.mask_threshold

        if pc_msg.height <= 1:
            rospy.logwarn(
                "PointCloud2 is unorganized (height=%d). Organized cloud is required.",
                pc_msg.height,
            )
            return

        pc_h = pc_msg.height
        pc_w = pc_msg.width
        mask_h, mask_w = binary_mask.shape[:2]

        if pc_h != mask_h or pc_w != mask_w:
            rospy.logwarn(
                "Size mismatch: cloud(%dx%d) vs mask(%dx%d). Resizing mask.",
                pc_w,
                pc_h,
                mask_w,
                mask_h,
            )
            binary_mask = self._resize_mask(binary_mask, pc_w, pc_h)

        valid_indices = np.flatnonzero(binary_mask.reshape(-1))
        if len(valid_indices) == 0:
            rospy.loginfo("No valid pixels inside mask. Skipping.")
            return

        raw_data = np.frombuffer(pc_msg.data, dtype=np.uint8)
        point_step = pc_msg.point_step
        row_step = pc_msg.row_step

        if row_step == pc_w * point_step:
            all_points = raw_data.reshape(pc_h * pc_w, point_step)
        else:
            all_points = np.zeros((pc_h * pc_w, point_step), dtype=np.uint8)
            for row in range(pc_h):
                row_start = row * row_step
                for col in range(pc_w):
                    src = row_start + col * point_step
                    all_points[row * pc_w + col] = raw_data[src : src + point_step]

        masked_points = all_points[valid_indices]

        x_offset = self._get_field_offset(pc_msg.fields, "x")
        y_offset = self._get_field_offset(pc_msg.fields, "y")
        z_offset = self._get_field_offset(pc_msg.fields, "z")
        if x_offset is not None and y_offset is not None and z_offset is not None:
            xs = masked_points[:, x_offset : x_offset + 4].copy().view(np.float32).reshape(-1)
            ys = masked_points[:, y_offset : y_offset + 4].copy().view(np.float32).reshape(-1)
            zs = masked_points[:, z_offset : z_offset + 4].copy().view(np.float32).reshape(-1)
            finite_mask = ~(np.isnan(xs) | np.isnan(ys) | np.isnan(zs))
            masked_points = masked_points[finite_mask]

        if len(masked_points) == 0:
            rospy.loginfo("No valid points after NaN removal.")
            return

        out_msg = PointCloud2()
        out_msg.header = pc_msg.header
        out_msg.height = 1
        out_msg.width = len(masked_points)
        out_msg.fields = pc_msg.fields
        out_msg.is_bigendian = pc_msg.is_bigendian
        out_msg.point_step = point_step
        out_msg.row_step = point_step * len(masked_points)
        out_msg.data = masked_points.tobytes()
        out_msg.is_dense = True

        self.pc_pub.publish(out_msg)
        rospy.loginfo("Published %d masked points (from %d points).", len(masked_points), pc_h * pc_w)

    def _image_to_numpy(self, img_msg):
        encoding = img_msg.encoding.lower()
        height = img_msg.height
        width = img_msg.width

        if encoding in ("mono8", "8uc1"):
            return np.frombuffer(img_msg.data, dtype=np.uint8).reshape(height, width)
        if encoding in ("mono16", "16uc1"):
            array = np.frombuffer(img_msg.data, dtype=np.uint16).reshape(height, width)
            max_value = int(array.max()) if array.size else 0
            if max_value > 0:
                return (array.astype(np.float32) / max_value * 255.0).astype(np.uint8)
            return array.astype(np.uint8)
        if encoding in ("rgb8", "bgr8"):
            array = np.frombuffer(img_msg.data, dtype=np.uint8).reshape(height, width, 3)
            return np.mean(array, axis=2).astype(np.uint8)
        if encoding == "32fc1":
            array = np.frombuffer(img_msg.data, dtype=np.float32).reshape(height, width)
            return np.clip(array * 255.0, 0.0, 255.0).astype(np.uint8)

        rospy.logwarn("Unsupported image encoding: %s", encoding)
        return None

    @staticmethod
    def _resize_mask(mask, target_w, target_h):
        src_h, src_w = mask.shape[:2]
        row_idx = (np.arange(target_h) * src_h / target_h).astype(int)
        col_idx = (np.arange(target_w) * src_w / target_w).astype(int)
        return mask[np.ix_(row_idx, col_idx)]

    @staticmethod
    def _get_field_offset(fields, name):
        for field in fields:
            if field.name == name:
                return field.offset
        return None


def main():
    MaskedPointCloudNode()
    rospy.spin()


if __name__ == "__main__":
    main()

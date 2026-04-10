#!/usr/bin/env python3
import os
import struct
import time

import numpy as np
import rospy
import torch
import trimesh.transformations as tra
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import PointCloud2
from tf2_ros import Buffer, TransformException, TransformListener
from visualization_msgs.msg import Marker, MarkerArray

from grasp_gen.grasp_server import GraspGenSampler, load_grasp_cfg
from grasp_gen.robot import get_gripper_info
from grasp_gen.utils.grasp_ranking import (
    compute_approach_clearance_scores,
    compute_centrality_scores,
    compute_surface_alignment_scores,
    compute_total_scores,
    estimate_support_plane_height,
    filter_by_centrality,
    filter_by_support_plane_clearance,
)
from grasp_gen.utils.meshcat_utils import (
    get_color_from_score,
    visualize_grasp,
    visualize_pointcloud,
)
from grasp_gen.utils.point_cloud_utils import (
    filter_colliding_grasps,
    point_cloud_outlier_removal_with_color,
)


def read_points(cloud, field_names=None, skip_nans=False, uvs=None):
    if uvs is None:
        uvs = []

    assert isinstance(cloud, PointCloud2), "cloud is not a sensor_msgs.msg.PointCloud2"
    _get_struct_fmt(cloud.is_bigendian, cloud.fields, field_names)

    width = cloud.width
    height = cloud.height
    point_step = cloud.point_step

    if skip_nans and cloud.is_dense:
        pass

    raw_data = np.frombuffer(cloud.data, dtype=np.uint8)
    num_points = width * height

    if num_points == 0:
        return np.empty((0, 3), dtype=np.float32), None

    try:
        reshaped = raw_data.reshape(num_points, point_step)
    except ValueError:
        if cloud.row_step == width * point_step:
            rospy.logwarn("PointCloud2 data size is inconsistent.")
            return np.empty((0, 3), dtype=np.float32), None

        reshaped = np.zeros((num_points, point_step), dtype=np.uint8)
        for row in range(height):
            row_start = row * cloud.row_step
            for col in range(width):
                src = row_start + col * point_step
                reshaped[row * width + col] = raw_data[src : src + point_step]

    x_offset = -1
    y_offset = -1
    z_offset = -1
    rgb_offset = -1

    for field in cloud.fields:
        if field.name == "x":
            x_offset = field.offset
        elif field.name == "y":
            y_offset = field.offset
        elif field.name == "z":
            z_offset = field.offset
        elif field.name == "rgb":
            rgb_offset = field.offset

    if x_offset == -1 or y_offset == -1 or z_offset == -1:
        return np.empty((0, 3), dtype=np.float32), None

    xs = reshaped[:, x_offset : x_offset + 4].copy().view(np.float32).reshape(-1)
    ys = reshaped[:, y_offset : y_offset + 4].copy().view(np.float32).reshape(-1)
    zs = reshaped[:, z_offset : z_offset + 4].copy().view(np.float32).reshape(-1)
    points = np.stack([xs, ys, zs], axis=1)

    if skip_nans:
        finite_mask = ~np.isnan(points).any(axis=1)
        points = points[finite_mask]
    else:
        finite_mask = None

    colors = None
    if rgb_offset != -1:
        colors = np.zeros((num_points, 3), dtype=np.float32)
        if finite_mask is not None:
            colors = colors[finite_mask]

    return points, colors


def _get_struct_fmt(is_bigendian, fields, field_names=None):
    return "fff"


def transform_stamped_to_matrix(transform_stamped):
    translation = transform_stamped.transform.translation
    rotation = transform_stamped.transform.rotation
    matrix = tra.quaternion_matrix([rotation.x, rotation.y, rotation.z, rotation.w])
    matrix[:3, 3] = [translation.x, translation.y, translation.z]
    return matrix


class GraspInferenceNodeAdvancedRos1(object):
    def __init__(self):
        rospy.init_node("grasp_inference_node_advanced_ros1", anonymous=False)

        self.scene_topic = rospy.get_param(
            "~scene_topic",
            "/hsrb/head_rgbd_sensor/depth_registered/rectified_points",
        )
        self.object_topic = rospy.get_param("~object_topic", "/object_pointcloud")
        gripper_config_path = rospy.get_param(
            "~gripper_config",
            "GraspGenModels/checkpoints/graspgen_robotiq_2f_140.yml",
        )
        self.target_frame = rospy.get_param("~target_frame", "base_link")
        self.tf_timeout_sec = float(rospy.get_param("~tf_timeout_sec", 0.2))
        self.grasp_confidence_threshold = float(
            rospy.get_param("~grasp_confidence_threshold", 0.5)
        )
        self.collision_threshold = float(rospy.get_param("~collision_threshold", 0.02))
        self.table_clearance_threshold = float(
            rospy.get_param("~table_clearance_threshold", 0.02)
        )
        self.support_plane_axis = int(rospy.get_param("~support_plane_axis", 2))
        self.support_plane_percentile = float(
            rospy.get_param("~support_plane_percentile", 3.0)
        )
        self.min_centrality_threshold = float(
            rospy.get_param("~min_centrality_threshold", 0.15)
        )
        self.approach_corridor_radius = float(
            rospy.get_param("~approach_corridor_radius", 0.03)
        )
        self.approach_corridor_length = float(
            rospy.get_param("~approach_corridor_length", 0.12)
        )
        self.surface_alignment_k_neighbors = int(
            rospy.get_param("~surface_alignment_k_neighbors", 32)
        )
        self.score_weight_confidence = float(
            rospy.get_param("~score_weight_confidence", 0.5)
        )
        self.score_weight_centrality = float(
            rospy.get_param("~score_weight_centrality", 0.2)
        )
        self.score_weight_clearance = float(
            rospy.get_param("~score_weight_clearance", 0.2)
        )
        self.score_weight_surface_alignment = float(
            rospy.get_param("~score_weight_surface_alignment", 0.1)
        )
        self.meshcat_zmq_url = rospy.get_param(
            "~meshcat_zmq_url",
            os.environ.get("MESHCAT_ZMQ_URL", "tcp://127.0.0.1:6000"),
        )

        rospy.loginfo("Scene Topic: %s", self.scene_topic)
        rospy.loginfo("Object Topic: %s", self.object_topic)
        rospy.loginfo("Target Frame: %s", self.target_frame)

        self.scene_sub = rospy.Subscriber(
            self.scene_topic,
            PointCloud2,
            self.listener_callback_scene,
            queue_size=1,
        )
        self.object_sub = rospy.Subscriber(
            self.object_topic,
            PointCloud2,
            self.listener_callback_object,
            queue_size=1,
        )

        self.marker_pub = rospy.Publisher("/grasp_markers", MarkerArray, queue_size=1)
        self.best_grasp_pub = rospy.Publisher(
            "/grasp/best_pose", PoseStamped, queue_size=1
        )

        self.tf_buffer = Buffer(cache_time=rospy.Duration(10.0))
        self.tf_listener = TransformListener(self.tf_buffer)

        if not os.path.exists(gripper_config_path):
            rospy.logwarn("Config not found: %s", gripper_config_path)

        rospy.loginfo("Loading GraspGen model...")
        self.grasp_cfg = load_grasp_cfg(gripper_config_path)
        self.gripper_name = self.grasp_cfg.data.gripper_name
        self.grasp_sampler = GraspGenSampler(self.grasp_cfg)
        self.gripper_info = get_gripper_info(self.gripper_name)
        self.gripper_collision_mesh = self.gripper_info.collision_mesh
        rospy.loginfo("Model loaded successfully.")

        self.vis = self.create_custom_visualizer(self.meshcat_zmq_url)
        self.vis.delete()

        self.latest_scene_pc = None
        self.latest_scene_color = None

    def create_custom_visualizer(self, zmq_url):
        import meshcat

        rospy.loginfo("Waiting for meshcat server at %s", zmq_url)
        return meshcat.Visualizer(zmq_url=zmq_url)

    def lookup_transform_matrix(self, source_frame):
        if source_frame == self.target_frame:
            return np.eye(4, dtype=np.float64)

        try:
            transform_stamped = self.tf_buffer.lookup_transform(
                self.target_frame,
                source_frame,
                rospy.Time(0),
                rospy.Duration(self.tf_timeout_sec),
            )
        except TransformException as exc:
            rospy.logwarn(
                "Failed to lookup TF %s -> %s: %s",
                source_frame,
                self.target_frame,
                exc,
            )
            return None

        return transform_stamped_to_matrix(transform_stamped)

    def transform_points_to_target_frame(self, points, source_frame):
        transform_matrix = self.lookup_transform_matrix(source_frame)
        if transform_matrix is None:
            return None
        return tra.transform_points(points, transform_matrix)

    def listener_callback_scene(self, msg):
        points, colors = read_points(msg)
        if len(points) == 0:
            return

        transformed_points = self.transform_points_to_target_frame(
            points, msg.header.frame_id
        )
        if transformed_points is None:
            return

        self.latest_scene_pc = transformed_points
        self.latest_scene_color = colors

    def listener_callback_object(self, msg):
        rospy.loginfo("Received OBJECT pointcloud. Running inference...")

        obj_points, obj_colors = read_points(msg, skip_nans=True)
        if len(obj_points) == 0:
            rospy.logwarn("Empty object point cloud received.")
            return

        obj_points = self.transform_points_to_target_frame(obj_points, msg.header.frame_id)
        if obj_points is None:
            rospy.logwarn(
                "Skipping object cloud because TF to target frame is unavailable."
            )
            return

        finite_mask = ~np.isnan(obj_points).any(axis=1)
        obj_points = obj_points[finite_mask]
        if obj_colors is not None:
            obj_colors = obj_colors[finite_mask]

        if len(obj_points) > 4096:
            idx = np.random.choice(len(obj_points), 4096, replace=False)
            obj_points = obj_points[idx]
            if obj_colors is not None:
                obj_colors = obj_colors[idx]

        obj_pc_torch = torch.from_numpy(obj_points).float()
        obj_c_torch = torch.zeros_like(obj_pc_torch)
        obj_pc_clean, _, _, _ = point_cloud_outlier_removal_with_color(
            obj_pc_torch, obj_c_torch
        )
        obj_pc_clean_np = obj_pc_clean.cpu().numpy()
        obj_pc_clean = obj_pc_clean.cuda()

        visualize_pointcloud(self.vis, "pc_object", obj_pc_clean_np, None, size=0.005)
        if self.latest_scene_pc is not None:
            visualize_pointcloud(self.vis, "pc_scene", self.latest_scene_pc, None, size=0.002)

        t0 = time.time()
        grasps, grasp_conf = GraspGenSampler.run_inference(
            obj_pc_clean,
            self.grasp_sampler,
            grasp_threshold=self.grasp_confidence_threshold,
            num_grasps=100,
            max_tries=2,
        )
        t_infer = time.time() - t0
        rospy.loginfo(
            "Inference done in %.3fs. Found %d grasps.", t_infer, len(grasps)
        )

        if len(grasps) == 0:
            return

        grasp_conf = grasp_conf.cpu().numpy()
        grasps = grasps.cpu().numpy()
        grasps[:, 3, 3] = 1

        final_grasps = grasps
        final_conf = grasp_conf

        if self.latest_scene_pc is not None:
            rospy.loginfo("Checking collisions...")
            scene_check = self.latest_scene_pc
            if len(scene_check) > 10000:
                idx = np.random.choice(len(scene_check), 10000, replace=False)
                scene_check = scene_check[idx]

            collision_mask = filter_colliding_grasps(
                scene_pc=scene_check,
                grasp_poses=grasps,
                gripper_collision_mesh=self.gripper_collision_mesh,
                collision_threshold=self.collision_threshold,
            )
            final_grasps = grasps[collision_mask]
            final_conf = grasp_conf[collision_mask]
            rospy.loginfo(
                "Collision check: %d -> %d valid grasps.",
                len(grasps),
                len(final_grasps),
            )

            if len(final_grasps) > 0:
                plane_height = estimate_support_plane_height(
                    scene_check,
                    axis=self.support_plane_axis,
                    percentile=self.support_plane_percentile,
                )
                support_mask = filter_by_support_plane_clearance(
                    final_grasps,
                    plane_height=plane_height,
                    min_clearance=self.table_clearance_threshold,
                    axis=self.support_plane_axis,
                )
                rospy.loginfo(
                    "Support clearance filter: %d -> %d valid grasps (plane=%.3f, axis=%d)",
                    len(final_grasps),
                    int(np.sum(support_mask)),
                    plane_height,
                    self.support_plane_axis,
                )
                final_grasps = final_grasps[support_mask]
                final_conf = final_conf[support_mask]

        if len(final_grasps) > 0:
            centrality_mask = filter_by_centrality(
                obj_pc_clean_np,
                final_grasps,
                min_centrality=self.min_centrality_threshold,
            )
            rospy.loginfo(
                "Centrality filter: %d -> %d valid grasps.",
                len(final_grasps),
                int(np.sum(centrality_mask)),
            )
            final_grasps = final_grasps[centrality_mask]
            final_conf = final_conf[centrality_mask]

        if len(final_grasps) == 0:
            rospy.logwarn("All grasps were removed by hard filters.")
            return

        centrality_scores = compute_centrality_scores(obj_pc_clean_np, final_grasps)
        environment_pc = (
            self.latest_scene_pc if self.latest_scene_pc is not None else obj_pc_clean_np
        )
        clearance_scores = compute_approach_clearance_scores(
            environment_pc=environment_pc,
            grasp_poses=final_grasps,
            corridor_radius=self.approach_corridor_radius,
            corridor_length=self.approach_corridor_length,
        )
        surface_alignment_scores = compute_surface_alignment_scores(
            object_pc=obj_pc_clean_np,
            grasp_poses=final_grasps,
            k_neighbors=self.surface_alignment_k_neighbors,
        )
        total_scores = compute_total_scores(
            confidence=final_conf,
            centrality=centrality_scores,
            clearance=clearance_scores,
            surface_alignment=surface_alignment_scores,
            weight_confidence=self.score_weight_confidence,
            weight_centrality=self.score_weight_centrality,
            weight_clearance=self.score_weight_clearance,
            weight_surface_alignment=self.score_weight_surface_alignment,
        )
        final_scores = get_color_from_score(total_scores, use_255_scale=True)

        for index, grasp_pose in enumerate(final_grasps[:20]):
            visualize_grasp(
                self.vis,
                "grasps/g_%d" % index,
                grasp_pose,
                color=final_scores[index],
                gripper_name=self.gripper_name,
            )

        self.publish_markers(final_grasps, final_scores, self.target_frame)

        best_idx = int(np.argmax(total_scores))
        best_grasp = final_grasps[best_idx]
        rospy.loginfo(
            "Selected Best Grasp: total=%.3f conf=%.3f center=%.3f clear=%.3f align=%.3f",
            total_scores[best_idx],
            final_conf[best_idx],
            centrality_scores[best_idx],
            clearance_scores[best_idx],
            surface_alignment_scores[best_idx],
        )
        self.publish_best_grasp(best_grasp, self.target_frame)
        visualize_grasp(
            self.vis,
            "grasps/best_grasp",
            best_grasp,
            color=[0, 255, 0],
            gripper_name=self.gripper_name,
        )

    def publish_best_grasp(self, grasp_pose, frame_id):
        msg = PoseStamped()
        msg.header.frame_id = frame_id
        msg.header.stamp = rospy.Time.now()

        translation = grasp_pose[:3, 3]
        quaternion = tra.quaternion_from_matrix(grasp_pose)

        msg.pose.position.x = float(translation[0])
        msg.pose.position.y = float(translation[1])
        msg.pose.position.z = float(translation[2])
        msg.pose.orientation.x = float(quaternion[0])
        msg.pose.orientation.y = float(quaternion[1])
        msg.pose.orientation.z = float(quaternion[2])
        msg.pose.orientation.w = float(quaternion[3])
        self.best_grasp_pub.publish(msg)

    def publish_markers(self, grasps, scores, frame_id):
        marker_array = MarkerArray()
        stamp = rospy.Time.now()

        for index, (pose, score) in enumerate(zip(grasps[:50], scores[:50])):
            marker = Marker()
            marker.header.frame_id = frame_id
            marker.header.stamp = stamp
            marker.ns = "grasp"
            marker.id = index
            marker.type = Marker.ARROW
            marker.action = Marker.ADD

            translation = pose[:3, 3]
            quaternion = tra.quaternion_from_matrix(pose)

            marker.pose.position.x = float(translation[0])
            marker.pose.position.y = float(translation[1])
            marker.pose.position.z = float(translation[2])
            marker.pose.orientation.x = float(quaternion[0])
            marker.pose.orientation.y = float(quaternion[1])
            marker.pose.orientation.z = float(quaternion[2])
            marker.pose.orientation.w = float(quaternion[3])

            marker.scale.x = 0.1
            marker.scale.y = 0.01
            marker.scale.z = 0.01

            rgb = score / 255.0
            marker.color.r = float(rgb[0])
            marker.color.g = float(rgb[1])
            marker.color.b = float(rgb[2])
            marker.color.a = 1.0

            marker_array.markers.append(marker)

        self.marker_pub.publish(marker_array)


def main():
    GraspInferenceNodeAdvancedRos1()
    rospy.spin()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import struct
import sys
import time

import numpy as np
import rclpy
import torch
import trimesh.transformations as tra
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from visualization_msgs.msg import Marker, MarkerArray

# GraspGen imports
from grasp_gen.grasp_server import GraspGenSampler, load_grasp_cfg
from grasp_gen.utils.meshcat_utils import (
    create_visualizer,
    get_color_from_score,
    visualize_grasp,
    visualize_pointcloud,
)
from grasp_gen.utils.point_cloud_utils import (
    point_cloud_outlier_removal_with_color,
    filter_colliding_grasps,
)
from grasp_gen.robot import get_gripper_info

# --- Custom PointCloud2 Parser (since sensor_msgs_py is missing) ---
def read_points(cloud, field_names=None, skip_nans=False, uvs=[]):
    """
    Read points from a L{sensor_msgs.PointCloud2} message.
    """
    assert isinstance(cloud, PointCloud2), 'cloud is not a sensor_msgs.msg.PointCloud2'
    fmt = _get_struct_fmt(cloud.is_bigendian, cloud.fields, field_names)
    width, height, point_step, row_step, data, is_dense = cloud.width, cloud.height, cloud.point_step, cloud.row_step, cloud.data, cloud.is_dense
    unpack_from = struct.Struct(fmt).unpack_from

    if skip_nans:
        if is_dense:
            # print("Writing is_dense=True for a cloud that is valid, but we are skipping nans")
            pass
        else:
            # print("is_dense=False")
            pass

    # Select fields
    if field_names is None:
        field_names = [f.name for f in cloud.fields]
    
    # Check if we want all fields
    include_all = True
    # Implementation simplified for standard float fields (x, y, z, rgb/intensity)
    
    # Generator
    pk_count = width * height
    # unpack = struct.Struct(fmt).unpack_from
    
    # Parse data assumes float32 for simplicity in this custom fallback
    # A full implementation handles all types. Here we assume standard XYZ or XYZRGB float32
    
    # --- Simplified numpy based parser for speed ---
    # This is much faster than struct.unpack for large clouds
    
    # output array
    points = []
    
    # Get offsets
    offsets = {f.name: f.offset for f in cloud.fields}
    
    dt = np.dtype(np.uint8)
    # data_arr = np.frombuffer(cloud.data, dt)
    # This is slightly complex to do fully generic in pure numpy without sensor_msgs_py, 
    # but we can do a structured array approach if we know the layout.
    
    # Fallback to a simpler manual extraction for x,y,z if common
    dummy_points = []
    
    # Create a dummy generic reader that works for x, y, z float32
    # We will use a generator to yield points, but for GraspGen we usually need the full array.
    
    # Helper to unpack
    def yield_points():
        p_step = cloud.point_step
        # Format string for unpacking user requested fields
        # This part is tricky without the fall helper. 
        # Let's try to extract x,y,z specifically as float32
        
        # 1. Cast data to view
        # We assume little endian usually
        limit = width * height * point_step
        
        # Create a view of the raw data
        raw_data = np.frombuffer(cloud.data, dtype=np.uint8)
        
        # Extract X, Y, Z
        x_offset = -1
        y_offset = -1
        z_offset = -1
        rgb_offset = -1
        
        for f in cloud.fields:
            if f.name == 'x': x_offset = f.offset
            elif f.name == 'y': y_offset = f.offset
            elif f.name == 'z': z_offset = f.offset
            elif f.name == 'rgb': rgb_offset = f.offset

        if x_offset == -1 or y_offset == -1 or z_offset == -1:
            return np.array([]), np.array([])
            
        # Re-shape to (N, point_step)
        # Handle potential padding?
        # Usually data is row_step * height.
        
        # Let's just walk the bytes for safety if stride is weird, but numpy stride is faster
        num_points = width * height
        
        if len(raw_data) != num_points * point_step:
            # Maybe row_step padding?
             pass 


        
        # X
        # Create a buffer of just the X bytes
        # This is strictly valid only if data is compact or we handle stride
        # We can reshape raw_data to (num_points, point_step)
        reshaped = raw_data.reshape(num_points, point_step)
        
        x_bytes = reshaped[:, x_offset:x_offset+4].copy()
        y_bytes = reshaped[:, y_offset:y_offset+4].copy()
        z_bytes = reshaped[:, z_offset:z_offset+4].copy()
        
        xs = x_bytes.view(dtype=np.float32).flatten()
        ys = y_bytes.view(dtype=np.float32).flatten()
        zs = z_bytes.view(dtype=np.float32).flatten()
        
        points = np.stack([xs, ys, zs], axis=1)
        
        colors = None
        if rgb_offset != -1:
            rgb_bytes = reshaped[:, rgb_offset:rgb_offset+4].copy()
            # RGB is usually packed as float or uint32
            # But we often want extracted R, G, B
            # For simplicity, let's keep it as float for now or ignore color if not strictly needed for grasp logic
            # (GraspGen uses geometry mostly, color outlier removal uses it but we can skip color if needed)
            
            # Actually, standard ROS packing involves casting float to int or vice versa for RGB.
            # Let's try to extract as uint8 r,g,b
            # offsets inside the 4 bytes depend on endianness. Assuming standard:
            # B G R x (little endian int) -> R G B
            
            # Just grab byte values directly
            # rgb_bytes is (N, 4)
            # Typically: [B, G, R, A] or similar
            # Let's assume offset is correct.
            # We can return None for colors to simplify initial implementation if color usage is optional.
            # But the demo uses `point_cloud_outlier_removal_with_color`.
            # Let's try to pass dummy colors if parsing is hard.
            colors = np.zeros((num_points, 3), dtype=np.float32) # Dummy black
            
            # Try parsing real color
            # Just take the first 3 bytes at offset?
            # rgb_packed = rgb_bytes.view(dtype=np.uint32).flatten()
            # r = (rgb_packed >> 16) & 0x0000ff
            # g = (rgb_packed >> 8) & 0x0000ff
            # b = (rgb_packed) & 0x0000ff
            # colors = np.stack([r, g, b], axis=1).astype(np.float32) / 255.0

        return points, colors

    return yield_points()

def _get_struct_fmt(is_bigendian, fields, field_names=None):
    # Simplified placeholder
    return 'fff' 


class GraspInferenceNode(Node):
    def __init__(self):
        super().__init__('grasp_inference_node')

        # --- Parameters ---
        self.declare_parameter('scene_topic', '/camera/camera/depth/color/points')
        self.declare_parameter('object_topic', '/yolov8/object_points') 
        self.declare_parameter('gripper_config', 'GraspGenModels/checkpoints/graspgen_robotiq_2f_140.yml')
        
        self.scene_topic = self.get_parameter('scene_topic').value
        self.object_topic = self.get_parameter('object_topic').value
        gripper_config_path = self.get_parameter('gripper_config').value

        self.get_logger().info(f"Scene Topic: {self.scene_topic}")
        self.get_logger().info(f"Object Topic: {self.object_topic}")

        # --- Subscriptions ---
        self.scene_sub = self.create_subscription(
            PointCloud2,
            self.scene_topic,
            self.listener_callback_scene,
            1
        )
        self.object_sub = self.create_subscription(
            PointCloud2,
            self.object_topic,
            self.listener_callback_object,
            1
        )

        # --- Publishers ---
        self.marker_pub = self.create_publisher(MarkerArray, '/grasp_markers', 1)

        # --- Validations ---
        if not os.path.exists(gripper_config_path):
            self.get_logger().warn(f"Config not found: {gripper_config_path}, trying absolute path or default...")
            # Fallback logic could go here
        
        # --- Load GraspGen Model ---
        self.get_logger().info("Loading GraspGen model...")
        try:
            self.grasp_cfg = load_grasp_cfg(gripper_config_path)
            self.gripper_name = self.grasp_cfg.data.gripper_name
            self.grasp_sampler = GraspGenSampler(self.grasp_cfg)
            
            # Load gripper collision mesh
            self.gripper_info = get_gripper_info(self.gripper_name)
            self.gripper_collision_mesh = self.gripper_info.collision_mesh
            self.get_logger().info("Model loaded successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {e}")
            raise e

        # --- MeshCat ---
        self.get_logger().info("Initializing MeshCat...")
        # Check environment variable or parameter for ZMQ URL
        zmq_url = os.environ.get("MESHCAT_ZMQ_URL", "tcp://127.0.0.1:6000")
        self.get_logger().info(f"Connecting to MeshCat at {zmq_url}")
        
        # Override create_visualizer to support custom URL
        self.vis = self.create_custom_visualizer(zmq_url) 
        self.vis.delete() # Clear
        
        # --- State ---
        self.latest_scene_pc = None
        self.latest_scene_color = None

    def create_custom_visualizer(self, zmq_url):
        import meshcat
        self.get_logger().info(f"Waiting for meshcat server at {zmq_url}...")
        vis = meshcat.Visualizer(zmq_url=zmq_url)
        return vis

    def listener_callback_scene(self, msg):
        """Buffer the latest scene point cloud for collision checking."""
        # self.get_logger().info(f"Received scene pointcloud: {msg.width * msg.height} points")
        points, colors = read_points(msg)
        
        if len(points) == 0:
            return

        # Simple downsampling for storage (optional, to save memory/speed)
        # N = len(points)
        # if N > 20000:
        #     idx = np.random.choice(N, 20000, replace=False)
        #     points = points[idx]
        #     if colors is not None: colors = colors[idx]
            
        self.latest_scene_pc = points
        self.latest_scene_color = colors
        
        # Visualize scene in MeshCat immediately?
        # Maybe throttle this to avoid lagging
        # visualize_pointcloud(self.vis, "pc_scene", points, colors, size=0.005)

    def listener_callback_object(self, msg):
        """Receive object point cloud and trigger inference."""
        self.get_logger().info(f"Received OBJECT pointcloud. Running inference...")
        
        obj_points, obj_colors = read_points(msg, skip_nans=True)
        if len(obj_points) == 0:
            self.get_logger().warn("Empty object point cloud received.")
            return

        # Handle NaNs if custom parser didn't
        mask = ~np.isnan(obj_points).any(axis=1)
        obj_points = obj_points[mask]
        if obj_colors is not None:
             obj_colors = obj_colors[mask]
        
        # --- 1. Preprocessing ---
        if len(obj_points) > 4096:
            idx = np.random.choice(len(obj_points), 4096, replace=False)
            obj_points = obj_points[idx]
            if obj_colors is not None: obj_colors = obj_colors[idx]
            
        # Outlier removal (critical for RealSense noise)
        # Use simple statistical removal or just pass through if clean enough
        # GraspGen utility requires Tensor
        obj_pc_torch = torch.from_numpy(obj_points).float()
        obj_c_torch = torch.zeros_like(obj_pc_torch) # Dummy color if none
        
        # Outlier removal
        obj_pc_clean, _, _, _ = point_cloud_outlier_removal_with_color(
             obj_pc_torch, obj_c_torch
        )
        obj_pc_clean_np = obj_pc_clean.cpu().numpy()
        
        # Ensure tensor is on CUDA for inference
        obj_pc_clean = obj_pc_clean.cuda()
        
        # Update MeshCat visualization
        visualize_pointcloud(self.vis, "pc_object", obj_pc_clean_np, None, size=0.005)
        
        if self.latest_scene_pc is not None:
             visualize_pointcloud(self.vis, "pc_scene", self.latest_scene_pc, None, size=0.002)

        # --- 2. Inference ---
        t0 = time.time()
        # run_inference expects (N,3)
        grasps, grasp_conf = GraspGenSampler.run_inference(
            obj_pc_clean,
            self.grasp_sampler,
            grasp_threshold=0.5, # Configurable
            num_grasps=100,
            max_tries=2
        )
        t_infer = time.time() - t0
        self.get_logger().info(f"Inference done in {t_infer:.3f}s. Found {len(grasps)} grasps.")
        
        if len(grasps) == 0:
            return

        # Post-process
        grasp_conf = grasp_conf.cpu().numpy()
        grasps = grasps.cpu().numpy()
        grasps[:, 3, 3] = 1 # Homogeneous fix
        
        # Scores for color
        scores = get_color_from_score(grasp_conf, use_255_scale=True)
        
        # Center the visual logic
        # For visualization, we need to handle coordinates correctly.
        # The grasps are in the same frame as the input point cloud (Camera frame).
        
        # --- 3. Collision Filtering (if scene available) ---
        final_grasps = grasps
        final_scores = scores
        
        if self.latest_scene_pc is not None:
            self.get_logger().info("Checking collisions...")
            # Use only a subset of scene for speed
            scene_check = self.latest_scene_pc
            if len(scene_check) > 10000:
                idx = np.random.choice(len(scene_check), 10000, replace=False)
                scene_check = scene_check[idx]
            
            mask = filter_colliding_grasps(
                scene_pc=scene_check,
                grasp_poses=grasps,
                gripper_collision_mesh=self.gripper_collision_mesh,
                collision_threshold=0.02 # TODO parameterize
            )
            final_grasps = grasps[mask]
            final_scores = scores[mask]
            self.get_logger().info(f"Collision check: {len(grasps)} -> {len(final_grasps)} valid grasps.")
        
        # --- 4. Visualize in MeshCat ---
        # Clear old grasps?
        # vis["grasps"].delete() # Depends on meshcat structure
        
        for i, g in enumerate(final_grasps):
             # Limit number
            if i >= 20: break
            visualize_grasp(
                self.vis,
                f"grasps/g_{i}",
                g,
                color=final_scores[i],
                gripper_name=self.gripper_name
            )

        # --- 5. Publish Markers to ROS ---
        self.publish_markers(final_grasps, final_scores, msg.header.frame_id)

    def publish_markers(self, grasps, scores, frame_id):
        marker_array = MarkerArray()
        
        for i, (pose, score) in enumerate(zip(grasps, scores)):
            if i >= 50: break # Limit
            
            # Create a simple arrow or gripper marker
            marker = Marker()
            marker.header.frame_id = frame_id
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "grasp"
            marker.id = i
            marker.type = Marker.ARROW
            marker.action = Marker.ADD
            
            # Pose is 4x4 matrix. Decompose to pos/orient
            t = pose[:3, 3]
            q = tra.quaternion_from_matrix(pose)
            
            marker.pose.position.x = float(t[0])
            marker.pose.position.y = float(t[1])
            marker.pose.position.z = float(t[2])
            marker.pose.orientation.x = float(q[0])
            marker.pose.orientation.y = float(q[1])
            marker.pose.orientation.z = float(q[2])
            marker.pose.orientation.w = float(q[3])
            
            marker.scale.x = 0.1 # Length
            marker.scale.y = 0.01 # Width
            marker.scale.z = 0.01 # Height
            
            # Color from score (RGB 0-1)
            # scores is 0-255 in the snippet above? 
            # get_color_from_score(..., use_255_scale=True) returns [R, G, B] in 0-255?
            # Let's check logic. Usually we want 0-1 for ROS Marker
            rgb = score / 255.0
            marker.color.r = float(rgb[0])
            marker.color.g = float(rgb[1])
            marker.color.b = float(rgb[2])
            marker.color.a = 1.0
            
            marker_array.markers.append(marker)
            
        self.marker_pub.publish(marker_array)

import os
def main(args=None):
    rclpy.init(args=args)
    node = GraspInferenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

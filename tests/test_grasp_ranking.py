import numpy as np

from grasp_gen.utils.grasp_ranking import (
    compute_approach_clearance_scores,
    compute_centrality_scores,
    compute_surface_alignment_scores,
    compute_total_scores,
    estimate_support_plane_height,
    filter_by_centrality,
    filter_by_support_plane_clearance,
)


def _make_pose(position, z_axis):
    pose = np.eye(4, dtype=np.float64)
    pose[:3, 3] = np.asarray(position, dtype=np.float64)
    pose[:3, 2] = np.asarray(z_axis, dtype=np.float64)
    pose[:3, 2] /= np.linalg.norm(pose[:3, 2])
    pose[:3, 0] = np.array([1.0, 0.0, 0.0])
    pose[:3, 1] = np.array([0.0, 1.0, 0.0])
    return pose


def test_compute_centrality_scores_prefers_middle():
    object_pc = np.array(
        [[-1.0, 0.0, 0.0], [-0.5, 0.0, 0.0], [0.0, 0.0, 0.0], [0.5, 0.0, 0.0], [1.0, 0.0, 0.0]]
    )
    grasps = np.stack(
        [
            _make_pose([0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
            _make_pose([0.95, 0.0, 0.0], [0.0, 0.0, 1.0]),
        ]
    )

    scores = compute_centrality_scores(object_pc, grasps)

    assert scores[0] > scores[1]
    assert filter_by_centrality(object_pc, grasps, min_centrality=0.5).tolist() == [True, False]


def test_support_plane_estimation_and_filter():
    scene_pc = np.array(
        [[0.0, 0.0, 0.0], [0.1, 0.0, 0.0], [-0.1, 0.0, 0.0], [0.0, 0.1, 0.002]]
    )
    grasps = np.stack(
        [
            _make_pose([0.0, 0.0, 0.05], [0.0, 0.0, 1.0]),
            _make_pose([0.0, 0.0, 0.01], [0.0, 0.0, 1.0]),
        ]
    )

    plane_height = estimate_support_plane_height(scene_pc, axis=2, percentile=10.0)
    mask = filter_by_support_plane_clearance(grasps, plane_height, min_clearance=0.02, axis=2)

    assert plane_height >= 0.0
    assert mask.tolist() == [True, False]


def test_approach_clearance_scores_prefers_open_corridor():
    grasp_poses = np.stack(
        [
            _make_pose([0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
            _make_pose([0.0, 0.2, 0.0], [0.0, 0.0, 1.0]),
        ]
    )
    environment_pc = np.array(
        [
            [0.0, 0.0, -0.02],
            [0.0, 0.0, -0.03],
            [0.3, 0.3, 0.3],
        ]
    )

    scores = compute_approach_clearance_scores(
        environment_pc=environment_pc,
        grasp_poses=grasp_poses,
        corridor_radius=0.05,
        corridor_length=0.10,
    )

    assert scores[1] > scores[0]


def test_surface_alignment_scores_favor_normal_aligned_approach():
    plane_points = []
    for x in np.linspace(-0.05, 0.05, 5):
        for y in np.linspace(-0.05, 0.05, 5):
            plane_points.append([x, y, 0.0])
    object_pc = np.asarray(plane_points)
    grasps = np.stack(
        [
            _make_pose([0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
            _make_pose([0.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
        ]
    )

    scores = compute_surface_alignment_scores(object_pc, grasps, k_neighbors=16)

    assert scores[0] > scores[1]


def test_total_scores_use_weighted_sum():
    total_scores = compute_total_scores(
        confidence=np.array([0.8, 0.7]),
        centrality=np.array([0.1, 1.0]),
        clearance=np.array([0.1, 1.0]),
        surface_alignment=np.array([0.1, 1.0]),
        weight_confidence=0.2,
        weight_centrality=0.3,
        weight_clearance=0.3,
        weight_surface_alignment=0.2,
    )

    assert total_scores[1] > total_scores[0]

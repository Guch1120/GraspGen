import numpy as np


def _normalize_scores(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return values.astype(np.float32)
    min_value = float(np.min(values))
    max_value = float(np.max(values))
    if max_value - min_value < 1e-8:
        return np.ones_like(values, dtype=np.float32)
    return ((values - min_value) / (max_value - min_value)).astype(np.float32)


def estimate_support_plane_height(
    scene_pc: np.ndarray,
    axis: int = 2,
    percentile: float = 3.0,
) -> float:
    if len(scene_pc) == 0:
        raise ValueError("scene_pc must contain at least one point")
    axis_values = np.asarray(scene_pc, dtype=np.float64)[:, axis]
    return float(np.percentile(axis_values, percentile))


def filter_by_support_plane_clearance(
    grasp_poses: np.ndarray,
    plane_height: float,
    min_clearance: float,
    axis: int = 2,
) -> np.ndarray:
    grasp_positions = np.asarray(grasp_poses, dtype=np.float64)[:, :3, 3]
    return (grasp_positions[:, axis] - plane_height) >= min_clearance


def compute_centrality_scores(
    object_pc: np.ndarray,
    grasp_poses: np.ndarray,
) -> np.ndarray:
    object_pc = np.asarray(object_pc, dtype=np.float64)
    grasp_positions = np.asarray(grasp_poses, dtype=np.float64)[:, :3, 3]

    centered = object_pc - object_pc.mean(axis=0, keepdims=True)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    principal_axis = vh[0]

    object_proj = centered @ principal_axis
    grasp_proj = (grasp_positions - object_pc.mean(axis=0, keepdims=True)) @ principal_axis
    scale = max(float(np.max(np.abs(object_proj))), 1e-6)
    normalized_distance = np.clip(np.abs(grasp_proj) / scale, 0.0, 1.0)
    return (1.0 - normalized_distance).astype(np.float32)


def filter_by_centrality(
    object_pc: np.ndarray,
    grasp_poses: np.ndarray,
    min_centrality: float,
) -> np.ndarray:
    centrality = compute_centrality_scores(object_pc, grasp_poses)
    return centrality >= min_centrality


def compute_approach_clearance_scores(
    environment_pc: np.ndarray,
    grasp_poses: np.ndarray,
    corridor_radius: float = 0.03,
    corridor_length: float = 0.12,
) -> np.ndarray:
    environment_pc = np.asarray(environment_pc, dtype=np.float64)
    grasp_poses = np.asarray(grasp_poses, dtype=np.float64)
    scores = np.ones(len(grasp_poses), dtype=np.float32)

    if len(environment_pc) == 0 or len(grasp_poses) == 0:
        return scores

    for i, grasp_pose in enumerate(grasp_poses):
        grasp_position = grasp_pose[:3, 3]
        pregrasp_direction = -grasp_pose[:3, 2]
        pregrasp_direction /= max(np.linalg.norm(pregrasp_direction), 1e-8)

        deltas = environment_pc - grasp_position[None, :]
        axial_distance = deltas @ pregrasp_direction
        radial_distance = np.linalg.norm(
            deltas - np.outer(axial_distance, pregrasp_direction), axis=1
        )

        in_corridor = (
            (axial_distance > 0.0)
            & (axial_distance <= corridor_length)
            & (radial_distance <= corridor_radius)
        )
        if np.any(in_corridor):
            nearest_obstacle = float(np.min(axial_distance[in_corridor]))
            scores[i] = nearest_obstacle / max(corridor_length, 1e-8)
        else:
            scores[i] = 1.0

    return np.clip(scores, 0.0, 1.0)


def estimate_local_surface_normal(
    object_pc: np.ndarray,
    query_point: np.ndarray,
    k_neighbors: int = 32,
) -> np.ndarray:
    object_pc = np.asarray(object_pc, dtype=np.float64)
    query_point = np.asarray(query_point, dtype=np.float64)
    if len(object_pc) < 3:
        return np.array([0.0, 0.0, 1.0], dtype=np.float64)

    k = min(k_neighbors, len(object_pc))
    deltas = object_pc - query_point[None, :]
    distances = np.linalg.norm(deltas, axis=1)
    neighbor_idx = np.argpartition(distances, k - 1)[:k]
    neighbors = object_pc[neighbor_idx]
    centered = neighbors - neighbors.mean(axis=0, keepdims=True)
    covariance = centered.T @ centered / max(len(neighbors) - 1, 1)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    normal = eigenvectors[:, np.argmin(eigenvalues)]
    normal /= max(np.linalg.norm(normal), 1e-8)
    return normal


def compute_surface_alignment_scores(
    object_pc: np.ndarray,
    grasp_poses: np.ndarray,
    k_neighbors: int = 32,
) -> np.ndarray:
    object_pc = np.asarray(object_pc, dtype=np.float64)
    grasp_poses = np.asarray(grasp_poses, dtype=np.float64)
    scores = np.ones(len(grasp_poses), dtype=np.float32)

    for i, grasp_pose in enumerate(grasp_poses):
        grasp_position = grasp_pose[:3, 3]
        objectward_approach = grasp_pose[:3, 2]
        objectward_approach /= max(np.linalg.norm(objectward_approach), 1e-8)
        normal = estimate_local_surface_normal(
            object_pc=object_pc,
            query_point=grasp_position,
            k_neighbors=k_neighbors,
        )
        scores[i] = float(np.abs(np.dot(objectward_approach, normal)))

    return np.clip(scores, 0.0, 1.0)


def compute_total_scores(
    confidence: np.ndarray,
    centrality: np.ndarray,
    clearance: np.ndarray,
    surface_alignment: np.ndarray,
    weight_confidence: float = 0.5,
    weight_centrality: float = 0.2,
    weight_clearance: float = 0.2,
    weight_surface_alignment: float = 0.1,
) -> np.ndarray:
    confidence = _normalize_scores(confidence)
    total = (
        weight_confidence * confidence
        + weight_centrality * np.asarray(centrality, dtype=np.float32)
        + weight_clearance * np.asarray(clearance, dtype=np.float32)
        + weight_surface_alignment * np.asarray(surface_alignment, dtype=np.float32)
    )
    return total.astype(np.float32)

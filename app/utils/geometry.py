"""
AirMouse AI - Geometry Helpers Module.

Provides mathematical calculations for Euclidean distances, scale-invariant
hand size normalization, finger extension checks, and hand centroids.
"""

import math
from typing import Dict, List, Tuple, Any

# MediaPipe Landmark Indices
WRIST = 0

THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4

INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8

MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12

RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16

PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20


def math_clamp(val: int, min_val: int, max_val: int) -> int:
    """Clamps integer value to [min_val, max_val]."""
    return max(min_val, min(val, max_val))


def euclidean_distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculates 2D Euclidean distance between two points."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def euclidean_distance_3d(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    """Calculates 3D Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)


def calculate_hand_size(landmarks: List[Any]) -> float:
    """Calculates hand size reference scale based on Wrist to Middle MCP distance.

    Args:
        landmarks: List of HandLandmark objects (must contain at least 21 elements).

    Returns:
        float: Scale reference distance in normalized units (clamped > 0.001).
    """
    if not landmarks or len(landmarks) < 21:
        return 1.0

    w = (landmarks[WRIST].x, landmarks[WRIST].y)
    m = (landmarks[MIDDLE_MCP].x, landmarks[MIDDLE_MCP].y)
    dist = euclidean_distance_2d(w, m)
    return max(0.001, dist)


def calculate_normalized_distance(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    hand_size: float
) -> float:
    """Calculates 2D distance normalized by hand scale factor."""
    if hand_size <= 0.0001:
        hand_size = 1.0
    raw_dist = euclidean_distance_2d(p1, p2)
    return raw_dist / hand_size


def is_finger_extended(
    landmarks: List[Any],
    tip_id: int,
    pip_id: int,
    mcp_id: int,
    wrist_id: int = WRIST,
    ratio_threshold: float = 1.1
) -> bool:
    """Determines whether a finger is extended relative to the palm plane.

    Args:
        landmarks: List of 21 HandLandmark objects.
        tip_id: Landmark index of fingertip.
        pip_id: Landmark index of PIP joint.
        mcp_id: Landmark index of MCP joint.
        wrist_id: Landmark index of Wrist.
        ratio_threshold: Minimum tip-to-wrist vs mcp-to-wrist distance ratio.

    Returns:
        bool: True if finger is extended, False if folded into palm.
    """
    if not landmarks or len(landmarks) < 21:
        return False

    w = (landmarks[wrist_id].x, landmarks[wrist_id].y)
    tip = (landmarks[tip_id].x, landmarks[tip_id].y)
    pip = (landmarks[pip_id].x, landmarks[pip_id].y)
    mcp = (landmarks[mcp_id].x, landmarks[mcp_id].y)

    dist_tip = euclidean_distance_2d(tip, w)
    dist_pip = euclidean_distance_2d(pip, w)
    dist_mcp = euclidean_distance_2d(mcp, w)

    # Fingertip must be further from wrist than PIP and MCP joints
    return (dist_tip > dist_pip) and (dist_tip > dist_mcp * ratio_threshold)


def is_thumb_extended(landmarks: List[Any], ratio_threshold: float = 1.0) -> bool:
    """Determines whether the thumb is extended away from the index MCP joint."""
    if not landmarks or len(landmarks) < 21:
        return False

    thumb_tip = (landmarks[THUMB_TIP].x, landmarks[THUMB_TIP].y)
    index_mcp = (landmarks[INDEX_MCP].x, landmarks[INDEX_MCP].y)
    pinky_mcp = (landmarks[PINKY_MCP].x, landmarks[PINKY_MCP].y)
    wrist = (landmarks[WRIST].x, landmarks[WRIST].y)

    dist_thumb_index = euclidean_distance_2d(thumb_tip, index_mcp)
    hand_width = euclidean_distance_2d(index_mcp, pinky_mcp)

    return dist_thumb_index > (hand_width * 0.7 * ratio_threshold)


def get_finger_extension_states(
    landmarks: List[Any],
    ratio_threshold: float = 1.1
) -> Dict[str, bool]:
    """Returns extension states for all 5 fingers.

    Returns:
        Dict[str, bool]: Mapping finger name -> is_extended bool.
    """
    if not landmarks or len(landmarks) < 21:
        return {
            "thumb": False, "index": False, "middle": False, "ring": False, "pinky": False
        }

    return {
        "thumb": is_thumb_extended(landmarks, ratio_threshold),
        "index": is_finger_extended(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP, ratio_threshold=ratio_threshold),
        "middle": is_finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP, ratio_threshold=ratio_threshold),
        "ring": is_finger_extended(landmarks, RING_TIP, RING_PIP, RING_MCP, ratio_threshold=ratio_threshold),
        "pinky": is_finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP, ratio_threshold=ratio_threshold)
    }


def calculate_hand_center(landmarks: List[Any]) -> Tuple[float, float]:
    """Calculates the geometric center (centroid) of the palm."""
    if not landmarks or len(landmarks) < 21:
        return (0.5, 0.5)

    palm_ids = [WRIST, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP]
    avg_x = sum(landmarks[i].x for i in palm_ids) / len(palm_ids)
    avg_y = sum(landmarks[i].y for i in palm_ids) / len(palm_ids)
    return (avg_x, avg_y)

"""
rdm_get_warp.py - Get warp between two ResearchDoom frames

This module computes the pixel-wise warp/flow between two frames based on
depth maps and camera egomotion.

Copyright (c) 2016-26 Andrea Vedaldi
"""

import numpy as np


def rdm_get_warp(frame1, frame2):
    """
    Get warp between two frames.
    
    Computes arrays U, V containing the horizontal and vertical location
    of each pixel of frame2 in frame1. This is estimated from the depth map
    and ego motion. Results are not correct for sprites (which are flat) and
    moving objects.
    
    Args:
        frame1: First frame from rdm_get_frame()
        frame2: Second frame from rdm_get_frame()
        
    Returns:
        u1, v1: Arrays containing horizontal and vertical pixel locations
                in frame1 for each pixel in frame2
    """
    # Get 3D transformation from camera 2 back to camera 1
    A1 = get_player_transform(frame1)
    A2 = get_player_transform(frame2)
    A = np.linalg.inv(A1) @ A2
    
    # Camera matrix
    # From Doom source code, FOV computation:
    # ANG180 = 0x80000000
    # ANGLETOFINESHIFT = 19
    # FIELDOFVIEW = 2048
    # doomFov = FIELDOFVIEW / (ANG180/2^ANGLETOFINESHIFT) * pi
    #
    # Note: Doom shifts the view center slightly w.r.t. image center,
    # optical center is at pixel W/2+1
    # 
    # Small correction for scale due to Doom's angle shift in tangent tables
    
    doom_fov = np.pi / 2
    W = frame2['depthmap'].shape[1]
    H = frame2['depthmap'].shape[0]
    scale = np.tan(doom_fov / 2) / (W / 2) * 1.0007
    
    K = np.diag([scale, -scale, 1.0]) @ np.array([
        [1, 0, -W/2 - 1],
        [0, 1, -H/2 - 1],
        [0, 0, 1]
    ])
    iK = np.linalg.inv(K)
    
    # Get pixel coordinates in 3D space
    u2, v2 = np.meshgrid(np.arange(1, W + 1), np.arange(1, H + 1))
    x2 = K[0, 0] * u2 + K[0, 1] * v2 + K[0, 2]
    y2 = K[1, 0] * u2 + K[1, 1] * v2 + K[1, 2]
    
    # Get 3D points in camera 2
    depth = frame2['depthmap'].astype(np.float32) / (2**6)
    X2 = x2 * depth
    Y2 = y2 * depth
    Z2 = depth
    
    # Get 3D points in camera 1
    X1 = A[0, 0] * X2 + A[0, 1] * Y2 + A[0, 2] * Z2 + A[0, 3]
    Y1 = A[1, 0] * X2 + A[1, 1] * Y2 + A[1, 2] * Z2 + A[1, 3]
    Z1 = A[2, 0] * X2 + A[2, 1] * Y2 + A[2, 2] * Z2 + A[2, 3]
    
    # Project on image 1
    x1 = X1 / Z1
    y1 = Y1 / Z1
    u1 = iK[0, 0] * x1 + iK[0, 1] * y1 + iK[0, 2]
    v1 = iK[1, 0] * x1 + iK[1, 1] * y1 + iK[1, 2]
    
    return u1, v1


def get_player_transform(frame):
    """
    Get player transformation matrix.
    
    Args:
        frame: Frame dictionary with 'player' key
        
    Returns:
        4x4 transformation matrix
    """
    T = frame['player']['position']
    r = frame['player']['orientation'] - np.pi / 2
    
    A = np.array([
        [np.cos(r), 0, -np.sin(r), T[0]],
        [0,         1,  0,         T[2]],
        [np.sin(r), 0,  np.cos(r), T[1]],
        [0,         0,  0,         1]
    ])
    
    return A

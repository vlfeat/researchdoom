"""
rdm_test_warp.py - Demonstrate optical flow estimation with rdm_get_warp()

Copyright (c) 2016-26 Andrea Vedaldi
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

from .rdm_load import rdm_load
from .rdm_get_frame import rdm_get_frame
from .rdm_get_warp import rdm_get_warp


def rdm_test_warp(base_path='data/doomrecord', t1_idx=860, t2_idx=865):
    """
    Test optical flow/warp estimation between two frames.
    
    Args:
        base_path: Path to ResearchDoom recording
        t1_idx: Index of first frame in tics array
        t2_idx: Index of second frame in tics array
        
    Returns:
        Mean error value
    """
    # Load database
    rdb = rdm_load(base_path)
    
    # Get tics
    t1 = rdb['tics']['id'][t1_idx]
    t2 = rdb['tics']['id'][t2_idx]
    
    print(f"Computing warp from tic {t1} to tic {t2}")
    
    # Get frames
    f1 = rdm_get_frame(rdb, t1)
    f2 = rdm_get_frame(rdb, t2)
    
    # Get warp
    u, v = rdm_get_warp(f1, f2)
    
    # Convert indexed images to RGB
    if f1['rgb_colors'] is not None:
        im1 = f1['rgb_colors'][f1['rgb']]
    else:
        im1 = f1['rgb'] / 255.0
    
    if f2['rgb_colors'] is not None:
        im2 = f2['rgb_colors'][f2['rgb']]
    else:
        im2 = f2['rgb'] / 255.0
    
    # Warp image 1 to image 2 using interpolation
    h, w = im1.shape[:2]
    im2_warped = np.zeros_like(im2)
    
    # Create meshgrid for target coordinates
    v_grid, u_grid = np.mgrid[0:h, 0:w]
    
    for c in range(3):
        # Flatten arrays for interpolation
        valid_mask = ~np.isnan(u) & ~np.isnan(v)
        if np.any(valid_mask):
            # Use griddata for interpolation
            points = np.column_stack([v[valid_mask].ravel(), u[valid_mask].ravel()])
            values = im1[:, :, c][valid_mask].ravel()
            im2_warped[:, :, c] = griddata(
                points, values, (v_grid, u_grid),
                method='linear', fill_value=0
            )
    
    # Compute error
    err = np.sqrt(np.sum((im2_warped - im2)**2, axis=2))
    mean_err = np.nanmean(err)
    
    print(f"Mean warping error: {mean_err:.4f}")
    
    # Visualize results
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0, 0].imshow(im1)
    axes[0, 0].set_title('Frame 1')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(im2)
    axes[0, 1].set_title('Frame 2')
    axes[0, 1].axis('off')
    
    err_display = axes[1, 0].imshow(err, cmap='hot', vmin=0, vmax=3)
    axes[1, 0].set_title(f'Warping Error (mean={mean_err:.4f})')
    axes[1, 0].axis('off')
    plt.colorbar(err_display, ax=axes[1, 0])
    
    axes[1, 1].imshow(im2_warped)
    axes[1, 1].set_title('Frame 1 Warped to Frame 2')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig('warp_test.png')
    plt.show()
    
    # Interactive comparison (press any key to toggle)
    print("Showing interactive comparison. Close window to exit.")
    fig2 = plt.figure(figsize=(8, 6))
    
    while True:
        plt.clf()
        plt.imshow(im2)
        plt.title('Original Frame 2 - Press any key')
        plt.axis('off')
        try:
            plt.waitforbuttonpress()
        except:
            break
        
        plt.clf()
        plt.imshow(im2_warped)
        plt.title('Warped Frame 2 - Press any key')
        plt.axis('off')
        try:
            plt.waitforbuttonpress()
        except:
            break
    
    plt.close('all')
    
    return mean_err


def main():
    parser = argparse.ArgumentParser(description='Test optical flow estimation')
    parser.add_argument('--base-path', default='data/doomrecord',
                       help='Path to ResearchDoom recording')
    parser.add_argument('--t1', type=int, default=860,
                       help='Index of first frame')
    parser.add_argument('--t2', type=int, default=865,
                       help='Index of second frame')
    
    args = parser.parse_args()
    
    rdm_test_warp(args.base_path, args.t1, args.t2)


if __name__ == '__main__':
    main()

"""
rdm_test.py - Test rdm_load() and rdm_get_frame()

This script demonstrates loading ResearchDoom data and creating a video.

Copyright (c) 2016-26 Andrea Vedaldi
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
# Disable interactive mode so figures don't block on show()
plt.ioff()
from pathlib import Path
import imageio.v3 as iio

from .rdm_load import rdm_load
from .rdm_get_frame import rdm_get_frame


def rdm_test(base_path='data/cocodoom-raw', movie_path='data/doom.mp4', layout=(1, 4)):
    """
    Test ResearchDoom loading and frame extraction.
    
    Args:
        base_path: Path to ResearchDoom recording directory
        movie_path: Output video file path
        layout: Visualization layout (rows, cols)
    """
    # Load database
    rdb = rdm_load(base_path)
    
    # Plot object statistics
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    ax1.plot(rdb['objects']['endTic'], label='end')
    ax1.plot(rdb['objects']['startTic'], label='start')
    ax1.set_ylabel('tic')
    ax1.legend()
    ax1.set_title('Object Start/End Times')
    
    duration = rdb['objects']['endTic'] - rdb['objects']['startTic']
    ax2.plot(duration)
    ax2.set_ylabel('tic')
    ax2.set_title('Object Duration')
    
    plt.tight_layout()
    plt.savefig('object_stats.png')
    plt.close(fig)
    
    # Plot player trajectory
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    x = rdb['player']['position'][0, :]
    y = rdb['player']['position'][1, :]
    z = rdb['player']['position'][2, :]
    a = rdb['player']['orientation']
    
    ax.quiver(x, y, z, np.cos(a), np.sin(a), np.zeros_like(a), length=50)
    ax.plot(x, y, z, 'g-', linewidth=2, label='trajectory')
    ax.plot([x[0]], [y[0]], [z[0]], 'ro', markersize=8, label='start')
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Player Trajectory')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('player_trajectory.png')
    plt.close(fig)
    
    # Create video
    print(f"Creating video at {movie_path}...")
    Path(movie_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Determine video extent (up to end of second level)
    if len(rdb['levels']['endTic']) >= 2:
        stop_idx = np.where(rdb['tics']['id'] <= rdb['levels']['endTic'][1])[0]
        if len(stop_idx) > 0:
            stop_idx = stop_idx[-1]
        else:
            stop_idx = len(rdb['tics']['id'])
    else:
        stop_idx = len(rdb['tics']['id'])
    
    # Open video writer for incremental writing
    with iio.imopen(movie_path, 'w', plugin='pyav') as writer:
        writer.init_video_stream('libx264', fps=30)
        
        for i, tic in enumerate(rdb['tics']['id'][:min(len(rdb['tics']['id']), stop_idx)]):
            print(f"Processing frame {i+1}/{min(len(rdb['tics']['id']), stop_idx)}, tic={tic}")
            
            # Get frame (with visualization)
            frame = rdm_get_frame(rdb, tic, layout=layout, visualize=True)

            # Capture the current figure
            fig = plt.gcf()
            img = fig_to_array(fig)
            # Convert ARGB to RGB
            img_rgb = img[:, :, 1:4]
            
            writer.write_frame(img_rgb)
            plt.pause(0.001)
    
    print(f"Video saved to {movie_path}")


def main():
    parser = argparse.ArgumentParser(description='Test ResearchDoom data loading')
    parser.add_argument('--base-path', default='data/cocodoom-raw',
                       help='Path to ResearchDoom recording')
    parser.add_argument('--movie-path', default='data/doom.mp4',
                       help='Output video path')
    parser.add_argument('--layout-rows', type=int, default=1,
                        help='Visualization rows')
    parser.add_argument('--layout-cols', type=int, default=4,
                       help='Visualization columns')
    
    args = parser.parse_args()
    
    rdm_test(args.base_path, args.movie_path, (args.layout_rows, args.layout_cols))


def fig_to_array(fig):
    canvas = fig.canvas
    canvas.draw()

    # Get device pixel ratio
    w, h = canvas.get_width_height()
    w_, h_ = (fig.get_size_inches() * fig.dpi).astype(int)
    dpr = ((w / w_) + (h / h_)) / 2.0

    # Get buffer size
    w = int(w / dpr)
    h = int(h / dpr)

    buffer = canvas.tostring_argb()
    return np.frombuffer(buffer, dtype=np.uint8).reshape(h, w, 4)


if __name__ == '__main__':
    main()

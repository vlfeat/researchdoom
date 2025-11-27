"""
rdm_get_frame.py - Get ResearchDoom frame information

This module extracts information for a specific frame from a ResearchDoom database.

Copyright (c) 2016-26 Andrea Vedaldi
"""

import os
import numpy as np
import imageio.v3 as iio
from pathlib import Path
from skimage.measure import regionprops, label as sk_label
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d import Axes3D
from typing import Any, Dict, Optional, cast


def _make_matlab_colorcube(size: int) -> np.ndarray:
    """Return a MATLAB-compatible colorcube palette."""
    if size < 9:
        if size <= 0:
            return np.zeros((0, 3), dtype=np.float32)
        values = np.linspace(0.0, 1.0, size, dtype=np.float32)
        return np.column_stack((values, values, values))

    cube_len = int(np.cbrt(size))
    while (cube_len + 1) ** 3 <= size:
        cube_len += 1

    reserve = size - cube_len**3
    blue_levels = cube_len - 1 if reserve == 0 else cube_len
    level_values = np.linspace(0.0, 1.0, cube_len, dtype=np.float32)
    blue_values = np.linspace(0.0, 1.0, blue_levels, dtype=np.float32)

    r, g, b = np.meshgrid(level_values, level_values, blue_values, indexing="xy")
    palette = np.column_stack((r.ravel(), g.ravel(), b.ravel()))

    not_gray = np.any(palette[:, :1] != palette[:, 1:], axis=1)
    palette = palette[not_gray]

    pure_channel_count = np.sum(palette == 0.0, axis=1)
    palette = palette[pure_channel_count != 2]

    reserve = size - len(palette) - 1
    color_steps = reserve // 4
    gray_steps = reserve - 3 * color_steps

    if color_steps > 0:
        gradient = np.linspace(
            1.0 / color_steps, 1.0, color_steps, dtype=np.float32
        )[:, None]
        zeros = np.zeros_like(gradient)
        palette = np.vstack(
            (
                palette,
                np.hstack((gradient, zeros, zeros)),
                np.hstack((zeros, gradient, zeros)),
                np.hstack((zeros, zeros, gradient)),
            )
        )

    palette = np.vstack((palette, np.zeros((1, 3), dtype=np.float32)))

    if gray_steps > 0:
        gradient = np.linspace(1.0 / gray_steps, 1.0, gray_steps, dtype=np.float32)
        grays = np.column_stack((gradient, gradient, gradient))
        palette = np.vstack((palette, grays))

    return palette.astype(np.float32, copy=False)


_OBJECT_COLORS = np.vstack(
    (
        _make_matlab_colorcube(2**7),
        np.array(
            [
                [1.0, 1.0, 0.3],
                [0.5, 1.0, 0.3],
                [0.3, 0.7, 1.0],
            ],
            dtype=np.float32,
        ),
    )
)

_OBJECT_COLORMAP = ListedColormap(_OBJECT_COLORS, name="researchdoom_objects")


def rdm_get_frame(rdb, tic, layout=(1, 4), visualize=False):
    """
    Get ResearchDoom frame information.

    Args:
        rdb: ResearchDoom database from rdm_load()
        tic: Frame time identifier
        layout: Tuple (rows, cols) for visualization layout
        visualize: If True, visualize the frame

    Returns:
        Dictionary containing frame information:
        - rgb_path, rgb, rgb_colors: RGB image data
        - depthmap_path, depthmap: Depth map data
        - objectmap_path, objectmap: Object segmentation map
        - objects: Object information (frameId, id, label, box)
        - player: Player information (position, orientation)
    """
    # Find tic in database
    t_idx = np.where(rdb["tics"]["id"] == tic)[0]
    if len(t_idx) == 0:
        raise ValueError(f"Tic {tic} not found in RDB")
    t_idx = t_idx[0]

    # Figure out data layout
    map_path = Path(rdb["base_path"]) / f"map{rdb['tics']['level'][t_idx]:02d}"
    if map_path.exists():
        base_path = map_path
    else:
        base_path = Path(rdb["base_path"])

    frame = {}

    # Load RGB image
    frame["rgb_path"] = str(base_path / "rgb" / f"{tic:06d}.png")
    rgb_img = iio.imread(frame["rgb_path"])
    
    # Check if image is palette-based (single channel with palette metadata)
    if len(rgb_img.shape) == 2 or (len(rgb_img.shape) == 3 and rgb_img.shape[2] == 1):
        frame["rgb"] = rgb_img
        # Try to get palette from metadata if available
        try:
            metadata = iio.immeta(frame["rgb_path"])
            if 'palette' in metadata:
                frame["rgb_colors"] = np.array(metadata['palette']).reshape(-1, 3) / 255.0
            else:
                frame["rgb_colors"] = None
        except:
            frame["rgb_colors"] = None
    else:
        frame["rgb"] = rgb_img
        frame["rgb_colors"] = None

    # Load depth map
    frame["depthmap_path"] = str(base_path / "depth" / f"{tic:06d}.png")
    frame["depthmap"] = iio.imread(frame["depthmap_path"])

    # Load object map
    frame["objectmap_path"] = str(base_path / "objects" / f"{tic:06d}.png")
    obj_img = iio.imread(frame["objectmap_path"])

    # Combine RGB channels into single object ID
    frame["objectmap"] = (
        obj_img[:, :, 0].astype(np.uint32)
        + obj_img[:, :, 1].astype(np.uint32) * 256
        + obj_img[:, :, 2].astype(np.uint32) * 65536
    )

    # Extract visible object identities and bounding boxes
    ids = np.unique(frame["objectmap"])

    # Create labeled image for regionprops
    id_to_label = {obj_id: i for i, obj_id in enumerate(ids)}
    labeled = np.zeros_like(frame["objectmap"], dtype=int)
    for obj_id, lbl in id_to_label.items():
        if obj_id >= 2**23:  # Sky, walls, ground/ceiling
            continue
        labeled[frame["objectmap"] == obj_id] = lbl + 1

    props = regionprops(labeled)

    # Extract bounding boxes in the same half-pixel convention as MATLAB/Octave regionprops.
    boxes = []
    valid_ids = []
    for i, prop in enumerate(props):
        if prop.label > 0:
            minr, minc, maxr, maxc = prop.bbox
            boxes.append([minc + 0.5, minr + 0.5, maxc + 0.5, maxr + 0.5])
            # Find corresponding object ID
            for obj_id, lbl in id_to_label.items():
                if lbl + 1 == prop.label:
                    valid_ids.append(obj_id)
                    break

    boxes = (
        np.array(boxes, dtype=np.float32).T
        if boxes
        else np.zeros((4, 0), dtype=np.float32)
    )

    frame["objects"] = {
        "frameId": np.array(valid_ids, dtype=int),
        "id": np.zeros(len(valid_ids), dtype=int),
        "label": np.zeros(len(valid_ids), dtype=int),
        "box": boxes,
    }

    # Match object IDs with database
    for i, frame_id in enumerate(frame["objects"]["frameId"]):
        ok1 = (rdb["objects"]["id"] % (2**23)) == frame_id
        ok2 = rdb["objects"]["startTic"] <= tic
        ok3 = rdb["objects"]["endTic"] >= tic
        sel = np.where(ok1 & ok2 & ok3)[0]

        if len(sel) > 1:
            print(
                f"Warning: Ambiguous match for object with frameId {frame_id} at tic {tic}"
            )

        if len(sel) == 0:
            print(f"Warning: Unmatched object")
            frame["objects"]["id"][i] = -1
            frame["objects"]["label"][i] = -1
        else:
            match = sel[-1]
            frame["objects"]["id"][i] = rdb["objects"]["id"][match]
            frame["objects"]["label"][i] = rdb["objects"]["label"][match]

    # Get player info
    player_idx = np.where(rdb["player"]["tic"] == tic)[0]
    if len(player_idx) > 0:
        player_idx = player_idx[0]
        frame["player"] = {
            "position": rdb["player"]["position"][:, player_idx],
            "orientation": rdb["player"]["orientation"][player_idx],
        }
    else:
        frame["player"] = {"position": np.zeros(3), "orientation": 0.0}

    # Visualize if requested
    if visualize:
        visualize_frame(rdb, frame, tic, layout)

    return frame


# Cache for reusing figure and axes across calls
_viz_cache: Optional[Dict[str, Any]] = None

# {"fig": None, "axes": None, "layout": None}


def visualize_frame(rdb, frame, tic, layout):
    """Visualize frame information with fixed size and fast updates."""
    global _viz_cache
    rows, cols = layout

    # Reuse figure if layout matches, otherwise create new one
    if _viz_cache is None or _viz_cache["layout"] != layout:
        if _viz_cache is not None:
            plt.close(_viz_cache["fig"])

        # Create figure with exact size in inches
        fig = plt.figure(figsize=(cols * 4, rows * 3), dpi=100)
        fig.set_size_inches(cols * 4, rows * 3, forward=True)

        # Create subplots
        ax1 = plt.subplot(rows, cols, 1)
        ax2 = plt.subplot(rows, cols, 2)
        ax3 = plt.subplot(rows, cols, 3)
        ax4 = plt.subplot(rows, cols, 4, projection="3d")

        plt.tight_layout()

        _viz_cache = {"fig": fig, "axes": [ax1, ax2, ax3, ax4], "layout": layout}
    else:
        # Reuse
        fig = _viz_cache["fig"]
        ax1, ax2, ax3, ax4 = _viz_cache["axes"]
        ax1.clear()
        ax2.clear()
        ax3.clear()
        ax4.clear()

    # Lint: Type annotation for 3D axis
    ax4 = cast(Axes3D, ax4)

    # Prepare object labels
    strings = []
    for i in range(len(frame["objects"]["id"])):
        label_idx = np.where(frame["objects"]["label"][i] == rdb["classes"]["label"])[0]
        if len(label_idx) > 0:
            class_name = rdb["classes"]["name"][label_idx[0]]
        else:
            class_name = "UNKNOWN"
        strings.append(
            f"{frame['objects']['id'][i]}/{frame['objects']['label'][i]} ({class_name})"
        )

    # Plot 1: Depth map
    if len(frame["depthmap"].shape) == 2:
        ax1.imshow(frame["depthmap"], cmap="gray")
    ax1.set_title("Depth map")
    ax1.axis("off")

    # Plot 2: RGB with bounding boxes
    if frame["rgb_colors"] is not None:
        # Convert indexed image to RGB
        rgb_display = frame["rgb_colors"][frame["rgb"]]
    else:
        rgb_display = frame["rgb"]
    ax2.imshow(rgb_display)

    # Draw bounding boxes
    for i, box in enumerate(frame["objects"]["box"].T):
        x1, y1, x2, y2 = box
        rect = Rectangle(
            (x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="lime", linewidth=2
        )
        ax2.add_patch(rect)
        if i < len(strings):
            ax2.text(
                x1,
                y1 - 2,
                strings[i],
                color="lime",
                fontsize=6,
                bbox=dict(boxstyle="round", facecolor="black", alpha=0.5),
            )

    ax2.set_title(f"Appearance and objects (time {tic:06d})")
    ax2.axis("off")

    # Plot 3: Object segmentation
    obj_display = np.bitwise_and(frame["objectmap"], 255).astype(np.uint16)
    obj_display[frame["objectmap"] >= 2**23] += 2**7
    ax3.imshow(obj_display, cmap=_OBJECT_COLORMAP, norm=NoNorm())
    ax3.set_title("Class and instance segmentation")
    ax3.axis("off")

    # Plot 4: Ego-motion trajectory
    level_number = np.where(rdb["levels"]["startTic"] <= tic)[0][-1]
    level_name = rdb["levels"]["name"][level_number]

    sel = (rdb["levels"]["startTic"][level_number] <= rdb["player"]["tic"]) & (
        rdb["player"]["tic"] <= tic
    )

    x = rdb["player"]["position"][0, sel]
    y = rdb["player"]["position"][1, sel]
    z = rdb["player"]["position"][2, sel]
    a = rdb["player"]["orientation"][sel]

    ax4.quiver(x, y, z, np.cos(a), np.sin(a), np.zeros_like(a), length=50)
    ax4.plot(x, y, z, "g-", linewidth=2)
    ax4.plot([x[0]], [y[0]], [z[0]], "ro", markersize=8)
    ax4.set_xlabel("X")
    ax4.set_ylabel("Y")
    ax4.set_zlabel("Z")
    ax4.set_title(f"Ego-motion (level {level_name})")
    
    # Set bounds based on the entire level trajectory
    level_span = (rdb["levels"]["startTic"][level_number] <= rdb["player"]["tic"]) & (
        rdb["player"]["tic"] <= rdb["levels"]["endTic"][level_number]
    )
    x_all = rdb["player"]["position"][0, level_span]
    y_all = rdb["player"]["position"][1, level_span]
    z_all = rdb["player"]["position"][2, level_span]
    
    if len(x_all) > 0:
        # Keep per-axis data limits independent.
        x_range = x_all.max() - x_all.min()
        y_range = y_all.max() - y_all.min()
        z_range = z_all.max() - z_all.min()

        x_mid = (x_all.max() + x_all.min()) / 2
        y_mid = (y_all.max() + y_all.min()) / 2
        z_mid = (z_all.max() + z_all.min()) / 2
        
        margin_x = 0.05 * x_range
        margin_y = 0.05 * y_range
        margin_z = 0.2 * z_range

        ax4.set_xlim(x_mid - x_range/2 - margin_x, x_mid + x_range/2 + margin_x)
        ax4.set_ylim(y_mid - y_range/2 - margin_y, y_mid + y_range/2 + margin_y)
        ax4.set_zlim(z_mid - z_range/2 - margin_z, z_mid + z_range/2 + margin_z)

        # Keep the rendered 3D box cubic without forcing equal data ranges.
        # ax4.set_box_aspect([1, 1, 1])
        ax4.set_box_aspect([x_range, y_range, z_range])

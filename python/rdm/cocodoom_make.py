"""
cocodoom_make.py - Convert ResearchDoom output to COCO format

This module converts ResearchDoom recordings to MS COCO format for object detection.

Copyright (c) 2016-26 Andrea Vedaldi
"""

import os
import shutil
import argparse
from typing import cast
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy import ndimage

from .rdm_load import rdm_load
from .rdm_get_frame import rdm_get_frame
from .utils import (
    dp_simplify,
    json_array_one_item_per_line,
    json_coco_document,
    json_compact,
    write_text,
)


_BOUNDARY_ROW8 = np.array([-1, -1, 0, 1, 1, 1, 0, -1], dtype=np.int64)
_BOUNDARY_COL8 = np.array([0, 1, 1, 1, 0, -1, -1, -1], dtype=np.int64)
_BOUNDARY_BACK8 = np.array([7, 7, 1, 1, 3, 3, 5, 5], dtype=np.int64)
_BOUNDARY_NEXT8 = np.array([1, 2, 3, 4, 5, 6, 7, 0], dtype=np.int64)


def _trace_boundary_pixels(component_mask):
    """Trace one 8-connected component boundary following Octave __boundary__."""
    padded = np.pad(component_mask.astype(bool), 1, mode='constant')
    rows, cols = padded.shape
    region = padded.ravel(order='F')
    pixels = np.flatnonzero(region)

    if pixels.size == 0:
        return np.zeros((0, 2), dtype=np.float64)

    start = int(pixels[0])
    boundary = [start]

    if pixels.size == 1:
        boundary.append(start)
    else:
        moore_offsets = _BOUNDARY_ROW8 + rows * _BOUNDARY_COL8

        finish = 0
        for offset in moore_offsets:
            candidate = start + int(offset)
            if region[candidate]:
                finish = candidate

        bp = start
        current_dir = int(_BOUNDARY_NEXT8[0])
        done = False

        while not done:
            cp = bp + int(moore_offsets[current_dir])

            if not region[cp]:
                current_dir = int(_BOUNDARY_NEXT8[current_dir])
            else:
                boundary.append(cp)

                if bp == finish and cp == start:
                    done = True
                else:
                    bp = cp
                    current_dir = int(_BOUNDARY_BACK8[current_dir])

    boundary = np.asarray(boundary, dtype=np.int64)
    boundary_rows = boundary % rows
    boundary_cols = boundary // rows
    return np.column_stack((boundary_rows, boundary_cols)).astype(np.float64)


def _extract_boundary_polygons(mask):
    """Extract outer boundaries of all visible mask components."""
    labeled_result = cast(
        tuple[np.ndarray, int],
        ndimage.label(
            mask.astype(bool), structure=np.ones((3, 3), dtype=np.uint8)
        ),
    )
    labeled, num_components = labeled_result
    polygons = []
    component_keys = []

    for component_id in range(1, num_components + 1):
        component_mask = labeled == component_id
        component_pixels = np.flatnonzero(component_mask.ravel(order='F'))

        if component_pixels.size == 0:
            continue

        boundary_rc = _trace_boundary_pixels(component_mask)

        if boundary_rc.shape[0] < 4:
            continue

        component_keys.append(int(component_pixels[0]))
        polygons.append(boundary_rc[:, [1, 0]])

    if component_keys:
        order = np.argsort(np.asarray(component_keys))
        polygons = [polygons[idx] for idx in order]

    return polygons


def cocodoom_make(rdm_dir, coco_dir, run_id=1, run_name='run1',
                 tic_skip=1, use_symlinks=True, maps=None):
    """
    Convert ResearchDoom output to COCO format.
    
    Args:
        rdm_dir: ResearchDoom recording directory
        coco_dir: Output COCO directory
        run_id: Run identifier for image IDs
        run_name: Run name (e.g., 'run1')
        tic_skip: Sample every tic_skip frames (>=1)
        use_symlinks: Use symlinks instead of copying images (Unix only)
        maps: List of map indices to process (None = all maps)
    """
    # Load ResearchDoom database
    print(f'Loading ResearchDoom database {rdm_dir}')
    rdb = rdm_load(rdm_dir)
    
    # Prepare output directory
    run_path = Path(coco_dir) / run_name
    run_path.mkdir(parents=True, exist_ok=True)
    
    # Process each level/map
    if maps is None:
        maps = range(1, len(rdb['levels']['name']) + 1)
    
    for level_id in maps:
        level_name = f'map{level_id:02d}'
        qual_path = f'{run_name}/{level_name}'
        level_dir = Path(coco_dir) / qual_path
        
        if (level_dir / 'coco.json').exists():
            print(f'Skipping level {level_id} because it already exists ({level_dir / "coco.json"})')
            continue
        else:
            print(f'Processing level {level_id}')
        
        # Create output directories
        (level_dir / 'rgb').mkdir(parents=True, exist_ok=True)
        (level_dir / 'depth').mkdir(parents=True, exist_ok=True)
        (level_dir / 'objects').mkdir(parents=True, exist_ok=True)
        
        # Get tics for this level
        if level_id - 1 < len(rdb['levels']['startTic']):
            tic_start = rdb['levels']['startTic'][level_id - 1]
            tic_end = rdb['levels']['endTic'][level_id - 1]
        else:
            print(f'Level {level_id} not found in database, skipping')
            continue
        
        tics = rdb['tics']['id']
        tics = tics[(tics >= tic_start) & (tics <= tic_end)]
        
        image_list = []
        object_list = []
        
        # Process each frame
        for tic in tics[::tic_skip]:
            frame = rdm_get_frame(rdb, tic)
            
            # Create image entry in COCO format
            image_id = int(10e8 * run_id + 10e6 * level_id + tic)
            image_name = f'{tic:06d}.png'
            
            image_entry = {
                'id': image_id,
                'width': 320,
                'height': 200,
                'file_name': f'{qual_path}/rgb/{image_name}',
                'license': 1,
                'flickr_url': '',
                'coco_url': '',
                'date_captured': datetime.now().isoformat()
            }
            image_list.append(image_entry)
            
            # Copy or symlink images
            put_image(use_symlinks, frame['rgb_path'],
                     level_dir / 'rgb' / image_name)
            put_image(use_symlinks, frame['depthmap_path'],
                     level_dir / 'depth' / image_name)
            put_image(use_symlinks, frame['objectmap_path'],
                     level_dir / 'objects' / image_name)
            
            # Extract objects
            for i in range(len(frame['objects']['id'])):
                mask = (frame['objectmap'] == frame['objects']['frameId'][i])
                area = int(np.sum(mask))
                
                # Upsample mask for better contour extraction
                mask_up = np.repeat(np.repeat(mask.astype(bool), 4, axis=0), 4, axis=1)
                
                # Trace boundary pixels to match the legacy bwboundaries flow.
                contours = _extract_boundary_polygons(mask_up)
                
                poly_list = []
                for contour in contours:
                    one_poly = (contour - 2.5) / 4 + 1
                    
                    # Simplify polygon
                    if len(one_poly) > 2:
                        one_poly_simple, _ = dp_simplify(one_poly, 0.25)
                        one_poly_round = np.round(one_poly_simple * 2) / 2
                        one_poly_very_simple, _ = dp_simplify(one_poly_round, 0.75)
                        
                        # Flatten to [x1, y1, x2, y2, ...] and serialize as ints.
                        poly_flat = np.rint(one_poly_very_simple - 0.5).astype(int).flatten().tolist()
                        poly_list.append(poly_flat)
                
                # Bounding box
                box = frame['objects']['box'][:, i] - 1
                box_coco = np.rint([
                    box[0],
                    box[1],
                    box[2] - box[0] + 1,
                    box[3] - box[1] + 1,
                ]).astype(int).tolist()
                
                # Object ID (up to 14 decimal digits)
                object_id = int(image_id * 1e6 + frame['objects']['id'][i])
                
                object_entry = {
                    'id': object_id,
                    'image_id': image_id,
                    'category_id': int(frame['objects']['label'][i]),
                    'segmentation': poly_list,
                    'area': area,
                    'bbox': box_coco,
                    'iscrowd': 0
                }
                object_list.append(object_entry)
            
            print(f'Done: run {run_name}, level: {level_id}/{len(rdb["levels"]["name"])}, '
                  f'tic: {tic}/{max(tics)}')
        
        # Create COCO categories
        category_list = []
        for c in range(len(rdb['classes']['label'])):
            cat_entry = {
                'id': int(rdb['classes']['label'][c]),
                'name': rdb['classes']['name'][c],
                'supercategory': ''
            }
            category_list.append(cat_entry)
        
        # Create COCO info
        info = {
            'year': 2016,
            'version': 1,
            'description': 'ResearchDoom',
            'contributor': 'VGG',
            'url': '',
            'date_created': datetime.now().isoformat()
        }
        
        # Create COCO license
        license_entry = {
            'id': 1,
            'name': 'rdoom',
            'url': ''
        }
        
        # Assemble COCO annotation file
        coco_data = {
            'info': info,
            'images': image_list,
            'annotations': object_list,
            'categories': category_list,
            'licenses': [license_entry]
        }
        
        # Write JSON files
        write_text(str(level_dir / 'images.json'),
                  json_array_one_item_per_line(image_list))
        write_text(str(level_dir / 'objects.json'),
                  json_array_one_item_per_line(object_list))
        write_text(str(level_dir / 'categories.json'),
                  json_array_one_item_per_line(category_list))
        write_text(str(level_dir / 'info.json'),
                  json_compact(info))
        write_text(str(level_dir / 'license.json'),
                  json_array_one_item_per_line([license_entry]))
        write_text(str(level_dir / 'coco.json'),
                  json_coco_document(
                      info,
                      image_list,
                      object_list,
                      category_list,
                      [license_entry],
                  ))


def put_image(use_symlinks, src, dst):
    """Copy or symlink an image file."""
    if not dst.exists():
        if use_symlinks and os.name != 'nt':
            # Create relative or absolute symlink
            src_abs = Path(src).resolve()
            os.symlink(src_abs, dst)
        else:
            shutil.copyfile(src, dst)


def main():
    parser = argparse.ArgumentParser(description='Convert ResearchDoom to COCO format')
    parser.add_argument('rdm_dir', help='ResearchDoom recording directory')
    parser.add_argument('coco_dir', help='Output COCO directory')
    parser.add_argument('--run-id', type=int, default=1,
                       help='Run ID for image IDs')
    parser.add_argument('--run-name', default='run1',
                       help='Run name')
    parser.add_argument('--tic-skip', type=int, default=1,
                       help='Sample every tic-skip frames')
    parser.add_argument('--no-symlinks', action='store_true',
                       help='Copy files instead of symlinking')
    parser.add_argument('--maps', type=int, nargs='+',
                       help='Map indices to process (default: all)')
    
    args = parser.parse_args()
    
    cocodoom_make(args.rdm_dir, args.coco_dir,
                 run_id=args.run_id,
                 run_name=args.run_name,
                 tic_skip=args.tic_skip,
                 use_symlinks=not args.no_symlinks,
                 maps=args.maps)


if __name__ == '__main__':
    main()

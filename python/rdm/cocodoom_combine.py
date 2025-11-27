"""
cocodoom_combine.py - Merge CocoDoom annotation files

Copyright (c) 2016-26 Andrea Vedaldi
"""

import json
import argparse
from pathlib import Path

from .utils import json_coco_document, write_text


def cocodoom_combine(src_files, dst_file, skip=1, min_area=30, categories=None):
    """
    Merge multiple COCO annotation files into one.
    
    Args:
        src_files: List of source COCO JSON file paths
        dst_file: Destination COCO JSON file path
        skip: Sample every 'skip' images
        min_area: Minimum object area to keep
        categories: List of category IDs to keep (None = all)
        
    Returns:
        List of image file names included
    """
    print(f'cocodoom_combine: producing {dst_file}')
    
    # Load all source files
    src_objs = []
    for src_file in src_files:
        with open(src_file, 'r') as f:
            src_objs.append(json.load(f))
    
    # Start with first file
    dst_obj = src_objs[0].copy()
    
    # Merge images and annotations from other files
    for i in range(1, len(src_objs)):
        dst_obj['images'].extend(src_objs[i]['images'])
        dst_obj['annotations'].extend(src_objs[i]['annotations'])
    
    # Skip some images if needed
    dst_obj['images'] = dst_obj['images'][::skip]
    
    # Keep only annotations for retained images
    image_ids = {img['id'] for img in dst_obj['images']}
    dst_obj['annotations'] = [
        ann for ann in dst_obj['annotations']
        if ann['image_id'] in image_ids
    ]
    
    # Filter by area and categories
    filtered_anns = []
    for ann in dst_obj['annotations']:
        if ann['area'] >= min_area:
            if categories is None or ann['category_id'] in categories:
                filtered_anns.append(ann)
    dst_obj['annotations'] = filtered_anns
    
    # Remove unused categories
    used_category_ids = {ann['category_id'] for ann in dst_obj['annotations']}
    dst_obj['categories'] = [
        cat for cat in dst_obj['categories']
        if cat['id'] in used_category_ids
    ]
    
    # Save the JSON file using the same compact formatting as per-map exports.
    Path(dst_file).parent.mkdir(parents=True, exist_ok=True)
    write_text(
        dst_file,
        json_coco_document(
            dst_obj['info'],
            dst_obj['images'],
            dst_obj['annotations'],
            dst_obj['categories'],
            dst_obj['licenses'],
        ),
    )
    
    # Return list of images used
    images = [img['file_name'] for img in dst_obj['images']]
    return images


def main():
    parser = argparse.ArgumentParser(description='Combine COCO annotation files')
    parser.add_argument('src_files', nargs='+',
                       help='Source COCO JSON files')
    parser.add_argument('dst_file',
                       help='Destination COCO JSON file')
    parser.add_argument('--skip', type=int, default=1,
                       help='Sample every skip images')
    parser.add_argument('--min-area', type=float, default=30,
                       help='Minimum object area')
    parser.add_argument('--categories', type=int, nargs='+',
                       help='Category IDs to keep')
    
    args = parser.parse_args()
    
    images = cocodoom_combine(args.src_files, args.dst_file,
                             skip=args.skip,
                             min_area=args.min_area,
                             categories=args.categories)
    
    print(f'Included {len(images)} images')


if __name__ == '__main__':
    main()

"""
cocodoom_test.py - Test the CocoDoom dataset

Copyright (c) 2016-26 Andrea Vedaldi
"""

import argparse
from pathlib import Path
from pycocotools.coco import COCO


def cocodoom_test(data_path='data/cocodoom'):
    """Test CocoDoom dataset splits."""
    data_path = Path(data_path)
    
    split_files = [
        data_path / 'map-full-train.json',
        data_path / 'map-full-val.json',
        data_path / 'map-full-test.json',
        data_path / 'map-train.json',
        data_path / 'map-val.json',
        data_path / 'map-test.json',
        data_path / 'run-full-train.json',
        data_path / 'run-full-val.json',
        data_path / 'run-full-test.json',
        data_path / 'run-train.json',
        data_path / 'run-val.json',
        data_path / 'run-test.json',
    ]
    
    stats = []
    
    for file_path in split_files:
        if Path(file_path).exists():
            stat = get_stats(file_path)
            stats.append(stat)
    
    # Print table
    print('|{:15s}|{:10s}|{:10s}|'.format('split', 'images', 'objects'))
    print('|{:15s}|{:10s}|{:10s}|'.format('-' * 15, '-' * 10, '-' * 10))
    
    for stat in stats:
        print('|{:15s}|{:10d}|{:10d}|'.format(stat['name'], stat['images'], stat['objects']))


def get_stats(file_path):
    """Get statistics for a COCO annotation file."""
    print(f'==== {file_path} ====')
    
    coco = COCO(file_path)
    cats = coco.loadCats(coco.getCatIds())
    
    name = Path(file_path).stem
    cat_names = [cat['name'] for cat in cats]
    n_images = len(coco.getImgIds())
    n_objects = len(coco.getAnnIds())
    
    print(f'{n_images} images, {n_objects} objects')
    
    return {
        'name': name,
        'cat_names': cat_names,
        'images': n_images,
        'objects': n_objects
    }


def main():
    parser = argparse.ArgumentParser(description='Test CocoDoom dataset')
    parser.add_argument('--data-path', default='data/cocodoom',
                       help='Base path to CocoDoom annotation files')
    args = parser.parse_args()
    
    cocodoom_test(args.data_path)


if __name__ == '__main__':
    main()

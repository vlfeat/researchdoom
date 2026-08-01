"""
cocodoom_split.py - Generate standard CocoDoom train/val/test splits

Copyright (c) 2016-26 Andrea Vedaldi
"""

import argparse
from pathlib import Path
from pycocotools.coco import COCO

from .cocodoom_combine import cocodoom_combine
from .utils import write_text


def cocodoom_split(data_dir='data/cocodoom'):
    """
    Generate standard CocoDoom train/val/test splits.
    
    Creates splits based on:
    1. Player splits: run1=train, run2=val, run3=test
    2. Map splits: maps (0,1 mod 4)=train, map (2 mod 4)=val, map (3 mod 4)=test
    
    Args:
        data_dir: CocoDoom data directory
    """
    data_dir = Path(data_dir)
    
    # Copy metadata
    for r in range(1, 4):
        raw_root = data_dir.parent / 'cocodoom-raw'
        src = raw_root / f'cocodoom_run{r}' / 'log.txt'
        if not src.exists():
            src = raw_root / f'run{r}' / 'log.txt'
        dst = data_dir / f'run{r}' / 'log.txt'
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy(src, dst)
    
    standard_images = []
    full_images = []
    
    # ========================================================================
    # Get player splits
    # ========================================================================
    train_files = []
    val_files = []
    test_files = []
    
    for run in range(1, 4):
        for map_id in range(1, 33):
            json_file = data_dir / f'run{run}' / f'map{map_id:02d}' / 'coco.json'
            if json_file.exists():
                if run == 1:
                    train_files.append(str(json_file))
                elif run == 2:
                    val_files.append(str(json_file))
                elif run == 3:
                    test_files.append(str(json_file))
    
    # Get statistics and select categories
    print("Computing training set statistics...")
    train_path = str(data_dir / 'run-train.json')
    cocodoom_combine(train_files, train_path, skip=5)
    
    coco = COCO(train_path)
    cats = coco.loadCats(coco.getCatIds())
    
    num_instances = {}
    for cat in cats:
        ann_ids = coco.getAnnIds(catIds=[cat['id']])
        num_instances[cat['id']] = len(ann_ids)
    
    # Select categories with at least 100 instances
    sel_cats = [cat_id for cat_id, count in num_instances.items() if count >= 100]
    print(f'Selected {len(sel_cats)} categories out of {len(num_instances)}')
    
    # Create standard splits (subsampled)
    standard_images.extend(
        cocodoom_combine(train_files, str(data_dir / 'run-train.json'),
                        skip=5, categories=sel_cats))
    standard_images.extend(
        cocodoom_combine(val_files, str(data_dir / 'run-val.json'),
                        skip=20, categories=sel_cats))
    standard_images.extend(
        cocodoom_combine(test_files, str(data_dir / 'run-test.json'),
                        skip=20, categories=sel_cats))
    
    # Create full splits (all frames)
    full_images.extend(
        cocodoom_combine(train_files, str(data_dir / 'run-full-train.json'),
                        categories=sel_cats))
    full_images.extend(
        cocodoom_combine(val_files, str(data_dir / 'run-full-val.json'),
                        categories=sel_cats))
    full_images.extend(
        cocodoom_combine(test_files, str(data_dir / 'run-full-test.json'),
                        categories=sel_cats))
    
    # ========================================================================
    # Get map splits
    # ========================================================================
    train_files = []
    val_files = []
    test_files = []
    
    for run in range(1, 4):
        for map_id in range(1, 33):
            json_file = data_dir / f'run{run}' / f'map{map_id:02d}' / 'coco.json'
            if json_file.exists():
                if (map_id - 1) % 4 <= 1:
                    train_files.append(str(json_file))
                elif (map_id - 1) % 4 == 2:
                    val_files.append(str(json_file))
                else:
                    test_files.append(str(json_file))
    
    # Create standard splits
    standard_images.extend(
        cocodoom_combine(train_files, str(data_dir / 'map-train.json'),
                        skip=5, categories=sel_cats))
    standard_images.extend(
        cocodoom_combine(val_files, str(data_dir / 'map-val.json'),
                        skip=20, categories=sel_cats))
    standard_images.extend(
        cocodoom_combine(test_files, str(data_dir / 'map-test.json'),
                        skip=20, categories=sel_cats))
    
    # Create full splits
    full_images.extend(
        cocodoom_combine(train_files, str(data_dir / 'map-full-train.json'),
                        categories=sel_cats))
    full_images.extend(
        cocodoom_combine(val_files, str(data_dir / 'map-full-val.json'),
                        categories=sel_cats))
    full_images.extend(
        cocodoom_combine(test_files, str(data_dir / 'map-full-test.json'),
                        categories=sel_cats))
    
    # Write image lists
    standard_images = sorted(set(standard_images))
    full_images = sorted(set(full_images))
    
    write_text(str(data_dir / 'images.txt'), '\n'.join(standard_images))
    write_text(str(data_dir / 'images-full.txt'), '\n'.join(full_images))
    
    print(f'Standard split: {len(standard_images)} unique images')
    print(f'Full split: {len(full_images)} unique images')


def main():
    parser = argparse.ArgumentParser(description='Generate CocoDoom splits')
    parser.add_argument('--data-dir', default='data/cocodoom',
                       help='CocoDoom data directory')
    
    args = parser.parse_args()
    cocodoom_split(args.data_dir)


if __name__ == '__main__':
    main()

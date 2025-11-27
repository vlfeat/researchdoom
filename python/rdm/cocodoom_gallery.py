"""
cocodoom_gallery.py - Produce a gallery of CocoDoom categories

Copyright (c) 2016-26 Andrea Vedaldi
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from pycocotools.coco import COCO


def cocodoom_gallery(coco_path='data/cocodoom/run-train.json',
                    data_path='data/cocodoom',
                    output_path='data/cocodoom-gallery.png'):
    """
    Create a gallery visualization of CocoDoom categories.
    
    Args:
        coco_path: Path to COCO annotation file
        data_path: Base path to image data
        output_path: Output image path
    """
    coco = COCO(coco_path)
    cats = coco.loadCats(coco.getCatIds())
    
    M = 14  # rows
    N = 7   # cols
    aspect_ratio = 320 / 200
    
    fig = plt.figure(figsize=(N * 3.2 * aspect_ratio, M * 3.2))
    
    for c, cat in enumerate(cats):
        if c >= M * N:
            break
        
        ann_ids = coco.getAnnIds(catIds=[cat['id']])
        print(f"{c+1:03d}) id:{cat['id']:03d} name:{cat['name']:10s} inst:{len(ann_ids)}")
        
        anns = coco.loadAnns(ann_ids)
        
        if len(anns) == 0:
            continue
        
        # Find best annotation (largest, centered, complete)
        bboxes = np.array([ann['bbox'] for ann in anns])  # [x, y, w, h]
        areas = np.array([ann['area'] for ann in anns])
        
        # Convert to [x1, y1, x2, y2]
        boxes = np.zeros((len(bboxes), 4))
        boxes[:, 0] = bboxes[:, 0]
        boxes[:, 1] = bboxes[:, 1]
        boxes[:, 2] = bboxes[:, 0] + bboxes[:, 2]
        boxes[:, 3] = bboxes[:, 1] + bboxes[:, 3]
        
        height = boxes[:, 3] - boxes[:, 1]
        width = boxes[:, 2] - boxes[:, 0]
        
        # Keep only complete objects (not on image boundary)
        keep = ((boxes[:, 0] > 1) & (boxes[:, 1] > 1) &
                (boxes[:, 2] < 320) & (boxes[:, 3] < 200))
        keep = keep & (areas / (height * width) > 0.5)
        
        # Score by size
        score = height / 200 + 0.5 * width / 200
        score[~keep] = -np.inf
        
        if np.all(score == -np.inf):
            sel = 0
        else:
            sel = np.argmax(score)
        
        ann = anns[sel]
        
        # Load image
        img_info = coco.loadImgs([ann['image_id']])[0]
        img_path = Path(data_path) / img_info['file_name']
        
        img = Image.open(img_path)
        if img.mode == 'P':
            img = img.convert('RGB')
        img = np.array(img)
        
        # Plot
        i = M - (c // N) - 1
        j = c % N
        
        ax = plt.axes([j/N, i/M, 1/N, 1/M])
        ax.imshow(img)
        
        # Draw segmentation
        if 'segmentation' in ann and len(ann['segmentation']) > 0:
            for seg in ann['segmentation']:
                if len(seg) >= 2:
                    seg_array = np.array(seg).reshape(-1, 2)
                    ax.plot(seg_array[:, 0], seg_array[:, 1], 'k-', linewidth=1)
                    ax.plot(seg_array[:, 0], seg_array[:, 1], 'y-', linewidth=0.5)
        
        # Add label
        ax.text(0.5, 0.95, cat['name'],
               transform=ax.transAxes,
               fontsize=6,
               fontweight='bold',
               ha='center',
               va='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.axis('off')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'Gallery saved to {output_path}')
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Create CocoDoom category gallery')
    parser.add_argument('--coco-path', default='data/cocodoom/run-train.json',
                       help='Path to COCO annotation file')
    parser.add_argument('--data-path', default='data/cocodoom',
                       help='Base path to image data')
    parser.add_argument('--output-path', default='data/cocodoom-gallery.png',
                       help='Output image path')
    
    args = parser.parse_args()
    
    cocodoom_gallery(args.coco_path, args.data_path, args.output_path)


if __name__ == '__main__':
    main()

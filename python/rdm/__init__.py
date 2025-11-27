"""
ResearchDoom Python Library

A Python port of the ResearchDoom MATLAB library for loading and processing
ResearchDoom game recordings with depth, object segmentation, and metadata.

Modules:
    - rdm_load: Load ResearchDoom database
    - rdm_get_frame: Extract frame information
    - rdm_get_warp: Compute optical flow between frames
    - rdm_test: Test and visualization scripts
    - cocodoom_*: COCO format conversion utilities

Copyright (c) 2016-26 Andrea Vedaldi
"""

__version__ = '1.0.0'
__author__ = 'Andrea Vedaldi (original MATLAB), Python port contributors'

from .rdm_load import rdm_load
from .rdm_get_frame import rdm_get_frame
from .rdm_get_warp import rdm_get_warp

__all__ = [
    'rdm_load',
    'rdm_get_frame',
    'rdm_get_warp',
]

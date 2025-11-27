"""
rdm_load.py - Load ResearchDoom database

This module provides functionality to load ResearchDoom metadata from a directory
written by the ResearchDoom engine.

Copyright (c) 2016-26 Andrea Vedaldi
"""

import re
import os
import numpy as np
from pathlib import Path
from typing import Any, Dict

from .rdm import get_class_names

def rdm_load(base_path):
    """
    Load ResearchDoom database.
    
    The database contains information required to interpret the ResearchDoom objectmaps. It also contains information about the player and camera location.

    Args:
        base_path: Directory path written by the ResearchDoom engine
        
    Returns:
        Dictionary containing the ResearchDoom database with keys:
        - base_path: Base path to the data
        - player: Player information (tic, position, orientation)
        - objects: Object information (id, startTic, endTic, label)
        - levels: Level information (name, startTic, endTic)
        - tics: Tic information (id, level)
        - classes: Class information (name, label)
    """
    base_path = Path(base_path)
    
    # Read log file
    with open(base_path / 'log.txt', 'r') as f:
        text = f.read()

    # Initialize database dictionary
    rdb: Dict[str, Any] = {'base_path': str(base_path)}
    
    # Get player and tics
    player_pattern = r'(\d+) player:([\de.,-]+)'
    tokens = re.finditer(player_pattern, text)
    
    player_tics = []
    player_positions = []
    player_orientations = []
    
    for match in tokens:
        tic = int(match.group(1))
        coords = match.group(2)
        xyza = [float(x) for x in coords.split(',')]
        
        player_tics.append(tic)
        player_positions.append(xyza[:3])
        player_orientations.append(xyza[3])
    
    rdb['player'] = {
        'tic': np.array(player_tics, dtype=int),
        'position': np.array(player_positions, dtype=np.float32).T,  # 3 x N
        'orientation': np.array(player_orientations, dtype=np.float32)
    }
    
    # Get objects
    object_pattern = r'(\d+) spawn:(\d+) type:(\d+) \[([\d\w]+)\]'
    tokens = re.finditer(object_pattern, text)
    
    object_ids = []
    object_start_tics = []
    object_end_tics = []
    object_labels = []
    
    for match in tokens:
        start_tic = int(match.group(1))
        obj_id = int(match.group(2))
        obj_type = int(match.group(3))
        
        object_ids.append(obj_id)
        object_start_tics.append(start_tic)
        object_end_tics.append(np.iinfo(np.int64).max)
        object_labels.append(obj_type)
    
    # Get object removal times
    remove_pattern = r'(\d+) remove:(\d+)'
    tokens = re.finditer(remove_pattern, text)
    
    object_ids = np.array(object_ids, dtype=int)
    object_start_tics = np.array(object_start_tics, dtype=int)
    object_end_tics = np.array(object_end_tics)
    object_labels = np.array(object_labels, dtype=int)
    
    for match in tokens:
        tic = int(match.group(1))
        obj_id = int(match.group(2))
        idx = np.where(object_ids == obj_id)[0]
        if len(idx) > 0:
            object_end_tics[idx[0]] = tic
    
    rdb['objects'] = {
        'id': object_ids,
        'startTic': object_start_tics,
        'endTic': object_end_tics,
        'label': object_labels
    }
    
    # Get levels
    level_pattern = r'(\d+) level loaded: ([\d\w]+)'
    tokens = list(re.finditer(level_pattern, text))
    
    level_names = []
    level_start_tics = []
    
    for match in tokens:
        start_tic = int(match.group(1))
        level_name = match.group(2)
        
        level_names.append(level_name)
        level_start_tics.append(start_tic)
    
    level_start_tics = np.array(level_start_tics, dtype=int)
    level_end_tics = np.concatenate([
        level_start_tics[1:] - 1,
        [rdb['player']['tic'].max()]
    ])
    
    rdb['levels'] = {
        'name': level_names,
        'startTic': level_start_tics,
        'endTic': level_end_tics
    }
    
    # Get tics
    tic_ids = rdb['player']['tic']
    tic_levels = np.digitize(tic_ids, 
                             np.concatenate([level_start_tics, [level_end_tics[-1] + 1]]))
    
    rdb['tics'] = {
        'id': tic_ids,
        'level': tic_levels
    }
    
    # Get classes
    rdb['classes'] = {
        'name': get_class_names(),
        'label': np.arange(len(get_class_names()), dtype=int)
    }
    
    return rdb


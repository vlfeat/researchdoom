"""
Helper utilities for ResearchDoom Python port

Copyright (c) 2025
"""

import json
from pathlib import Path


def write_text(file_name, txt):
    """
    Write text to file.
    
    Args:
        file_name: Path to output file
        txt: Text string to write
    """
    with open(file_name, 'w') as f:
        f.write(txt)


def json_compact(value):
    """Serialize one JSON value without extra whitespace."""
    return json.dumps(value, separators=(',', ':'))


def json_array_one_item_per_line(items, indent=0):
    """Serialize a JSON array with one compact item per physical line."""
    prefix = ' ' * indent
    if not items:
        return '[]'

    item_prefix = ' ' * (indent + 2)
    body = ',\n'.join(f'{item_prefix}{json_compact(item)}' for item in items)
    return f'[\n{body}\n{prefix}]'


def json_coco_document(info, images, annotations, categories, licenses):
    """Serialize a COCO document compactly while keeping array items readable."""
    parts = [
        f'  "info": {json_compact(info)}',
        f'  "images": {json_array_one_item_per_line(images, indent=2)}',
        f'  "annotations": {json_array_one_item_per_line(annotations, indent=2)}',
        f'  "categories": {json_array_one_item_per_line(categories, indent=2)}',
        f'  "licenses": {json_array_one_item_per_line(licenses, indent=2)}',
    ]
    return '{\n' + ',\n'.join(parts) + '\n}'


def dp_simplify(p, tol):
    """
    Recursive Douglas-Peucker Polyline Simplification.
    
    Simplifies a piecewise linear curve by reducing vertices according to
    a specified tolerance using the Douglas-Peucker algorithm.
    
    Args:
        p: Polyline as n x d numpy array (n vertices in d dimensions)
        tol: Tolerance (maximal euclidean distance allowed between
             simplified line and a vertex)
             
    Returns:
        ps: Simplified polyline
        ix: Indices of retained vertices (ps = p[ix])
    """
    import numpy as np
    
    if tol < 0:
        raise ValueError('tol must be a positive scalar')
    
    n_vertices = p.shape[0]
    dims = p.shape[1]
    
    # Handle edge cases
    if n_vertices == 1 or len(p) == 0:
        return p, np.array([0])
    
    if n_vertices == 2:
        if dims == 2:
            d = np.hypot(p[0, 0] - p[1, 0], p[0, 1] - p[1, 1])
        else:
            d = np.sqrt(np.sum((p[0, :] - p[1, :])**2))
        
        if d <= tol:
            return np.mean(p, axis=0, keepdims=True), np.array([0])
        else:
            return p, np.array([0, 1])
    
    # Check for NaN values
    i_nan = np.any(np.isnan(p), axis=1)
    
    if np.any(i_nan):
        # Handle NaN-separated polylines recursively
        i_nan_inv = ~i_nan
        
        # Find contiguous segments
        changes = np.diff(np.concatenate([[0], i_nan_inv.astype(int), [0]]))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        
        results = []
        indices = []
        
        for start, end in zip(starts, ends):
            segment = p[start:end, :]
            ps_seg, ix_seg = dp_simplify(segment, tol)
            results.append(ps_seg)
            indices.append(ix_seg + start)
            results.append(np.full((1, dims), np.nan))  # NaN separator
        
        if results:
            results = results[:-1]  # Remove last NaN
            ps = np.vstack(results)
            ix = np.concatenate(indices)
        else:
            ps = p
            ix = np.arange(n_vertices)
        
        return ps, ix
    
    # No NaN values - perform standard simplification
    I = np.ones(n_vertices, dtype=bool)
    
    def simplify_rec(ixs, ixe):
        """Recursive simplification helper."""
        # Check if start and endpoints are the same
        same_se = np.allclose(p[ixs, :], p[ixe, :], rtol=1e-9)
        
        if same_se:
            # Distance to start point only
            if dims == 2:
                d = np.hypot(p[ixs, 0] - p[ixs+1:ixe, 0],
                           p[ixs, 1] - p[ixs+1:ixe, 1])
            else:
                d = np.sqrt(np.sum((p[ixs, :] - p[ixs+1:ixe, :])**2, axis=1))
        else:
            # Distance to line from start to end
            pt = p[ixs+1:ixe, :] - p[ixs, :]
            a = p[ixe, :] - p[ixs, :]
            
            beta = np.dot(pt, a) / np.dot(a, a)
            b = pt - np.outer(beta, a)
            
            if dims == 2:
                d = np.hypot(b[:, 0], b[:, 1])
            else:
                d = np.sqrt(np.sum(b**2, axis=1))
        
        if len(d) == 0:
            return
        
        # Find maximum distance
        dmax = np.max(d)
        ixc = ixs + 1 + np.argmax(d)
        
        if dmax <= tol:
            # Remove all intermediate vertices
            if ixs != ixe - 1:
                I[ixs+1:ixe] = False
        else:
            # Recursively simplify segments
            simplify_rec(ixs, ixc)
            simplify_rec(ixc, ixe)
    
    simplify_rec(0, n_vertices - 1)
    
    ps = p[I, :]
    ix = np.where(I)[0]
    
    return ps, ix

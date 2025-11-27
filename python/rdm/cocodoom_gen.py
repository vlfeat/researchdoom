"""
cocodoom_gen.py - Generate CocoDoom dataset from multiple runs and maps

Copyright (c) 2016-26 Andrea Vedaldi
"""

import argparse
from pathlib import Path
from multiprocessing import Pool

from .cocodoom_make import cocodoom_make


def cocodoom_gen(data_dir='data'):
    """
    Generate CocoDoom dataset from multiple runs and maps.
    
    Args:
        data_dir: Base data directory containing cocodoom-raw recordings
    """
    data_dir = Path(data_dir)
    
    # Define jobs (run, map combinations)
    jobs = []
    for run in range(1, 4):  # runs 1-3
        for map_id in range(1, 33):  # maps 1-32
            jobs.append({
                'run': run,
                'map': map_id
            })
    
    # Process jobs (can be parallelized)
    def process_job(job):
        run = job['run']
        map_id = job['map']
        run_name = f'run{run}'
        
        print(f'### run{run} map{map_id}')
        
        cocodoom_make(
            str(data_dir / 'cocodoom-raw' / run_name),
            str(data_dir / 'cocodoom'),
            run_id=run,
            run_name=run_name,
            maps=[map_id]
        )
    
    # Process sequentially or in parallel
    for job in jobs:
        process_job(job)
    
    # For parallel processing, uncomment:
    # with Pool() as pool:
    #     pool.map(process_job, jobs)


def main():
    parser = argparse.ArgumentParser(description='Generate CocoDoom dataset')
    parser.add_argument('--data-dir', default='data',
                       help='Base data directory')
    
    args = parser.parse_args()
    cocodoom_gen(args.data_dir)


if __name__ == '__main__':
    main()

import sys
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Union
from urllib.request import urlretrieve

import hydra
from omegaconf import DictConfig, OmegaConf
import hashlib
import os
import subprocess
import imageio.v3 as iio
import numpy as np


def get_overview_grid(num_frames: int, tile_shape, target_aspect: float = 16 / 9):
    if num_frames <= 0:
        raise ValueError("num_frames must be positive")

    tile_height, tile_width = tile_shape[:2]
    tile_aspect = tile_width / tile_height

    best_rows = 1
    best_cols = num_frames
    best_score = None

    for cols in range(1, num_frames + 1):
        rows = int(np.ceil(num_frames / cols))
        aspect = (cols * tile_aspect) / rows
        padding = rows * cols - num_frames
        score = (abs(aspect - target_aspect), padding)

        if best_score is None or score < best_score:
            best_rows = rows
            best_cols = cols
            best_score = score

    return best_rows, best_cols


def get_md5(file_path: Union[str, Path]) -> str:
    """Compute the MD5 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        MD5 checksum as a hexadecimal string.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# fmt: off
def get_class_names():
    """Return list of Doom object class names."""
    return [
        'PLAYER', 'POSSESSED', 'SHOTGUY', 'VILE', 'FIRE', 'UNDEAD', 'TRACER',
        'SMOKE', 'FATSO', 'FATSHOT', 'CHAINGUY', 'TROOP', 'SERGEANT', 'SHADOWS',
        'HEAD', 'BRUISER', 'BRUISERSHOT', 'KNIGHT', 'SKULL', 'SPIDER', 'BABY',
        'CYBORG', 'PAIN', 'WOLFSS', 'KEEN', 'BOSSBRAIN', 'BOSSSPIT', 'BOSSTARGET',
        'SPAWNSHOT', 'SPAWNFIRE', 'BARREL', 'TROOPSHOT', 'HEADSHOT', 'ROCKET',
        'PLASMA', 'BFG', 'ARACHPLAZ', 'PUFF', 'BLOOD', 'TFOG', 'IFOG',
        'TELEPORTMAN', 'EXTRABFG', 'MISC0', 'MISC1', 'MISC2', 'MISC3', 'MISC4',
        'MISC5', 'MISC6', 'MISC7', 'MISC8', 'MISC9', 'MISC10', 'MISC11', 'MISC12',
        'INV', 'MISC13', 'INS', 'MISC14', 'MISC15', 'MISC16', 'MEGA', 'CLIP',
        'MISC17', 'MISC18', 'MISC19', 'MISC20', 'MISC21', 'MISC22', 'MISC23',
        'MISC24', 'MISC25', 'CHAINGUN', 'MISC26', 'MISC27', 'MISC28', 'SHOTGUN',
        'SUPERSHOTGUN', 'MISC29', 'MISC30', 'MISC31', 'MISC32', 'MISC33', 'MISC34',
        'MISC35', 'MISC36', 'MISC37', 'MISC38', 'MISC39', 'MISC40', 'MISC41',
        'MISC42', 'MISC43', 'MISC44', 'MISC45', 'MISC46', 'MISC47', 'MISC48',
        'MISC49', 'MISC50', 'MISC51', 'MISC52', 'MISC53', 'MISC54', 'MISC55',
        'MISC56', 'MISC57', 'MISC58', 'MISC59', 'MISC60', 'MISC61', 'MISC62',
        'MISC63', 'MISC64', 'MISC65', 'MISC66', 'MISC67', 'MISC68', 'MISC69',
        'MISC70', 'MISC71', 'MISC72', 'MISC73', 'MISC74', 'MISC75', 'MISC76',
        'MISC77', 'MISC78', 'MISC79', 'MISC80', 'MISC81', 'MISC82', 'MISC83',
        'MISC84', 'MISC85', 'MISC86'
    ]
# fmt: on


def ensure_lmp(cfg: DictConfig) -> Optional[Path]:
    if not cfg.lmp.get("path"):
        raise ValueError("cfg.lmp.path must be configured")
    lmp_path = Path(cfg.lmp.path)

    if not lmp_path.exists():
        if not cfg.lmp.get("url"):
            raise ValueError("cfg.lmp.url must be configured")

        tmpdir_base = Path(cfg.temp_dir)
        tmpdir_base.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(dir=tmpdir_base) as tmpdir_:
            tmpdir = Path(tmpdir_)

            archive_url = cfg.lmp.url
            archive_path = tmpdir / "archive.zip"
            urlretrieve(archive_url, archive_path)

            extract_dir = tmpdir / "extracted"
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            lmp_files = [
                path for path in extract_dir.rglob("*") if path.suffix.lower() == ".lmp"
            ]

            if not lmp_files:
                raise FileNotFoundError(
                    f"No *.lmp files found in ZIP archive from {archive_url}"
                )

            lmp_files.sort()
            first_lmp = lmp_files[0]

            lmp_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(first_lmp, lmp_path)

    if cfg.lmp.get("md5"):
        expected_md5 = cfg.lmp.md5
        actual_md5 = get_md5(lmp_path)
        if actual_md5 != expected_md5:
            raise ValueError(
                f"MD5 checksum mismatch for downloaded LMP file: "
                f"expected {expected_md5}, got {actual_md5}"
            )
        if cfg.verbose:
            print(f"LMP file {lmp_path} MD5 checksum verified: {actual_md5}")
    else:
        if not lmp_path.exists():
            raise FileNotFoundError(f"LMP file not found at {lmp_path}")

    return lmp_path


def ensure_wad(cfg):
    if not cfg.wad.get("path"):
        raise ValueError("cfg.wad.path must be configured")
    wad_path = Path(cfg.wad.path)
    if not wad_path.exists():
        raise FileNotFoundError(f"WAD file not found at {wad_path}")
    if cfg.wad.get("md5"):
        expected_md5 = cfg.wad.md5
        actual_md5 = get_md5(wad_path)
        if actual_md5 != expected_md5:
            raise ValueError(
                f"MD5 checksum mismatch for WAD file: "
                f"expected {expected_md5}, got {actual_md5}"
            )
        if cfg.verbose:
            print(f"WAD file {wad_path} MD5 checksum verified: {actual_md5}")
    return wad_path


def collect_frame_groups(path: Path):
    modality_files = []
    for subdir in ("rgb", "depth", "objects"):
        files = sorted((path / subdir).glob("*.png"))
        if files:
            modality_files.append(files)

    if not modality_files:
        return []

    frame_count = min(len(files) for files in modality_files)
    return [
        [files[frame_index] for files in modality_files]
        for frame_index in range(frame_count)
    ]


def normalize_tile_image(frame_image: np.ndarray) -> np.ndarray:
    if frame_image.ndim == 2:
        frame_image = frame_image[:, :, None]
    if frame_image.shape[2] == 1:
        # Assume this is depth, and also compress it in the 0-255
        return np.repeat(frame_image / 256, 3, axis=2)
    return frame_image


def write_overview_video(cfg, image_files, video_path, fps=30):
    "Expects images_files to be a list of lists of images"
    if cfg.get("verbose"):
        print(f"Writing video {video_path} at {fps} FPS from {len(image_files)} frames")

    with iio.imopen(video_path, "w", plugin="pyav") as writer:
        writer.init_video_stream("libx264", fps=fps)
        for frame_files in image_files:
            frame_images = [
                normalize_tile_image(iio.imread(frame_file))
                for frame_file in frame_files
            ]
            rows, cols = get_overview_grid(len(frame_images), frame_images[0].shape)
            blank_tile = np.zeros_like(frame_images[0])
            padded_tiles = frame_images + [blank_tile] * (
                rows * cols - len(frame_images)
            )
            stacked_rows = [
                np.hstack(padded_tiles[row_start : row_start + cols])
                for row_start in range(0, len(padded_tiles), cols)
            ]
            frame = np.vstack(stacked_rows)
            writer.write_frame(frame)

    if cfg.get("verbose"):
        print(f"Video written: {video_path}")


def run_variant(cfg, variant=None):
    wad_path = ensure_wad(cfg)
    lmp_path = ensure_lmp(cfg)
    dataset_path = Path(cfg.dataset.output_dir)
    dataset_path.mkdir(parents=True, exist_ok=True)

    if variant is not None:
        dataset_path = dataset_path / f"variant_{variant.name}"

    cmd = [
        cfg.engine.executable_path,
        "-iwad",
        str(wad_path),
        "-playdemo",
        str(lmp_path),
        "-config",
        str(cfg.engine.config_path),
        "-extraconfig",
        str(cfg.engine.extraconfig_path),
        "-rdm-outdir",
        str(dataset_path),
        "-rdm-hideplayer",
        "-rdm-syncframes",
        "-rdm-rgb",
        "-rdm-depth",
        "-rdm-objects",
    ]

    if cfg.engine.get("fixed_palette"):
        cmd.append("-rdm-fixed-palette")

    if variant is not None:
        if variant.get("camera"):
            camera_params = list(map(str, variant.camera))
            cmd += ["-rdm-fixedcamera"] + camera_params

    if cfg.get("verbose"):
        print("Running RDM:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"RDM failed with exit code {e.returncode}") from e


@hydra.main(config_path="config", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    if cfg.get("verbose"):
        print(OmegaConf.to_yaml(cfg, resolve=True))
    video_path = Path(cfg.dataset.output_dir) / "overview.mp4"

    if cfg.dataset.variants is None:
        if cfg.get("verbose"):
            print(f"Processing dataset: {cfg.dataset.name}")
        run_variant(cfg)
        path = Path(cfg.dataset.output_dir)
        image_files = []
        for modality in ["rgb", "depth", "objects"]:
            image_files.append(sorted(list((path / modality).glob("*.png"))))
        image_files = [list(items) for items in zip(*image_files)]
        write_overview_video(cfg, image_files, video_path, fps=30)
    else:
        for variant in cfg.dataset.variants:
            if cfg.get("verbose"):
                print(f"Processing dataset variant: {cfg.dataset.name}/{variant.name}")
            run_variant(cfg, variant=variant)

        # Collect all the images for the overview video
        image_files = []
        for variant in cfg.dataset.variants:
            path = Path(cfg.dataset.output_dir) / f"variant_{variant.name}"
            image_files.append(sorted(list((path / "rgb").glob("*.png"))))
        image_files = [list(items) for items in zip(*image_files)]
        write_overview_video(cfg, image_files, video_path, fps=30)


if __name__ == "__main__":
    main()

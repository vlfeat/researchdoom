#!/usr/bin/env python3

"""Compare two CocoDoom dataset trees.

Checks relative file inventories for rgb/depth/object PNGs and COCO JSON files,
then validates matching PNGs pixel-for-pixel and COCO annotations semantically.
"""

# ./python/.venv/bin/python scripts/cocodoom-compare.py --limit 100

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from math import isclose
from typing import Any

import imageio.v3 as iio
import numpy as np


PNG_MODALITIES = ("rgb", "depth", "objects")
DEFAULT_IGNORED_JSON = {"run1.json", "run2.json", "run3.json"}


@dataclass
class CompareReport:
    kind: str
    checked: int = 0
    matches: int = 0
    missing_left: list[str] = field(default_factory=list)
    missing_right: list[str] = field(default_factory=list)
    mismatches: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing_left and not self.missing_right and not self.mismatches


def find_dataset_files(
    root: Path,
    include_images: bool = True,
    ignored_json: set[str] | None = None,
) -> dict[str, set[str]]:
    files: dict[str, set[str]] = {kind: set() for kind in (*PNG_MODALITIES, "json")}
    ignored_json = ignored_json or set()

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()

        if include_images and suffix == ".png":
            modality = next((part for part in path.parts if part in PNG_MODALITIES), None)
            if modality is not None:
                files[modality].add(rel)
        elif suffix == ".json" and rel not in ignored_json:
            files["json"].add(rel)

    return files


def compare_file_sets(kind: str, left_files: set[str], right_files: set[str]) -> CompareReport:
    report = CompareReport(kind=kind)
    report.missing_right = sorted(left_files - right_files)
    report.missing_left = sorted(right_files - left_files)
    common = left_files & right_files
    report.checked = len(common)
    report.matches = len(common)
    return report


def compare_png_files(
    kind: str,
    left_root: Path,
    right_root: Path,
    rel_paths: set[str],
    verbose: int = 0,
) -> CompareReport:
    report = CompareReport(kind=kind)

    for rel_path in sorted(rel_paths):
        if verbose >= 2:
            print(f"[{kind}] comparing {rel_path}")
        report.checked += 1
        left = iio.imread(left_root / rel_path)
        right = iio.imread(right_root / rel_path)

        if left.shape != right.shape:
            report.mismatches.append(
                f"{rel_path}: shape {left.shape} != {right.shape}"
            )
            continue

        if left.dtype != right.dtype:
            report.mismatches.append(
                f"{rel_path}: dtype {left.dtype} != {right.dtype}"
            )
            continue

        if np.array_equal(left, right):
            report.matches += 1
            continue

        diff = left.astype(np.int64) - right.astype(np.int64)
        report.mismatches.append(
            f"{rel_path}: {np.count_nonzero(diff)} values differ, max abs diff {np.abs(diff).max()}"
        )

    return report


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def format_json_counterexample(rel_path: str, label: str, items: Counter[str]) -> str:
    entry = next(iter(items.elements()))
    pretty = json.dumps(json.loads(entry), sort_keys=True, indent=2)
    return f"{rel_path}: {label}\n{pretty}"


def canonicalize_number(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return 0 if value == 0 else value
    if isinstance(value, float):
        if isclose(value, round(value), abs_tol=1e-9):
            rounded = int(round(value))
            return 0 if rounded == 0 else rounded
        return round(value, 9)
    return value


def canonicalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonicalize_json(val) for key, val in value.items()}
    if isinstance(value, list):
        return [canonicalize_json(item) for item in value]
    return canonicalize_number(value)


def normalize_segmentation(segmentation: Any) -> Any:
    canonical = canonicalize_json(segmentation)

    if not isinstance(canonical, list):
        return canonical

    if not canonical:
        return canonical

    if all(not isinstance(item, list) for item in canonical):
        return canonical

    polygons = [canonicalize_json(item) for item in canonical]
    return sorted(
        polygons,
        key=lambda polygon: json.dumps(polygon, separators=(",", ":")),
    )


def normalize_coco_image(image: dict[str, Any]) -> dict[str, Any]:
    return canonicalize_json({
        "file_name": image.get("file_name"),
        "width": image.get("width"),
        "height": image.get("height"),
    })


def normalize_coco_annotation(
    annotation: dict[str, Any],
    images_by_id: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    image_id = annotation.get("image_id")
    image = images_by_id.get(image_id, {}) if isinstance(image_id, int) else {}
    segmentation = normalize_segmentation(annotation.get("segmentation", []))

    return canonicalize_json({
        "image_file_name": image.get("file_name"),
        "category_id": annotation.get("category_id"),
        "bbox": annotation.get("bbox"),
        "area": annotation.get("area"),
        "iscrowd": annotation.get("iscrowd"),
        "segmentation": segmentation,
    })


def normalize_object_annotation(annotation: dict[str, Any]) -> dict[str, Any]:
    return canonicalize_json({
        "image_id": annotation.get("image_id"),
        "category_id": annotation.get("category_id"),
        "bbox": annotation.get("bbox"),
        "area": annotation.get("area"),
        "iscrowd": annotation.get("iscrowd"),
        "segmentation": normalize_segmentation(annotation.get("segmentation", [])),
    })


def is_coco_document(obj: Any) -> bool:
    return isinstance(obj, dict) and {"images", "annotations", "categories"}.issubset(obj)


def compare_json_list(rel_path: str, left_obj: Any, right_obj: Any) -> list[str]:
    if not isinstance(left_obj, list) or not isinstance(right_obj, list):
        return [f"{rel_path}: JSON differs"]

    if rel_path.endswith("/images.json"):
        left_items = Counter(
            json.dumps(normalize_coco_image(item), sort_keys=True, separators=(",", ":"))
            for item in left_obj
            if isinstance(item, dict)
        )
        right_items = Counter(
            json.dumps(normalize_coco_image(item), sort_keys=True, separators=(",", ":"))
            for item in right_obj
            if isinstance(item, dict)
        )
    elif rel_path.endswith("/objects.json"):
        left_items = Counter(
            json.dumps(normalize_object_annotation(item), sort_keys=True, separators=(",", ":"))
            for item in left_obj
            if isinstance(item, dict)
        )
        right_items = Counter(
            json.dumps(normalize_object_annotation(item), sort_keys=True, separators=(",", ":"))
            for item in right_obj
            if isinstance(item, dict)
        )
    else:
        left_items = Counter(
            json.dumps(canonicalize_json(item), sort_keys=True, separators=(",", ":"))
            for item in left_obj
        )
        right_items = Counter(
            json.dumps(canonicalize_json(item), sort_keys=True, separators=(",", ":"))
            for item in right_obj
        )

    if left_items == right_items:
        return []

    only_left = left_items - right_items
    only_right = right_items - left_items
    issues = [
        f"{rel_path}: JSON list differs ({sum(left_items.values())} vs {sum(right_items.values())}; "
        f"left-only {sum(only_left.values())}, right-only {sum(only_right.values())})"
    ]
    if only_left:
        issues.append(format_json_counterexample(rel_path, "left-only entry", only_left))
    if only_right:
        issues.append(format_json_counterexample(rel_path, "right-only entry", only_right))
    return issues


def compare_json_dict(rel_path: str, left_obj: Any, right_obj: Any) -> list[str]:
    if rel_path.endswith("/info.json"):
        keys = ("year", "version", "description", "contributor", "url")
        left_view = {key: left_obj.get(key) for key in keys}
        right_view = {key: right_obj.get(key) for key in keys}
        return [] if canonicalize_json(left_view) == canonicalize_json(right_view) else [f"{rel_path}: info metadata differs"]

    left_view = canonicalize_json(left_obj)
    right_view = canonicalize_json(right_obj)
    return [] if left_view == right_view else [f"{rel_path}: JSON differs"]


def compare_coco_json(rel_path: str, left_obj: Any, right_obj: Any) -> list[str]:
    issues: list[str] = []

    left_images = {
        image["id"]: image
        for image in left_obj.get("images", [])
        if isinstance(image, dict) and "id" in image
    }
    right_images = {
        image["id"]: image
        for image in right_obj.get("images", [])
        if isinstance(image, dict) and "id" in image
    }

    left_image_view = {
        image["file_name"]: normalize_coco_image(image)
        for image in left_images.values()
        if "file_name" in image
    }
    right_image_view = {
        image["file_name"]: normalize_coco_image(image)
        for image in right_images.values()
        if "file_name" in image
    }

    if left_image_view != right_image_view:
        only_left = sorted(set(left_image_view) - set(right_image_view))
        only_right = sorted(set(right_image_view) - set(left_image_view))
        if only_left:
            issues.append(f"{rel_path}: images only in left: {', '.join(only_left[:5])}")
        if only_right:
            issues.append(f"{rel_path}: images only in right: {', '.join(only_right[:5])}")
        shared = sorted(set(left_image_view) & set(right_image_view))
        for file_name in shared:
            if left_image_view[file_name] != right_image_view[file_name]:
                issues.append(f"{rel_path}: image metadata differs for {file_name}")
                break

    left_categories = {
        cat.get("id"): cat.get("name")
        for cat in left_obj.get("categories", [])
        if isinstance(cat, dict)
    }
    right_categories = {
        cat.get("id"): cat.get("name")
        for cat in right_obj.get("categories", [])
        if isinstance(cat, dict)
    }
    if left_categories != right_categories:
        issues.append(f"{rel_path}: category sets differ")

    left_annotations = Counter(
        json.dumps(
            normalize_coco_annotation(annotation, left_images),
            sort_keys=True,
            separators=(",", ":"),
        )
        for annotation in left_obj.get("annotations", [])
        if isinstance(annotation, dict)
    )
    right_annotations = Counter(
        json.dumps(
            normalize_coco_annotation(annotation, right_images),
            sort_keys=True,
            separators=(",", ":"),
        )
        for annotation in right_obj.get("annotations", [])
        if isinstance(annotation, dict)
    )

    if left_annotations != right_annotations:
        only_left = left_annotations - right_annotations
        only_right = right_annotations - left_annotations
        issues.append(
            f"{rel_path}: annotation multiset differs "
            f"({sum(left_annotations.values())} vs {sum(right_annotations.values())}; "
            f"left-only {sum(only_left.values())}, right-only {sum(only_right.values())})"
        )
        if only_left:
            issues.append(format_json_counterexample(rel_path, "left-only entry", only_left))
        if only_right:
            issues.append(format_json_counterexample(rel_path, "right-only entry", only_right))

    return issues


def compare_json_files(left_root: Path, right_root: Path, rel_paths: set[str], verbose: int = 0) -> CompareReport:
    report = CompareReport(kind="json")

    for rel_path in sorted(rel_paths):
        if verbose >= 1:
            print(f"[json] comparing {rel_path}")
        report.checked += 1
        left_obj = load_json(left_root / rel_path)
        right_obj = load_json(right_root / rel_path)

        if canonicalize_json(left_obj) == canonicalize_json(right_obj):
            report.matches += 1
            continue

        if is_coco_document(left_obj) and is_coco_document(right_obj):
            issues = compare_coco_json(rel_path, left_obj, right_obj)
            if not issues:
                report.matches += 1
            else:
                report.mismatches.extend(issues)
            continue

        if isinstance(left_obj, list) and isinstance(right_obj, list):
            issues = compare_json_list(rel_path, left_obj, right_obj)
            if not issues:
                report.matches += 1
            else:
                report.mismatches.extend(issues)
            continue

        if isinstance(left_obj, dict) and isinstance(right_obj, dict):
            issues = compare_json_dict(rel_path, left_obj, right_obj)
            if not issues:
                report.matches += 1
            else:
                report.mismatches.extend(issues)
            continue

        report.mismatches.append(f"{rel_path}: JSON differs")

    return report


def print_report(report: CompareReport, limit: int) -> None:
    print(f"[{report.kind}] checked={report.checked} matched={report.matches}")

    if report.missing_left:
        print(f"  only in right ({len(report.missing_left)}):")
        for rel_path in report.missing_left[:limit]:
            print(f"    {rel_path}")
        if len(report.missing_left) > limit:
            remaining = len(report.missing_left) - limit
            print(f"    ... {remaining} more not shown (increase --limit to see all)")
    if report.missing_right:
        print(f"  only in left ({len(report.missing_right)}):")
        for rel_path in report.missing_right[:limit]:
            print(f"    {rel_path}")
        if len(report.missing_right) > limit:
            remaining = len(report.missing_right) - limit
            print(f"    ... {remaining} more not shown (increase --limit to see all)")
    if report.mismatches:
        print(f"  mismatches ({len(report.mismatches)}):")
        for issue in report.mismatches[:limit]:
            for line in issue.splitlines():
                print(f"    {line}")
        if len(report.mismatches) > limit:
            remaining = len(report.mismatches) - limit
            print(f"    ... {remaining} more not shown (increase --limit to see all)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two CocoDoom datasets")
    parser.add_argument("left", nargs="?", default="/tmp/cocodoom")
    parser.add_argument("right", nargs="?", default="/tmp/cocodoom-legacy")
    parser.add_argument(
        "--limit",
        type=int,
        default=10_000,
        help="Maximum number of missing/mismatch entries to print per section",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip PNG inventory and pixel comparisons; compare JSON files only",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Increase progress reporting: -v prints comparison categories and all JSON files; "
            "-vv also prints each PNG file comparison"
        ),
    )
    parser.add_argument(
        "--include-run-json",
        action="store_true",
        help="Include top-level run1.json/run2.json/run3.json in JSON inventory and content comparisons",
    )
    args = parser.parse_args()

    left_root = Path(args.left)
    right_root = Path(args.right)

    if not left_root.is_dir():
        raise SystemExit(f"left dataset not found: {left_root}")
    if not right_root.is_dir():
        raise SystemExit(f"right dataset not found: {right_root}")

    ignored_json = set() if args.include_run_json else DEFAULT_IGNORED_JSON

    if args.verbose >= 1:
        scan_scope = "JSON files only" if args.skip_images else "all dataset files"
        print(f"[scan] indexing {scan_scope} under {left_root}")
        if ignored_json:
            print(f"[scan] ignoring JSON files: {', '.join(sorted(ignored_json))}")
    left_files = find_dataset_files(
        left_root,
        include_images=not args.skip_images,
        ignored_json=ignored_json,
    )

    if args.verbose >= 1:
        scan_scope = "JSON files only" if args.skip_images else "all dataset files"
        print(f"[scan] indexing {scan_scope} under {right_root}")
    right_files = find_dataset_files(
        right_root,
        include_images=not args.skip_images,
        ignored_json=ignored_json,
    )

    inventory_kinds = ("json",) if args.skip_images else (*PNG_MODALITIES, "json")
    content_kinds = () if args.skip_images else PNG_MODALITIES

    inventory_reports = [
        compare_file_sets(kind, left_files[kind], right_files[kind])
        for kind in inventory_kinds
    ]

    if args.verbose >= 1:
        for kind in inventory_kinds:
            print(f"[inventory] comparing {kind} file sets")
        for kind in content_kinds:
            print(f"[{kind}] comparing shared {kind} files")

    content_reports = [
        compare_png_files(
            kind,
            left_root,
            right_root,
            left_files[kind] & right_files[kind],
            verbose=args.verbose,
        )
        for kind in content_kinds
    ]
    content_reports.append(
        compare_json_files(
            left_root,
            right_root,
            left_files["json"] & right_files["json"],
            verbose=args.verbose,
        )
    )

    print(f"Comparing {left_root} <-> {right_root}")
    print()
    print("Inventory")
    for report in inventory_reports:
        print_report(report, args.limit)

    print()
    print("Content")
    for report in content_reports:
        print_report(report, args.limit)

    ok = all(report.ok for report in inventory_reports + content_reports)
    print()
    print("Result: MATCH" if ok else "Result: DIFFERENCES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
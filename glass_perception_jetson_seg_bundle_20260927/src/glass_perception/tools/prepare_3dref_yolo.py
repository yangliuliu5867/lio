#!/usr/bin/env python3
"""Convert 3DRef alllabel masks into auditable one-class YOLO detection data."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import cv2


def hash_fraction(name: str) -> float:
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big") / 2**64


def find_split(root: Path, split: str) -> tuple[Path, Path]:
    candidates = list(root.rglob(f"alllabel/{split}/image"))
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one alllabel/{split}/image, found {candidates}")
    images = candidates[0]
    masks = images.parent / "mask"
    if not masks.is_dir():
        raise RuntimeError(f"missing mask directory: {masks}")
    return images, masks


def labels_from_mask(mask: Path, width: int, height: int, min_area: int) -> list[str]:
    image = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE)
    if image is None or image.shape != (height, width):
        raise RuntimeError(f"invalid/mismatched mask: {mask}")
    binary = (image > 0).astype("uint8")
    count, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    labels = []
    for x, y, w, h, area in stats[1:count]:
        if area < min_area or w < 2 or h < 2:
            continue
        labels.append("0 %.8f %.8f %.8f %.8f" % ((x + w / 2) / width, (y + h / 2) / height,
                                                    w / width, h / height))
    return labels


def convert(source_images: Path, source_masks: Path, target: Path, val_fraction: float,
            min_area: int, fixed_split: str | None = None) -> dict:
    written = {"images": 0, "labels": 0, "empty": 0, "boxes": 0}
    for image in sorted(source_images.iterdir()):
        if image.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        mask = source_masks / image.name
        if not mask.is_file():
            raise RuntimeError(f"missing paired mask: {mask}")
        frame = cv2.imread(str(image), cv2.IMREAD_COLOR)
        if frame is None:
            raise RuntimeError(f"invalid image: {image}")
        height, width = frame.shape[:2]
        labels = labels_from_mask(mask, width, height, min_area)
        split = fixed_split or ("val" if hash_fraction(image.name) < val_fraction else "train")
        image_dir, label_dir = target / "images" / split, target / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        destination = image_dir / image.name
        shutil.copy2(image, destination)
        (label_dir / f"{image.stem}.txt").write_text("\n".join(labels) + ("\n" if labels else ""))
        written["images"] += 1
        written["boxes"] += len(labels)
        written["labels"] += bool(labels)
        written["empty"] += not bool(labels)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="extracted 3DRef root")
    parser.add_argument("--output", type=Path, required=True, help="new/empty YOLO dataset directory")
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--min-area-pixels", type=int, default=64)
    args = parser.parse_args()
    if not 0.05 <= args.val_fraction < 0.5 or args.min_area_pixels < 1:
        parser.error("val fraction must be [0.05,0.5), min area positive")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("output must not already contain files")
    train_images, train_masks = find_split(args.source, "train")
    test_images, test_masks = find_split(args.source, "test")
    output = args.output.resolve()
    train = convert(train_images, train_masks, output, args.val_fraction, args.min_area_pixels)
    test = convert(test_images, test_masks, output, args.val_fraction, args.min_area_pixels, "test")
    yaml_path = output / "3dref_suspect_surface.yaml"
    yaml_path.write_text("path: %s\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n  0: suspect_surface\n" % output)
    manifest = {"source": str(args.source.resolve()), "authors_split": "test preserved; train hash-split into train/val",
                "val_fraction": args.val_fraction, "min_area_pixels": args.min_area_pixels,
                "class": "suspect_surface", "train_and_val": train, "test": test}
    (output / "conversion_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

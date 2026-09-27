#!/usr/bin/env python3
"""Explicit training command, not run by ROS launch. No dataset is bundled."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True, help='YOLO dataset YAML')
    parser.add_argument('--model', required=True, help='Local initial detect/segment .pt weights')
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--batch', type=int, default=8)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--project', default='runs/surfaces')
    args = parser.parse_args()
    if min(args.epochs, args.imgsz, args.batch) <= 0:
        parser.error('epochs/imgsz/batch must be positive')
    for path in (args.data, args.model):
        if not Path(path).is_file():
            parser.error('File does not exist: '+path)
    import yaml
    with open(args.data) as stream:
        dataset = yaml.safe_load(stream)
    names = dataset.get('names', {})
    if names not in ({0: 'suspect_surface'}, ['suspect_surface']):
        parser.error('Dataset names must be 0: suspect_surface')
    from ultralytics import YOLO
    model = YOLO(args.model)
    if model.task not in ('detect', 'segment'):
        parser.error('Use detect or segment initialization weights')
    model.train(data=str(Path(args.data).resolve()), epochs=args.epochs,
                imgsz=args.imgsz, batch=args.batch, device=args.device,
                seed=args.seed, deterministic=True, project=args.project, name='suspect_surface', exist_ok=False)


if __name__ == '__main__':
    main()

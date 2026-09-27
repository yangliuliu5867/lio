"""Static checks runnable without ROS or ML dependencies."""
import ast
from pathlib import Path
import xml.etree.ElementTree as ET
root = Path(__file__).resolve().parents[1]
files = list(root.rglob('*.py'))
for path in files:
    ast.parse(path.read_text(), filename=str(path), feature_version=(3, 8))
for path in [root / 'package.xml', root / 'launch/monocular.launch']:
    ET.parse(path)
print('PASS: Python 3.8 syntax (%d files), package and launch XML' % len(files))

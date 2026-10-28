"""Atajo: equivale a  python3 scripts/build_obra.py cid  (genera web/data/cid.js).
Las demás obras (Santa Oria...) se construyen con build_obra.py."""
import os, subprocess, sys
sys.exit(subprocess.call([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_obra.py"), "cid"]))

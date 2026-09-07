import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from generate_building import build, ROOT
build(json.loads((ROOT/"tools/world/market_building.json").read_text()))

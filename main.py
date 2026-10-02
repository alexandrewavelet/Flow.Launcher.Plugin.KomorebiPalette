# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

plugindir = Path.absolute(Path(__file__).parent)
paths = (".", "lib", "plugin")
sys.path = [str(plugindir / p) for p in paths] + sys.path

from plugin import executor  # noqa: E402
from plugin.palette import KomorebiPalette  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == executor.RUN_FLAG:
        executor.execute(json.loads(sys.argv[2]))
    else:
        KomorebiPalette()

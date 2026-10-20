"""Builds every book in books.json into <build dir>/<id>.tsv, plus its audio manifest.

Usage: build_all.py <build dir> <lexicon.tsv.gz>
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    build, lexicon = sys.argv[1:3]
    os.makedirs(build, exist_ok=True)
    for c in json.load(open(os.path.join(ROOT, "books.json"), encoding="utf-8")):
        out = os.path.join(build, f"{c['id']}.tsv")
        lower = [os.path.join(ROOT, p) for p in c["lower"]]
        here = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, os.path.join(here, "build.py"), c["level"], os.path.join(ROOT, c["sources"]), lexicon, out, *lower], check=True)
        subprocess.run([sys.executable, os.path.join(here, "audio_manifest.py"), out, os.path.join(build, f"{c['id']}.manifest")], check=True)


if __name__ == "__main__":
    main()

"""Publishes the built word books: versioned files under <id>/ and the catalog index.json.

Usage: publish.py <build dir> [--audio]

Reads books.json (what to publish) and, per book, <build dir>/<id>.tsv and, with --audio, the
recordings in <build dir>/audio/<id>/ listed by <build dir>/<id>.manifest. A book whose word list
changed gets the next version number; its files are written as <id>/<id>-<version>.tsv and
<id>/<id>-<version>-audio-<n>.zip. Recordings are published only when every text of the book has
one; a book first published without them gets a new version once they are all there. Unchanged
books keep their version and files, so the app only offers an update when there is something new. The
previous version's files are kept one round longer, for CDN mirrors still serving the old index.
"""
import hashlib
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(path: str) -> dict:
    return {"path": os.path.relpath(path, ROOT).replace(os.sep, "/"), "bytes": os.path.getsize(path), "sha256": sha256(path)}


def count_words(tsv: str) -> int:
    lines = [l for l in open(tsv, encoding="utf-8") if l.strip() and not l.startswith("#")]
    return len(lines) - 1


# jsDelivr serves files from GitHub only up to 20 MB, so recordings go into parts below that.
PART_BYTES = 15_000_000


def write_zips(source_dir: str, prefix: str) -> list:
    """Writes <prefix>-1.zip, <prefix>-2.zip, …; returns their paths.

    Stored, sorted and with fixed timestamps: the recordings are already compressed, and the
    same recordings always give the same files.
    """
    parts, current, size = [], [], 0
    for name in sorted(os.listdir(source_dir)):
        length = os.path.getsize(os.path.join(source_dir, name))
        if current and size + length > PART_BYTES:
            parts.append(current)
            current, size = [], 0
        current.append(name)
        size += length
    if current:
        parts.append(current)
    paths = []
    for i, names in enumerate(parts, 1):
        path = f"{prefix}-{i}.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
            for name in names:
                info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                with open(os.path.join(source_dir, name), "rb") as f:
                    z.writestr(info, f.read())
        paths.append(path)
    return paths


def audio_complete(build: str, book_id: str) -> bool:
    audio_dir = os.path.join(build, "audio", book_id)
    have = set(os.listdir(audio_dir)) if os.path.isdir(audio_dir) else set()
    keys = [line.split("\t", 1)[0] for line in open(os.path.join(build, f"{book_id}.manifest"), encoding="utf-8") if line.strip()]
    missing = [k for k in keys if f"{k}.webm" not in have]
    if missing:
        print(f"{book_id}: {len(missing)} of {len(keys)} recordings still missing")
    return not missing


def main() -> None:
    build = sys.argv[1]
    with_audio = "--audio" in sys.argv[2:]
    config = json.load(open(os.path.join(ROOT, "books.json"), encoding="utf-8"))
    index_path = os.path.join(ROOT, "index.json")
    old = {}
    if os.path.exists(index_path):
        old = {b["id"]: b for b in json.load(open(index_path, encoding="utf-8")).get("books", [])}

    books = []
    for c in config:
        book_id = c["id"]
        built = os.path.join(build, f"{book_id}.tsv")
        digest = sha256(built)
        previous = old.get(book_id)
        folder = os.path.join(ROOT, book_id)
        os.makedirs(folder, exist_ok=True)
        add_audio = with_audio and audio_complete(build, book_id)
        if previous and previous["book"]["sha256"] == digest and (previous.get("audio") or not add_audio):
            entry = dict(previous)
            print(f"{book_id}: unchanged, version {entry['version']}")
        else:
            version = previous["version"] + 1 if previous else 1
            tsv = os.path.join(folder, f"{book_id}-{version}.tsv")
            with open(built, "rb") as src, open(tsv, "wb") as dst:
                dst.write(src.read())
            entry = {"id": book_id, "version": version, "book": describe(tsv)}
            audio_dir = os.path.join(build, "audio", book_id)
            if add_audio:
                zips = write_zips(audio_dir, os.path.join(folder, f"{book_id}-{version}-audio"))
                entry["audio"] = [describe(z) for z in zips]
            print(f"{book_id}: new version {version}")
        entry.update({k: c[k] for k in ("title", "description", "level")})
        entry["words"] = count_words(os.path.join(ROOT, entry["book"]["path"]))
        books.append(entry)

        # Keep the files of this version and the one before; drop anything older.
        keep = {entry["version"], entry["version"] - 1}
        for name in os.listdir(folder):
            m = re.fullmatch(re.escape(book_id) + r"-(\d+)(\.tsv|-audio-\d+\.zip)", name)
            if not m or int(m.group(1)) not in keep:
                os.remove(os.path.join(folder, name))

    ordered = [{k: b[k] for k in ("id", "title", "description", "level", "version", "words", "book", "audio") if k in b} for b in books]
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"format": 1, "books": ordered}, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()

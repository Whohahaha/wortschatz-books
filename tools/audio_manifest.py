"""Lists every text the app may read aloud for a word book, as input for gen_audio.py.

Usage: audio_manifest.py <book .tsv> <output manifest>

Writes "key<TAB>text" lines. This must match Audio.texts and Audio.key in the app
(core/src/main/kotlin/app/wortschatz/core/Audio.kt): the key is the first 16 hex digits of the
SHA-1 of the exact UTF-8 text, and the texts are the word (nouns with their article), "die" +
plural, the verb forms "fährt, fuhr, ist gefahren", and the example sentence.
"""
import hashlib
import sys


def key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def texts(row: dict) -> list:
    lemma = row["lemma"].replace("|", "")
    out = [f"{row['gender']} {lemma}" if row["gender"] else lemma]
    if row["plural"]:
        out.append(f"die {row['plural']}")
    if row["participle"]:
        aux = "ist" if row["aux"] == "sein" else "hat"
        out.append(f"{row['present3']}, {row['preterite']}, {aux} {row['participle']}")
    if row["example"]:
        out.append(row["example"])
    return out


def main() -> None:
    book, out_path = sys.argv[1:3]
    header, seen = None, {}
    for line in open(book, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        cells = [c.strip() for c in line.rstrip("\n").split("\t")]
        if header is None:
            header = cells
            continue
        row = dict(zip(header, cells + [""] * (len(header) - len(cells))))
        for text in texts(row):
            seen.setdefault(text, key(text))
    with open(out_path, "w", encoding="utf-8") as out:
        for text, k in seen.items():
            out.write(f"{k}\t{text}\n")
    print(f"{len(seen)} texts for {book}")


if __name__ == "__main__":
    main()

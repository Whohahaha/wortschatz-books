"""Builds a downloadable Goethe word book (A2, B1, …) from hand-written sources.

Usage: build.py <level> <source dir> <lexicon.tsv[.gz]> <output .tsv> [lower level .tsv …]

The headwords follow the public Goethe-Zertifikat word list of that level; the Chinese meanings
and all example sentences are written for this project. Each book holds only the words that are
new at its level: a word already in one of the lower level books given (same part of speech and
lemma) is left out, so learners going A1 → A2 → B1 never meet a word twice, and progress on it
carries over. Plurals and verb forms not given in the sources come from the Wiktionary lexicon
(tools/lexicon/build_lexicon.py).

Entry ids are the slug of the lemma, as in the A1 book, and never change between versions of a
book: the study progress on the phone is keyed by them. An id already taken by a different word
in a lower book gets the level as suffix ("schloss-b1").

Source columns: pos, headword, meaning, example, example_zh, [plural or auxiliary]
  - nouns are written with their article ("der Tisch"); plural "-" means none
  - for verbs the last column overrides the perfect auxiliary (haben / sein)
  - separable verbs mark the prefix with "|" ("an|rufen")
"""
import glob
import gzip
import os
import sys

UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
ARTICLES = {"der", "die", "das"}
POS = {"n", "v", "adj", "adv", "other"}
COLUMNS = ["id", "level", "pos", "lemma", "gender", "plural", "meaning",
           "present3", "preterite", "participle", "aux", "example", "example_zh"]
TITLES = {"A2": "歌德 A2 词书", "B1": "歌德 B1 词书"}


def slug(text: str) -> str:
    s = text.lower().translate(UMLAUTS)
    s = "".join(c if c.isalnum() else "-" for c in s).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s


def open_text(path: str):
    return gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") else open(path, encoding="utf-8")


def load_lexicon(path: str):
    nouns, verbs = {}, {}
    with open_text(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            c = (line.rstrip("\n").split("\t") + [""] * 8)[:8]
            if c[1] == "n":
                nouns.setdefault((c[0], c[2]), c[3])
            elif c[1] == "v":
                verbs.setdefault(c[0], c[4:8])
    return nouns, verbs


def load_book(path: str):
    """(ids, words) of an existing word book; words are (pos, lemma without '|')."""
    ids, words = set(), set()
    with open(path, encoding="utf-8") as f:
        header = None
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            cells = line.rstrip("\n").split("\t")
            if header is None:
                header = {name: i for i, name in enumerate(cells)}
                continue
            ids.add(cells[header["id"]])
            words.add((cells[header["pos"]], cells[header["lemma"]].replace("|", "").lower()))
    return ids, words


def main() -> None:
    level, source_dir, lexicon_path, out_path = sys.argv[1:5]
    lower_ids, lower_words = set(), set()
    for path in sys.argv[5:]:
        ids, words = load_book(path)
        lower_ids |= ids
        lower_words |= words

    nouns, verbs = load_lexicon(lexicon_path)
    rows, ids, seen, notes, skipped = [], set(), set(), [], 0

    for path in sorted(glob.glob(os.path.join(source_dir, "source_*.tsv"))):
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            if not line.strip() or line.startswith("#"):
                continue
            cells = [c.strip() for c in line.rstrip("\n").split("\t")]
            where = f"{os.path.basename(path)}:{n}"
            assert len(cells) in (5, 6), f"{where}: {len(cells)} columns"
            pos, head, meaning, example, example_zh = cells[:5]
            extra = cells[5] if len(cells) == 6 else None
            assert pos in POS, f"{where}: unknown pos {pos}"
            assert meaning and example, f"{where}: empty meaning or example"

            gender = plural = ""
            forms = ["", "", "", ""]
            lemma = head
            if pos == "n":
                article, lemma = head.split(" ", 1)
                assert article in ARTICLES, f"{where}: noun without article: {head}"
                gender = article
                if extra is not None:
                    plural = "" if extra == "-" else extra
                else:
                    plural = nouns.get((lemma, gender), "")
            elif pos == "v" and " " not in head:
                found = verbs.get(head.replace("|", ""))
                if found and found[2]:
                    forms = list(found)
                    if extra in ("haben", "sein"):
                        forms[3] = extra
                else:
                    notes.append(f"no verb forms found: {head}")

            word = (pos, lemma.replace("|", "").lower())
            # Words of lower levels, and the same word written twice in the sources.
            if word in lower_words or word in seen:
                skipped += 1
                continue
            seen.add(word)

            base = slug(lemma.replace("|", ""))
            entry_id = base
            for candidate in (base, f"{base}-{pos}", f"{base}-{level.lower()}", f"{base}-{pos}-{level.lower()}"):
                if candidate not in ids and candidate not in lower_ids:
                    entry_id = candidate
                    break
            else:
                raise AssertionError(f"{where}: no free id for {head}")
            ids.add(entry_id)
            rows.append([entry_id, level, pos, lemma, gender, plural, meaning, *forms, example, example_zh])

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(f"# title: {TITLES.get(level, '歌德 ' + level + ' 词书')}\n")
        out.write(f"# 词头依据歌德学院 Goethe-Zertifikat {level} 公开词表，只收比低一级词书新增的词；中文释义和例句为本项目自编。\n")
        out.write("# 复数和动词变位来自 Wiktionary（经 kaikki.org 整理），CC BY-SA 4.0。\n")
        out.write("\t".join(COLUMNS) + "\n")
        for r in rows:
            out.write("\t".join(c.replace("\t", " ") for c in r) + "\n")
    print(f"{len(rows)} entries written to {out_path} ({skipped} already in lower levels or repeated)")
    for note in notes:
        print("  " + note)


if __name__ == "__main__":
    main()

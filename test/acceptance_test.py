#!/usr/bin/env python3
"""CryptogramPress acceptance test.

Proof-output method: build a real book (2 puzzles per difficulty band),
then re-verify every puzzle with a checker written independently of
the engine: a second pattern-matching solver (longest-word-first,
its own pattern function) re-decodes the printed cipher against the
dictionary DATA and must find exactly one decode, equal to the printed
quotation. Also audits the substitution (true bijection, no letter
maps to itself), the printed key (decode with the key reproduces the
quotation exactly), and a tamper case (swap two cipher letters: the
key decode no longer matches, so the gate must reject it). Plus PDF
geometry, timing, determinism.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cryptogram_press import run_cryptogrampress, DICTIONARY  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "out")
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def pat(word):
    m = {}
    out = []
    for ch in word:
        if ch not in m:
            m[ch] = len(m)
        out.append(m[ch])
    return tuple(out)


_INDEX = {}
for _w in DICTIONARY:
    _INDEX.setdefault((len(_w), pat(_w)), []).append(_w)


def count_decodes_independent(cipher_words, limit=2):
    """Longest-word-first backtracking with forward consistency on the
    partial letter map -- a different search order and code path from
    the engine's fewest-candidates solver."""
    words = sorted(set(cipher_words), key=lambda w: -len(w))
    cand_lists = []
    for cw in words:
        lst = _INDEX.get((len(cw), pat(cw)), [])
        if not lst:
            return 0
        cand_lists.append(lst)
    found = [0]
    c2p, p2c = {}, {}

    def rec(k):
        if found[0] >= limit:
            return
        if k == len(words):
            found[0] += 1
            return
        cw = words[k]
        for w in cand_lists[k]:
            added = {}
            ok = True
            for cc, pp in zip(cw, w):
                if cc in c2p and c2p[cc] != pp:
                    ok = False
                    break
                if pp in p2c and p2c[pp] != cc:
                    ok = False
                    break
                if cc not in c2p:
                    added[cc] = pp
            if not ok:
                continue
            for cc, pp in added.items():
                c2p[cc] = pp
                p2c[pp] = cc
            rec(k + 1)
            for cc in added:
                del p2c[c2p[cc]]
                del c2p[cc]
            if found[0] >= limit:
                return

    rec(0)
    return found[0]


def cipher_words_of(text):
    out = []
    for w in text.replace(";", " ").replace(",", " ").replace(".", " ").split():
        w = "".join(ch for ch in w.lower() if ch.isalpha())
        if w:
            out.append(w)
    return out


def main():
    t0 = time.time()
    s = run_cryptogrampress(6, OUT, seed=42, difficulty="Mixed")
    dt = time.time() - t0
    ps = s["puzzles"]
    check("counts: 6 puzzles, Easy/Medium/Hard rotating",
          len(ps) == 6 and [p["difficulty"] for p in ps] ==
          ["Easy", "Medium", "Hard", "Easy", "Medium", "Hard"],
          f"({[p['difficulty'] for p in ps]})")

    bij_ok, unique_ok, key_ok = True, True, True
    for p in ps:
        if sorted(p["p2c"].values()) != list("abcdefghijklmnopqrstuvwxyz"):
            bij_ok = False
        if any(p["p2c"][ch] == ch for ch in p["p2c"]):
            bij_ok = False
        decoded = "".join(
            p["c2p"][ch.lower()].upper() if ch.isupper()
            else p["c2p"][ch.lower()] if ch.isalpha() else ch
            for ch in p["cipher"])
        if decoded != p["text"]:
            key_ok = False
        cnt = count_decodes_independent(cipher_words_of(p["cipher"]), limit=2)
        if cnt != 1:
            unique_ok = False
    check("every substitution is a bijection with no fixed letters", bij_ok, "")
    check("printed key decodes every cipher back to its quotation exactly",
          key_ok, "")
    check("every cipher: exactly one decode (independent longest-first "
          "pattern solver)", unique_ok,
          f"(letters per puzzle: {[p['letters'] for p in ps]})")

    # tamper: swap two cipher letters throughout the cipher text; the
    # printed key must then fail to reproduce the quotation
    p0 = ps[0]
    used = sorted({ch.lower() for ch in p0["cipher"] if ch.isalpha()})
    a, b = used[0], used[1]
    swapped = p0["cipher"].translate(str.maketrans({a: b, b: a,
                                                     a.upper(): b.upper(),
                                                     b.upper(): a.upper()}))
    decoded_bad = "".join(
        p0["c2p"][ch.lower()].upper() if ch.isupper()
        else p0["c2p"][ch.lower()] if ch.isalpha() else ch
        for ch in swapped)
    check("tamper: swapping two cipher letters breaks the key decode",
          decoded_bad != p0["text"], "")

    with open(s["pdf_path"], "rb") as fh:
        data = fh.read()
    pages = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    check("PDF 612x792pt, 14 pages", b"612 792" in data and pages == 14,
          f"({pages})")
    check("6-puzzle mixed book builds in under 180s", dt < 180, f"({dt:.1f}s)")

    s2 = run_cryptogrampress(6, OUT, seed=42, difficulty="Mixed")
    same = [p["cipher"] for p in s2["puzzles"]] == [p["cipher"] for p in ps]
    check("deterministic for fixed seed", same, "")

    npass = sum(1 for _, ok, _ in results if ok)
    print(f"\n{npass}/{len(results)} PASS")
    with open(os.path.join(os.path.dirname(__file__),
                           "acceptance_results.txt"), "w") as fh:
        for name, ok, detail in results:
            fh.write(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}\n")
        fh.write(f"\n{npass}/{len(results)} PASS\n")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

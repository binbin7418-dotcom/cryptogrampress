# CryptogramPress

Build print-ready **cryptogram puzzle books for Amazon KDP** where every cipher is *proven* to have exactly one decode.

## Why

A cryptogram is a promise: the printed letters decode to exactly one English text. Break it — a short quote, a sloppy key — and two different "solutions" fit, and your readers will find the second one. CryptogramPress checks the promise before it prints:

1. A public-domain quotation (68 in the bank: Twain, Austen, Dickens, Shakespeare, Lincoln, Franklin, Seneca and more) is encrypted with a fresh random substitution — a true bijection, and no letter ever stands for itself.
2. A **pattern-matching solver** (word-pattern backtracking against the built-in 1,700+ word dictionary, written separately from the encryptor) decodes the cipher from the printed letters alone. The puzzle ships only when the solver finds **exactly one** decode — the quotation itself.
3. Quotations whose word patterns admit a second decode never enter a book. Difficulty is by quotation length: Easy 38–65 letters, Medium 66–95, Hard 96–150. The proven pools hold 17 Easy, 12 Medium and 6 Hard quotations; a book larger than a pool re-uses quotations under fresh ciphers (each still individually proven), so series production never silently breaks the guarantee.

## Use

**App (Windows):** launch `CryptogramPress.exe`, choose the cryptogram count, difficulty (Easy / Medium / Hard, or Mixed rotating all three) and a seed, click **Build the book**. Output: `cryptogram_book.pdf` in a `cryptogrampress_out` folder — title page, one puzzle per page (cipher letters over write-in lines, author hint, a key-recording strip), then full solutions with the complete key for every puzzle. 8.5×11in (612×792pt).

**Command line:** `python cryptogram_press.py out/ --puzzles=20 --difficulty=Mixed --seed=42`

A 6-puzzle sample book is included (`sample_book.pdf`).

## Verified

Acceptance test (8/8 PASS, `test/acceptance_results.txt`): a 6-puzzle mixed book re-verified by an independent checker whose pattern solver searches longest-word-first (a different code path from the engine's) — every cipher has exactly one decode against the dictionary; every substitution is a bijection with no fixed letters; the printed key decodes each cipher back to its quotation exactly; swapping two cipher letters in a printed puzzle breaks the key decode (the gate has teeth); PDF exactly 14 pages at 612×792pt; whole book in about 6 seconds (including the one-time pool proof); deterministic for a fixed seed.

Honest scope of the claim: "exactly one decode" means exactly one decode **against the built-in dictionary**, which ships in the source where anyone can audit it — the same standard any pattern solver can check.

## Scope

Classic letter-substitution cryptograms of famous public-domain quotations. No accounts, no uploads: 100% local, no per-book fees. Deterministic seeds make series production repeatable.

## Build from source

`pip install pyinstaller reportlab`, then `pyinstaller cryptogrampress.spec`. Or push to GitHub and let the included Actions workflow build the Windows package.

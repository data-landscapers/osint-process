---
type: doc
title: Purge the PDFs from OSINT's git history
status: not started — written 2026-08-16, for one OSINT session
last_reviewed: 2026-08-16
---

# Purge the PDFs from OSINT's git history

*(Written from CORPUS, for OSINT. **Self-contained** — it assumes nothing read first and names no path outside OSINT. One line per paragraph, OSINT house style.)*

*(Answers `X:
otes-for-osint.md` note 1, open since 2026-08-06. Note 1 said the tracked PDFs in `raw/` are the weight and that removing them from the tree would not recover the space, because history retains the blobs. This is the operation that does recover it.)*

## The state, measured 2026-08-16

`.git` is **5.1 GB** and the working tree **8.1 GB**, against GitHub's soft 5 GB ceiling — so the ceiling is crossed, not approached.

**760 PDFs are tracked**: 745 under `raw/`, 15 under `new-budget/`. In the `raw/` working tree there are 747 PDFs totalling **2.61 GB**, against about 74 MB for all 9,407 markdown records. The largest single file is 64 MB.

So the PDFs are essentially the whole of the repository's weight, and the markdown — the part that is actually edited, diffed and reviewed — is a rounding error beside them.

## What this asks you to decide

**PDFs stop being version-controlled and become backed-up binary artefacts.**

That is the whole of the decision, and it is worth stating plainly because it changes what git guarantees about them. A PDF is never edited after capture: it has no diff, no merge, no history worth reading. Version control buys nothing for it and costs 2.61 GB. What a PDF does need is a backup, and one is held outside this repository. That backup is Bill's and is run by him; it is not something OSINT operates, knows the location of, or has to arrange.

**A new repository is not needed and is the worse option.** It would discard the markdown history, which is the part with value. `git filter-repo` rewrites the existing history in place and keeps everything else.

**Nothing outside OSINT breaks.** This was checked before the document was written: no CORPUS script reads OSINT's committed `HEAD`, every CORPUS read goes through the working tree, and nothing CORPUS publishes cites an OSINT commit SHA. A rewrite invalidates no published citation. Slug permanence is untouched — this operation moves files and rewrites commits, and mints, retires or reissues no slug.

## Do it in this order

The order is the safety property. Untracking the PDFs before the rewrite is what keeps them on disk through it — see P2.

**P1 — Take a bundle first, and check it.**

```bash
git bundle create ../osint-pre-purge.bundle --all
git bundle verify ../osint-pre-purge.bundle
```

This is the rollback. It is a single file holding the entire history as it stands, and it is the only thing that can undo P3. Keep it until P5 has passed and you are satisfied.

**P2 — Untrack the PDFs where they stand. Nothing moves.**

**Every PDF stays exactly where it is in `raw/`** *(Bill, 2026-08-16 — he works directly in `raw/` for his own writing and needs the source documents beside their records)*. This step changes what git does about them, not where they are.

That rules out the `budget-archive/` pattern, and it should: a junction redirects a whole directory, and these PDFs are interleaved with the markdown records inside the year folders, so there is no directory to redirect that does not also take the records with it.

Add `*.pdf` to `.gitignore`, then drop them from the index while leaving them on disk:

```bash
git rm --cached -r --quiet -- '*.pdf' '*.PDF'
git commit -m "Untrack PDFs; they stay in raw/"
```

`--cached` is the whole of the safety here: it removes the files from git's index and touches nothing on disk.

**This step must come before P3, and that is the order the operation depends on.** `git filter-repo` finishes with a hard reset, which would delete the PDFs from the working tree if they were still tracked at `HEAD`. Once they are untracked and ignored, the reset cannot see them and they survive it untouched.

Confirm before continuing — 0 tracked, 747 still on disk under `raw/`:

```bash
git ls-files '*.pdf' '*.PDF' | wc -l
find raw -iname '*.pdf' | wc -l
```

**P3 — Rewrite the history.**

```bash
pip install git-filter-repo
git filter-repo --path-glob '*.pdf' --path-glob '*.PDF' --invert-paths
```

`--invert-paths` means *remove these paths* rather than keep only them. `--path-glob` matches at any depth, so it takes `raw/` and `new-budget/` together.

Two things it does that surprise people, both deliberate: it **removes the `origin` remote**, so that a force-push cannot be a reflex, and it refuses to run on a repository with uncommitted changes. Commit or stash first, and re-add the remote in P4.

It repacks as it goes, so no separate `git gc` is needed.

**P4 — Push the rewritten history.**

```bash
git remote add origin <the OSINT remote URL>
git push --force --all
git push --force --tags
```

**Every commit SHA from the first PDF commit onward is different.** Any other clone of this repository must be deleted and re-cloned — pulling into an old clone will merge the two histories back together and undo the whole operation.

**P5 — Verify.**

```bash
du -sh .git
git ls-files '*.pdf' '*.PDF' | wc -l
```

Expect `.git` around 2.4–2.6 GB and a count of **0**.

Then confirm nothing left the working tree — `find raw -iname '*.pdf' | wc -l` should still be **747**, and a sample should open from its original path. If that count has dropped, P2 was skipped or ran after P3; restore from the P1 bundle and start again.

## What is lost, and what is not

**Lost:** the ability to recover a PDF from git history. From here a PDF exists in the working tree and in Bill's backup of it, and nowhere else.

**Not changed: where the PDFs are.** They stay in `raw/`, beside the records they belong to, visible to anything that opens the folder. Nothing about working directly in `raw/` changes.

**Not lost:** the records themselves. Every markdown record in `raw/` stays tracked and committed, including the frontmatter, the body and the `url:` that makes the source citable. The standing requirement that `raw/`, `lookups/` and `wiki/` stay git-tracked is about those records, and it is unaffected — what leaves is the attached binary, not the evidence.

**The consequence to be deliberate about:** a backup outside git becomes the only protection for 2.61 GB of documents. Keeping that backup current is Bill's, and he has accepted it. Nothing about it falls to OSINT.

## Timing

Not while a session is mid-flight between `new/` and `raw/` — the rewrite must run on a settled tree with nothing uncommitted.

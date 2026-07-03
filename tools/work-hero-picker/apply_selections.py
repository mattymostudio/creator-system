#!/usr/bin/env python3
"""
Apply hero-selections.json (exported from the picker HTML) to the archive.

For every work where you picked a hero image, this creates a `_hero/` subfolder
inside that work and adds a symlink to the chosen file. Works you skipped are
left unchanged. Re-running the script replaces existing _hero/ contents.

Usage:
    python3 apply_selections.py path/to/hero-selections.json [--web-root <path>]

The script needs to know which directory the picker HTML was served from
(the "web root"), because image paths in the JSON are relative to that root.
If the JSON lives in your Downloads folder, pass --web-root pointing at the
folder you ran `python3 -m http.server` from.
"""
import argparse
import json
import os
import sys


def safe_symlink(src, dst):
    if os.path.lexists(dst):
        os.remove(dst)
    try:
        os.symlink(src, dst)
        return True
    except OSError as e:
        print(f"WARN symlink failed: {dst}: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path", help="Path to hero-selections.json (downloaded from the picker).")
    ap.add_argument("--web-root", required=True,
                    help="Directory you served via `python3 -m http.server`. "
                         "Image paths in the JSON are relative to this.")
    ap.add_argument("--hero-subdir", default="_hero",
                    help="Subfolder name inside each work (default: _hero).")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    web_root = os.path.abspath(args.web_root)
    if not os.path.isdir(web_root):
        sys.exit(f"web-root not a directory: {web_root}")

    with open(args.json_path) as f:
        data = json.load(f)

    selections = data.get("selections", {})
    works = {w["id"]: w for w in data.get("works", [])}

    n_picked = 0
    n_skipped = 0
    n_pending = 0

    for work_id, choice in selections.items():
        if choice == "__SKIP__":
            n_skipped += 1
            continue
        work = works.get(work_id)
        if not work:
            print(f"WARN unknown work id in JSON: {work_id}", file=sys.stderr)
            continue
        work_dir = os.path.join(web_root, work["rel_path"])
        if not os.path.isdir(work_dir):
            print(f"WARN work dir missing: {work_dir}", file=sys.stderr)
            continue
        chosen_file = os.path.join(work_dir, choice)
        if not os.path.exists(chosen_file) and not os.path.islink(chosen_file):
            print(f"WARN chosen file missing: {chosen_file}", file=sys.stderr)
            continue

        # follow if symlink, to get the real source target
        if os.path.islink(chosen_file):
            target = os.readlink(chosen_file)
        else:
            target = os.path.abspath(chosen_file)

        hero_dir = os.path.join(work_dir, args.hero_subdir)

        # The chosen filename may carry a subfolder prefix (e.g. "Photos/foo.JPG")
        # if the picker scanned recursively. Inside _hero/ we always flatten to
        # the basename so there's exactly one canonical hero per work.
        hero_basename = os.path.basename(choice)

        if args.dry_run:
            print(f"  WOULD: {work_dir} → {args.hero_subdir}/{hero_basename}")
            n_picked += 1
            continue

        # remove existing hero symlinks
        if os.path.exists(hero_dir):
            for f in os.listdir(hero_dir):
                p = os.path.join(hero_dir, f)
                if os.path.islink(p) or os.path.isfile(p):
                    try: os.remove(p)
                    except OSError: pass
        os.makedirs(hero_dir, exist_ok=True)
        if safe_symlink(target, os.path.join(hero_dir, hero_basename)):
            n_picked += 1

    # works with no selection → "pending"
    n_pending = sum(1 for w in works if w not in selections)

    print(f"Applied: {n_picked} hero(es) created, {n_skipped} works skipped, "
          f"{n_pending} works pending (no selection)",
          file=sys.stderr)


if __name__ == '__main__':
    main()

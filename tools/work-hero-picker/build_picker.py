#!/usr/bin/env python3
"""
Generate a self-contained HTML page for picking the hero image of every work
folder in your archive.

Use this when you have many folders, each containing several images of the same
piece (front, back, install, raw camera, edited export, etc.), and you want to
choose ONE canonical hero image per work — for a website, catalog, sales sheet,
or any standardized-display use case.

The HTML page works offline (after launch), persists picks in browser
localStorage, and exports a JSON file when you're done. A separate script
(`apply_selections.py`) takes that JSON and creates a `_hero/<filename>`
subfolder inside each work, with a symlink to the chosen image.

Usage:

    python3 build_picker.py --works-root path/to/archive

    # or with a glob for nested archives
    python3 build_picker.py --works-glob "archive/*/*"

The HTML is written next to your works root by default (or use --out).

Then:

    cd <directory containing the HTML>
    python3 -m http.server 8765
    # open http://localhost:8765/<your-html-name>.html

Click images to pick. Click "skip" if no image works. Click "Export selections"
when done — it downloads `hero-selections.json`. Pass that JSON to
`apply_selections.py`.
"""
import argparse
import glob
import json
import os
import re
import sys


IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.webp', '.tif', '.tiff', '.bmp'}
SKIP_EXTS = {'.psd', '.pdf', '.mov', '.mp4', '.zip', '.csv', '.xlsx', '.numbers',
             '.docx', '.txt', '.rtf', '.md', '.textclipping', '.ds_store',
             '.cr2', '.nef', '.arw', '.dng', '.raw'}
RENDERABLE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def score(filename, work_title, file_size_bytes):
    """Heuristic score for how likely a filename is the hero image. Higher = better."""
    name_lower = filename.lower()
    base, ext = os.path.splitext(filename)
    base_lower = base.lower()
    ext = ext.lower()
    s = 0

    if work_title:
        title_clean = re.sub(r'[^a-z0-9]+', '', work_title.lower())
        fn_clean = re.sub(r'[^a-z0-9]+', '', base_lower)
        if title_clean and title_clean in fn_clean:
            s += 5
        else:
            tokens = [t for t in re.split(r'[\s\-_]+', work_title.lower()) if len(t) >= 3]
            matched = sum(1 for t in tokens if re.sub(r'[^a-z0-9]+', '', t) in fn_clean)
            if tokens and matched / len(tokens) >= 0.5:
                s += 3
            elif matched >= 2:
                s += 2

    if 'front' in base_lower:
        s += 3
    if re.match(r'^[a-z][a-z0-9\-_\s]*[a-z0-9]$', base_lower) and not re.match(r'^img', base_lower):
        s += 2
    if ext in {'.jpg', '.jpeg', '.png'}:
        s += 2
    if ext in {'.heic', '.heif', '.gif', '.bmp', '.tif', '.tiff'}:
        s -= 1

    if len(base) > 12:
        s += 2
    elif len(base) <= 6:
        s -= 1

    mb = file_size_bytes / (1024 * 1024)
    s += min(int(mb), 4)

    if re.match(r'^(img[_ ]|os6a|dsc|p\d{7})', base_lower):
        s -= 3
    if base_lower.startswith('screen shot') or base_lower.startswith('screenshot'):
        s -= 5
    if 'back' in name_lower:
        s -= 2
    if re.search(r'__\d+$', base):
        s -= 1
    if '.compressed' in name_lower or 'thumbnail' in name_lower:
        s -= 2
    if re.match(r'^\d+$', base):
        s -= 5

    return s


def find_work_folders(works_root, works_glob, scan_depth):
    """Return absolute paths of folders to treat as works."""
    if works_glob:
        matches = sorted(
            p for p in glob.glob(works_glob)
            if os.path.isdir(p) and not os.path.basename(p).startswith('_')
        )
        return [os.path.abspath(p) for p in matches]
    if not works_root:
        sys.exit("Provide --works-root or --works-glob")
    works_root = os.path.abspath(works_root)
    if scan_depth == 1:
        return sorted(
            os.path.join(works_root, d)
            for d in os.listdir(works_root)
            if os.path.isdir(os.path.join(works_root, d)) and not d.startswith('_')
        )
    # recursive: any folder that contains image files
    found = []
    for root, dirs, files in os.walk(works_root):
        # skip _-prefixed (meta folders like _hero, _meta, etc.)
        dirs[:] = [d for d in dirs if not d.startswith('_')]
        if any(os.path.splitext(f)[1].lower() in IMAGE_EXTS for f in files):
            found.append(root)
    return sorted(found)


SUBFOLDER_BIAS = {
    'photos': 4, 'photo': 4, 'final': 4, 'finals': 4, 'hero': 6,
    'production': 1, 'install': 2, 'installs': 2,
    'engagement': -2, 'press': -1, 'social': -2,
    'assets': -3, 'design': -2, 'designs': -2, 'mockups': -2, 'brand assets': -3,
    'to-sort': -1, 'tosort': -1, '_tosort': -1,
    'invoice': -10, 'invoices': -10, 'contract': -10, 'contracts': -10,
}


def candidates_for(work_dir, web_root, recursive=False):
    """Return ranked list of candidate image dicts for a given work folder."""
    title = os.path.basename(work_dir)
    m = re.match(r'^\d{4}\s*-\s*(.+)$', title)
    if m:
        title = m.group(1)
    items = []
    if recursive:
        walk = []
        for root, dirs, files in os.walk(work_dir):
            dirs[:] = [d for d in dirs if not d.startswith('_')]
            for fn in files:
                walk.append((root, fn))
    else:
        walk = [(work_dir, fn) for fn in os.listdir(work_dir)]
    for root, fn in walk:
        if fn == '.DS_Store':
            continue
        if fn.startswith('_meta') or fn.startswith('_series'):
            continue
        full = os.path.join(root, fn)
        if not os.path.isfile(full) and not os.path.islink(full):
            continue
        ext = os.path.splitext(fn)[1].lower()
        if ext in SKIP_EXTS or ext not in IMAGE_EXTS:
            continue
        try:
            real = os.path.realpath(full)
            sz = os.path.getsize(real)
        except OSError:
            sz = 0
        rel_to_web = os.path.relpath(full, web_root)
        rel_to_work = os.path.relpath(full, work_dir)
        s = score(fn, title, sz)
        if recursive:
            for part in os.path.dirname(rel_to_work).split(os.sep):
                bias = SUBFOLDER_BIAS.get(part.lower())
                if bias is not None:
                    s += bias
        items.append({
            "filename": rel_to_work.replace(os.sep, '/') if recursive else fn,
            "path": rel_to_web.replace(os.sep, '/'),
            "score": s,
            "bytes": sz,
            "ext": ext,
            "renderable": ext in RENDERABLE_EXTS,
        })
    items.sort(key=lambda c: -c["score"])
    return items


def main():
    ap = argparse.ArgumentParser(description="Generate a hero-image picker HTML page.")
    ap.add_argument("--works-root", help="Folder whose direct subfolders are works.")
    ap.add_argument("--works-glob", help="Glob matching work folders (overrides --works-root).")
    ap.add_argument("--scan-depth", type=int, default=1,
                    help="With --works-root: 1 = direct subfolders (default), >1 = recursive scan for image-bearing folders.")
    ap.add_argument("--out", help="HTML output path (defaults to <web-root>/hero-picker.html).")
    ap.add_argument("--web-root", help="Root directory the HTTP server will serve from. "
                                       "Image paths in the HTML are relative to this. "
                                       "Defaults to the parent of --out.")
    ap.add_argument("--group-by-parent", action="store_true",
                    help="Display works grouped by their parent folder name (e.g. when each work lives at <category>/<work>/).")
    ap.add_argument("--recursive-candidates", action="store_true",
                    help="Scan all subfolders inside each work for candidate images "
                         "(use when a work folder is organized into Photos/, Production/, etc.).")
    ap.add_argument("--title", default="Hero Image Picker",
                    help="Page title shown in the browser.")
    args = ap.parse_args()

    work_dirs = find_work_folders(args.works_root, args.works_glob, args.scan_depth)
    if not work_dirs:
        sys.exit("No work folders found.")

    # Decide output and web-root
    if args.out:
        out_path = os.path.abspath(args.out)
    elif args.works_root:
        out_path = os.path.abspath(os.path.join(args.works_root, "..", "hero-picker.html"))
    else:
        # works_glob — fall back to cwd
        out_path = os.path.abspath("hero-picker.html")

    web_root = os.path.abspath(args.web_root) if args.web_root else os.path.dirname(out_path)

    works_data = []
    n_candidates = 0
    for wd in work_dirs:
        cands = candidates_for(wd, web_root, recursive=args.recursive_candidates)
        if not cands:
            # work folder with no image candidates — still include so user sees it
            cands = []
        n_candidates += len(cands)
        parent = os.path.basename(os.path.dirname(wd))
        works_data.append({
            "id": slugify(os.path.relpath(wd, web_root)),
            "group": parent if args.group_by_parent else "",
            "work": os.path.basename(wd),
            "rel_path": os.path.relpath(wd, web_root).replace(os.sep, '/'),
            "candidates": cands,
        })

    data_json = json.dumps(works_data)
    html = HTML_TEMPLATE \
        .replace("__DATA__", data_json) \
        .replace("__TITLE__", args.title) \
        .replace("__GROUP_BY_PARENT__", "true" if args.group_by_parent else "false")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Built {out_path}")
    print(f"  {len(works_data)} works, {n_candidates} candidate images")
    print(f"  web root: {web_root}")
    print()
    print("Next steps:")
    print(f"  cd {web_root!r}")
    print(f"  python3 -m http.server 8765")
    print(f"  open http://localhost:8765/{os.path.basename(out_path)}")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  :root {
    --bg: #0e0e0e;
    --fg: #f4f4f4;
    --muted: #888;
    --border: #2a2a2a;
    --accent: #4ade80;
    --skip: #f87171;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.4 -apple-system, BlinkMacSystemFont, sans-serif;
         background: var(--bg); color: var(--fg); }
  header { position: sticky; top: 0; z-index: 100; background: #181818;
           border-bottom: 1px solid var(--border); padding: 12px 20px; }
  header h1 { margin: 0 0 6px; font-size: 16px; font-weight: 600; }
  header .stats { color: var(--muted); font-size: 12px; }
  header .controls { margin-top: 10px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  header button { background: #2a2a2a; color: var(--fg); border: 1px solid var(--border);
                  padding: 6px 12px; border-radius: 4px; cursor: pointer; font: inherit; }
  header button:hover { background: #333; }
  header button.primary { background: var(--accent); color: #000; border-color: var(--accent); font-weight: 600; }
  header select { background: #2a2a2a; color: var(--fg); border: 1px solid var(--border);
                  padding: 5px 8px; border-radius: 4px; font: inherit; }
  header progress { width: 200px; height: 8px; }
  main { padding: 20px; max-width: 1400px; margin: 0 auto; }
  .group-header { margin: 30px 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border);
                  font-size: 14px; font-weight: 600; color: var(--muted); text-transform: uppercase;
                  letter-spacing: 0.05em; }
  .work { margin-bottom: 24px; padding: 14px; background: #161616; border-radius: 8px;
          border: 1px solid var(--border); transition: border-color 0.15s; }
  .work[data-status="picked"] { border-color: var(--accent); }
  .work[data-status="skipped"] { border-color: var(--skip); opacity: 0.6; }
  .work-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .work-title { font-weight: 600; font-size: 14px; }
  .work-status { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
  .work-status[data-state="picked"] { color: var(--accent); }
  .work-status[data-state="skipped"] { color: var(--skip); }
  .candidates { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
  .card { position: relative; background: #0a0a0a; border: 2px solid var(--border); border-radius: 6px;
          overflow: hidden; cursor: pointer; aspect-ratio: 1 / 1; transition: border-color 0.1s, transform 0.1s; }
  .card:hover { border-color: #555; transform: translateY(-1px); }
  .card.selected { border-color: var(--accent); }
  .card img { width: 100%; height: 100%; object-fit: contain; display: block; }
  .card .placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
                       color: var(--muted); font-size: 11px; padding: 12px; text-align: center; }
  .card .meta { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.85);
                color: var(--fg); font-size: 10px; padding: 4px 6px; line-height: 1.3;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .card .score { position: absolute; top: 4px; right: 4px; background: rgba(0,0,0,0.6);
                 color: var(--fg); font-size: 10px; padding: 2px 5px; border-radius: 3px; }
  .skip-btn { background: #2a1a1a; color: var(--skip); border: 1px dashed var(--skip);
              padding: 6px 12px; border-radius: 4px; cursor: pointer; font: inherit;
              font-size: 12px; margin-top: 8px; }
  .skip-btn:hover { background: #3a1a1a; }
  .work[hidden] { display: none; }
  .empty-note { color: var(--muted); font-size: 12px; }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <div class="stats">
    <span id="stats-text">Loading…</span>
    · <progress id="progress" max="100" value="0"></progress>
    · <span id="progress-text">0%</span>
  </div>
  <div class="controls">
    <select id="filter">
      <option value="all">Show: all works</option>
      <option value="pending">Show: pending only</option>
      <option value="picked">Show: picked only</option>
      <option value="skipped">Show: skipped only</option>
    </select>
    <button id="export-btn" class="primary">Export selections (JSON)</button>
    <button id="clear-btn">Clear all selections</button>
    <span class="stats">Tip: click an image to pick. Click "skip" if no image works.</span>
  </div>
</header>
<main id="main"></main>
<script>
const DATA = __DATA__;
const GROUP_BY_PARENT = __GROUP_BY_PARENT__;
const KEY = "hero-picker-selections-v1";

function loadSelections() {
  try { return JSON.parse(localStorage.getItem(KEY) || "{}"); }
  catch { return {}; }
}
function saveSelections(sel) { localStorage.setItem(KEY, JSON.stringify(sel)); }

let selections = loadSelections();

function fmtBytes(b) {
  if (b < 1024) return b + 'B';
  if (b < 1024*1024) return (b/1024).toFixed(0) + 'KB';
  return (b/(1024*1024)).toFixed(1) + 'MB';
}

function render() {
  const main = document.getElementById('main');
  main.innerHTML = '';
  let lastGroup = null;
  for (const w of DATA) {
    if (GROUP_BY_PARENT && w.group !== lastGroup) {
      const h = document.createElement('div');
      h.className = 'group-header';
      h.textContent = w.group + ' (' + DATA.filter(x => x.group === w.group).length + ' works)';
      main.appendChild(h);
      lastGroup = w.group;
    }
    const sel = selections[w.id];
    let status = 'pending';
    if (sel === '__SKIP__') status = 'skipped';
    else if (sel) status = 'picked';

    const work = document.createElement('div');
    work.className = 'work';
    work.dataset.id = w.id;
    work.dataset.status = status;
    work.dataset.group = w.group || '';

    const header = document.createElement('div');
    header.className = 'work-header';
    const title = document.createElement('div');
    title.className = 'work-title';
    title.textContent = w.work;
    const st = document.createElement('div');
    st.className = 'work-status';
    st.dataset.state = status;
    st.textContent = status;
    header.appendChild(title);
    header.appendChild(st);
    work.appendChild(header);

    if (w.candidates.length === 0) {
      const p = document.createElement('div');
      p.className = 'empty-note';
      p.textContent = '(no candidate images in this work folder)';
      work.appendChild(p);
    } else {
      const grid = document.createElement('div');
      grid.className = 'candidates';
      w.candidates.forEach(c => {
        const card = document.createElement('div');
        card.className = 'card' + (sel === c.filename ? ' selected' : '');
        card.dataset.fn = c.filename;
        if (c.renderable) {
          const img = document.createElement('img');
          img.loading = 'lazy';
          img.src = encodeURI(c.path);
          img.alt = c.filename;
          card.appendChild(img);
        } else {
          const ph = document.createElement('div');
          ph.className = 'placeholder';
          ph.textContent = c.ext.toUpperCase().slice(1) + ' — ' + c.filename;
          card.appendChild(ph);
        }
        const score = document.createElement('div');
        score.className = 'score';
        score.textContent = c.score;
        card.appendChild(score);
        const meta = document.createElement('div');
        meta.className = 'meta';
        meta.textContent = c.filename + ' · ' + fmtBytes(c.bytes);
        card.appendChild(meta);
        card.addEventListener('click', () => pick(w.id, c.filename));
        grid.appendChild(card);
      });
      work.appendChild(grid);
    }

    const skip = document.createElement('button');
    skip.className = 'skip-btn';
    skip.textContent = sel === '__SKIP__' ? '✓ Skipped (click to unskip)' : 'No suitable hero — skip this work';
    skip.addEventListener('click', () => skipWork(w.id));
    work.appendChild(skip);

    main.appendChild(work);
  }
  applyFilter();
  updateStats();
}

function pick(workId, filename) {
  if (selections[workId] === filename) {
    delete selections[workId];
  } else {
    selections[workId] = filename;
  }
  saveSelections(selections);
  rerenderWork(workId);
  updateStats();
}

function skipWork(workId) {
  if (selections[workId] === '__SKIP__') {
    delete selections[workId];
  } else {
    selections[workId] = '__SKIP__';
  }
  saveSelections(selections);
  rerenderWork(workId);
  updateStats();
}

function rerenderWork(workId) {
  const el = document.querySelector(`.work[data-id="${workId}"]`);
  if (!el) return;
  const sel = selections[workId];
  let status = 'pending';
  if (sel === '__SKIP__') status = 'skipped';
  else if (sel) status = 'picked';
  el.dataset.status = status;
  const st = el.querySelector('.work-status');
  st.textContent = status;
  st.dataset.state = status;
  el.querySelectorAll('.card').forEach(c => {
    c.classList.toggle('selected', c.dataset.fn === sel);
  });
  const skip = el.querySelector('.skip-btn');
  skip.textContent = sel === '__SKIP__' ? '✓ Skipped (click to unskip)' : 'No suitable hero — skip this work';
  applyFilter();
}

function updateStats() {
  const total = DATA.length;
  let picked = 0, skipped = 0;
  for (const w of DATA) {
    const s = selections[w.id];
    if (s === '__SKIP__') skipped++;
    else if (s) picked++;
  }
  const done = picked + skipped;
  document.getElementById('stats-text').textContent =
    `${total} works · ${picked} picked · ${skipped} skipped · ${total - done} pending`;
  const pct = total ? Math.round(100 * done / total) : 0;
  document.getElementById('progress').value = pct;
  document.getElementById('progress-text').textContent = pct + '%';
}

function applyFilter() {
  const v = document.getElementById('filter').value;
  document.querySelectorAll('.work').forEach(el => {
    const status = el.dataset.status;
    let show = true;
    if (v === 'pending') show = status === 'pending';
    else if (v === 'picked') show = status === 'picked';
    else if (v === 'skipped') show = status === 'skipped';
    el.hidden = !show;
  });
  document.querySelectorAll('.group-header').forEach(h => {
    let next = h.nextElementSibling;
    let any = false;
    while (next && !next.classList.contains('group-header')) {
      if (next.classList.contains('work') && !next.hidden) { any = true; break; }
      next = next.nextElementSibling;
    }
    h.hidden = !any;
  });
}

document.getElementById('filter').addEventListener('change', applyFilter);
document.getElementById('export-btn').addEventListener('click', () => {
  const out = { exported_at: new Date().toISOString(), selections,
                works: DATA.map(w => ({ id: w.id, work: w.work, rel_path: w.rel_path })) };
  const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'hero-selections.json';
  a.click();
});
document.getElementById('clear-btn').addEventListener('click', () => {
  if (confirm('Clear all picks and skips? This cannot be undone.')) {
    selections = {};
    saveSelections(selections);
    render();
  }
});

render();
</script>
</body>
</html>
"""


if __name__ == '__main__':
    main()

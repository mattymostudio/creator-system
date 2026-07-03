#!/usr/bin/env python3
"""
Folder Watcher — monitors a folder for new screenshots, automatically
OCRs, classifies, extracts entities, and creates Obsidian vault notes.

Usage:
    python3 folder_watcher.py --watch-dir ~/Screenshots --vault-dir Organized/Vault

    # Generate launchd plist for auto-start at login
    python3 folder_watcher.py --install-launchd --watch-dir ~/Screenshots --vault-dir Organized/Vault
"""

import argparse
import logging
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')
logging.getLogger('exifread').setLevel(logging.CRITICAL)

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pytesseract
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

# Import our modules
from classify_detailed import classify
from entity_extractor import extract_entities
from obsidian_builder import (
    build_note, write_note, create_image_symlink,
    sanitize_category,
)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.heic', '.heif', '.webp'}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('watcher')


def extract_text(filepath):
    """OCR a screenshot image."""
    try:
        img = Image.open(filepath)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return pytesseract.image_to_string(img, lang='eng').strip()
    except Exception as e:
        log.error(f"OCR failed for {filepath}: {e}")
        return None


def get_file_date(filepath):
    """Get file creation date."""
    st = os.stat(filepath)
    if hasattr(st, 'st_birthtime'):
        return datetime.fromtimestamp(st.st_birthtime)
    return datetime.fromtimestamp(st.st_mtime)


def process_screenshot(filepath, vault_dir, screenshots_archive=None):
    """Full pipeline: OCR → classify → extract → Obsidian note."""
    filepath = Path(filepath)
    file_stem = filepath.stem
    month = get_file_date(str(filepath)).strftime('%Y-%m')

    log.info(f"Processing: {filepath.name}")

    # 1. OCR
    text = extract_text(str(filepath))
    if not text:
        log.warning(f"No text extracted from {filepath.name}")
        text = ''

    # 2. Classify
    category, score, _ = classify(text)
    log.info(f"  Category: {category} (score: {score})")

    # 3. Extract entities
    entities = extract_entities(text, category=category)

    # 4. Create image symlink
    vault_dir = Path(vault_dir)
    attach_dir = vault_dir / '_attachments' / month
    attach_dir.mkdir(parents=True, exist_ok=True)

    link_path = attach_dir / filepath.name
    if not link_path.exists():
        os.symlink(filepath.resolve(), link_path)
    image_rel_path = f'_attachments/{month}/{filepath.name}'

    # 5. Build and write note
    note_content = build_note(
        file_stem, month, category, score,
        text, entities, image_rel_path
    )
    note_path = write_note(vault_dir, file_stem, month, note_content)

    # 6. Save OCR text alongside (for future re-classification)
    if screenshots_archive:
        archive_dir = Path(screenshots_archive) / sanitize_category(category) / month
        archive_dir.mkdir(parents=True, exist_ok=True)
        txt_path = archive_dir / f'{file_stem}.txt'
        if text:
            txt_path.write_text(text, encoding='utf-8')

    # Summary
    entity_summary = []
    for key, values in entities.items():
        if key.startswith('_'):
            continue
        if values:
            entity_summary.append(f"{len(values)} {key}")

    if entity_summary:
        log.info(f"  Extracted: {', '.join(entity_summary)}")
    log.info(f"  Note: {note_path}")

    return note_path


class ScreenshotHandler(FileSystemEventHandler):
    """Handles new screenshot files."""

    def __init__(self, vault_dir, screenshots_archive=None):
        self.vault_dir = vault_dir
        self.screenshots_archive = screenshots_archive
        self._processing = set()

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        if filepath.suffix.lower() not in IMAGE_EXTENSIONS:
            return

        if filepath.name.startswith('.'):
            return

        # Debounce — wait for file to finish writing
        if str(filepath) in self._processing:
            return
        self._processing.add(str(filepath))

        try:
            # Wait for file to be fully written
            time.sleep(2)

            # Verify file still exists and is non-empty
            if not filepath.exists() or filepath.stat().st_size == 0:
                return

            process_screenshot(filepath, self.vault_dir, self.screenshots_archive)

        except Exception as e:
            log.error(f"Error processing {filepath.name}: {e}")
        finally:
            self._processing.discard(str(filepath))


def generate_launchd_plist(watch_dir, vault_dir, script_dir):
    """Generate a macOS launchd plist for auto-start at login."""
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.photoprocessing.screenshotwatcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_dir}/folder_watcher.py</string>
        <string>--watch-dir</string>
        <string>{watch_dir}</string>
        <string>--vault-dir</string>
        <string>{vault_dir}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{script_dir}/watcher.log</string>
    <key>StandardErrorPath</key>
    <string>{script_dir}/watcher.log</string>
    <key>WorkingDirectory</key>
    <string>{script_dir}</string>
</dict>
</plist>"""

    plist_dir = Path.home() / 'Library' / 'LaunchAgents'
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_path = plist_dir / 'com.photoprocessing.screenshotwatcher.plist'
    plist_path.write_text(plist_content)

    print(f"LaunchAgent plist written to: {plist_path}")
    print(f"\nTo enable:")
    print(f"  launchctl load {plist_path}")
    print(f"\nTo disable:")
    print(f"  launchctl unload {plist_path}")
    print(f"\nLogs: {script_dir}/watcher.log")


def main():
    parser = argparse.ArgumentParser(description='Watch folder for new screenshots')
    parser.add_argument('--watch-dir', '-w', required=True,
                        help='Directory to watch for new screenshots')
    parser.add_argument('--vault-dir', '-v', default='Organized/Vault',
                        help='Obsidian vault directory')
    parser.add_argument('--archive-dir', '-a', default=None,
                        help='Directory to save OCR text (default: none)')
    parser.add_argument('--install-launchd', action='store_true',
                        help='Generate launchd plist for auto-start')
    args = parser.parse_args()

    watch_dir = Path(args.watch_dir).expanduser().resolve()
    vault_dir = Path(args.vault_dir).resolve()
    script_dir = Path(__file__).parent.resolve()

    if args.install_launchd:
        generate_launchd_plist(watch_dir, vault_dir, script_dir)
        return

    if not watch_dir.exists():
        print(f"Creating watch directory: {watch_dir}")
        watch_dir.mkdir(parents=True, exist_ok=True)

    vault_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Watching: {watch_dir}")
    log.info(f"Vault: {vault_dir}")
    log.info(f"Drop screenshots into {watch_dir} to auto-process")
    log.info("Press Ctrl+C to stop\n")

    handler = ScreenshotHandler(vault_dir, args.archive_dir)
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping watcher...")
        observer.stop()

    observer.join()
    log.info("Watcher stopped.")


if __name__ == '__main__':
    main()

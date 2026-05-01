# Drop your photos here

Copy (or move) a batch of photos into this folder before running the processor.

Typical source: an iPhone camera roll export, a `Photos.app` export, or a
folder of screenshots.

Supported formats:
- `.jpg`, `.jpeg`, `.png`, `.heic`, `.heif`, `.mp4`, `.mov`

**The pipeline expects a flat folder.** Subfolders will be scanned
recursively, but the output is organized by date/type.

Once photos are here, from the `photo-processor/` directory run:

```bash
./process.sh new --copy     # safe default — originals stay put
./process.sh new --move     # move the files into ./Organized/
```

Output lands in `./Organized/`.

The demo starts working with even a single image — drop one `.jpg` in here
and run `./process.sh new --copy` to see the pipeline flow end-to-end.

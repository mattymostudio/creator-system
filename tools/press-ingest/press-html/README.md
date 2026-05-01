# Cleaned-HTML article output

`process_articles.py` writes scraped, cleaned HTML press articles into this
folder. Each file is named `{year}-{outlet}.html` — for example
`2023-example-magazine.html`.

From here, `ingest_to_vault.py` converts them into Obsidian markdown notes
in your vault's `02_SOURCES/Articles/` folder.

To demo without running the full scrape, drop a hand-made HTML file in here
with minimal markup:

```html
<!DOCTYPE html>
<html>
<head><title>Sample Article</title></head>
<body>
  <article>
    <h1>Sample Headline</h1>
    <div class="byline">By A. Writer · 2024-05-01</div>
    <div class="article-body">
      <p>Body text goes here…</p>
    </div>
  </article>
</body>
</html>
```

Save it as `2024-sample-outlet.html` and run `python3 ingest_to_vault.py`.

# Press Article Screenshot & HTML Cleanup Prompt

Give this prompt to Claude Code (web app or desktop) with browser tools enabled.

---

## THE PROMPT

```
I need you to process a list of press articles for my company's press kit. For each article, you will:

1. **Navigate** to the article URL
2. **Take a full-page screenshot** and save it to disk (for use in a press kit)
3. **Extract the article HTML** from the page
4. **Create a cleaned HTML file** that preserves ONLY:
   - The publication's logo/branding (if visible)
   - The article headline
   - The author name and date
   - The full article body text and any inline images
   - Basic styling that matches the publication's look
5. **Remove** from the HTML:
   - All ads (display ads, inline ads, sponsored content blocks)
   - Navigation bars, headers, footers, sidebars
   - Cookie consent banners and popups
   - Social sharing buttons
   - Comments sections
   - Newsletter signup forms
   - Related articles / recommended content widgets
   - All tracking scripts, analytics, and third-party JavaScript
   - Paywall overlays (if present)
   - Video autoplay elements (unless the article IS a video)

## File naming convention

For screenshots:
`press-screenshots/[YEAR]-[outlet-name-slug]-screenshot.png`

For cleaned HTML:
`press-html/[YEAR]-[outlet-name-slug].html`

Example:
- `press-screenshots/2020-new-york-times-screenshot.png`
- `press-html/2020-new-york-times.html`

## Cleaned HTML template

Each cleaned HTML file should follow this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Headline] — [Publication Name]</title>
  <style>
    /* Clean, readable styling */
    body {
      font-family: Georgia, 'Times New Roman', serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 20px;
      color: #1a1a1a;
      line-height: 1.7;
      background: #fff;
    }
    .publication-branding {
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e0e0e0;
    }
    .publication-branding img {
      max-height: 40px;
      width: auto;
    }
    .publication-name {
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #666;
    }
    h1 {
      font-size: 2em;
      line-height: 1.2;
      margin: 0 0 16px 0;
    }
    .byline {
      font-size: 14px;
      color: #666;
      margin-bottom: 32px;
    }
    .article-body p {
      margin-bottom: 1.2em;
    }
    .article-body img {
      max-width: 100%;
      height: auto;
      margin: 24px 0;
    }
    .article-body figcaption {
      font-size: 13px;
      color: #888;
      margin-top: -16px;
      margin-bottom: 24px;
    }
    .original-link {
      margin-top: 48px;
      padding-top: 16px;
      border-top: 1px solid #e0e0e0;
      font-size: 13px;
      color: #999;
    }
    .original-link a {
      color: #666;
    }
  </style>
</head>
<body>
  <div class="publication-branding">
    <!-- Publication logo if available, otherwise text name -->
    <div class="publication-name">[PUBLICATION NAME]</div>
  </div>
  <article>
    <h1>[HEADLINE]</h1>
    <div class="byline">By [AUTHOR] · [DATE]</div>
    <div class="article-body">
      [CLEANED ARTICLE CONTENT — paragraphs, images, subheadings]
    </div>
  </article>
  <div class="original-link">
    Originally published by <a href="[ORIGINAL_URL]">[Publication Name]</a>
  </div>
</body>
</html>
```

## Handling edge cases

- **YouTube/video links**: Just take a screenshot. Skip the HTML cleanup. Note it as "video content" in the log.
- **Dead links (404/timeout)**: Log the failure. Skip and move to the next article.
- **Paywalled content**: Capture whatever is visible. Note "partial — paywalled" in the log.
- **Social media posts (Facebook, etc.)**: Screenshot only. Skip HTML cleanup.

## Progress log

After processing each article, append a line to `press-processing-log.md`:
```
| [status] | [year] | [outlet] | [headline] | [screenshot: yes/no] | [html: yes/no] | [notes] |
```

Status should be one of: done, partial, skipped, dead-link

## Here is the list of articles to process

Go to https://www.yourdomain.example/headlines and extract all the press links from the page. Process them in chronological order starting from the most recent (2026) working backward.

Process these in batches of 10-15 articles per session. At the end of each batch, tell me which articles you completed and which remain.

Start with the first batch now.
```

---

## TIPS FOR RUNNING THIS

1. **Batch size**: Don't try all 90+ in one session. Do 10-15 at a time.

2. **Create the output folders first** before starting:
   ```
   mkdir -p press-screenshots press-html
   ```

3. **After all batches are done**, you'll have:
   - A folder of ~80 screenshots for your press kit
   - A folder of ~60-70 clean HTML files (minus videos/dead links)
   - A processing log showing status of every article

4. **For your website integration**, you can host the clean HTML files as static pages and link to them from your press page, or embed them in iframes.

5. **If a specific publication's styling matters**, you can tell Claude: "For the [Publication] article, try to match their font and color scheme more closely in the cleaned HTML."

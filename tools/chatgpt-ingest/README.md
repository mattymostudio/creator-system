# chatgpt-ingest

Parses a ChatGPT export (`conversations.json`) and sorts conversation
titles into topic buckets — art, real estate, memoir, finance, etc. —
for later review or vault integration.

Uses Python standard library only. No LLM calls. No network.

## Get your export

[help.openai.com — How do I export my ChatGPT data?](https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data)

Drop the `conversations.json` from your export into `ChatGPT Download/`,
replacing the sample file that ships here.

## Standalone use (Path B)

```bash
cd chatgpt-ingest
python3 parse_conversations.py
```

Output lands in `parsed_domains/{art_park,real_estate,finance,memoir_creative,life_personal,reference_legal,uncategorized}.json`.

Each JSON file is a list of conversations (title, date, messages)
categorized into that domain. Read them directly, or feed them into
something else.

## Vault-aware use (Path A)

From Claude Code in your vault root:

> *"Run chatgpt-ingest against my latest export, then write one source
> note per conversation into `02_SOURCES/ChatGPT/{domain}/`."*

Claude will run `parse_conversations.py`, then take the resulting JSON
and generate properly front-mattered Obsidian notes per conversation.

## Customizing topics

The `DOMAIN_RULES` dict at the top of `parse_conversations.py` holds
the keyword lists per domain. Edit these to match your own interests —
add keywords, rename domains, or create new ones. It's just a dict.

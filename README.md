# piax-gen

```bash
npx skills add ImageCraftStudio/piax-gen
```

The CLI places this skill where Cursor, Claude Code, Codex, and other agents load skills. Python 3 is required.

Zip fallback (ChatGPT, or no npx): https://www.piax.org/skills/piax-gen.zip

Ask the agent to generate an image or video. If not signed in, it opens PIAX in the browser. No API key copy/export. Switch accounts with `--logout` then `--login`.

If a generate fails, the script lists other models. Ask the user whether to retry with one of them.

Defaults (omit `--model`):

- image / image_edit → `gpt-image-2.5`
- video → `seedance-2.5` (5s / 480p / 16:9)

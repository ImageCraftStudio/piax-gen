---
name: piax-gen
description: Generate and edit images or generate videos via PIAX. Use when the user asks to create or edit an image, poster, hero, cover, thumbnail, logo, icon, wallpaper, or to generate a video, reel, or image-to-video, including GPT Image 2.5, Seedance 2.5, Agnes, Wan 3.0, Gemini Omni Flash, Flux 3, GPT Image, Seedance, Kling, Flux, Sora, Veo, Wan, Nano Banana, Imagen, Ideogram, Grok, Muse, Luma, Runway, Vidu, MiniMax, Happy Horse.
---

# PIAX media generation

Always run `scripts/generate.py` with `python3`. Do not curl PIAX APIs yourself.
Reply in the user's language. Keep URLs verbatim.

Do not ask for environment variables, API keys, email codes, or passwords. Do not print tokens.
Do not name Cursor, Codex, or any specific product in user-facing copy — say “your agent”.

## Login

Do not run `--who` before every generate. Generate first. If the script returns `auth_required` / `auth_invalid` / `auth_pending`, then log in.

`--login` is a no-op if already signed in. If a browser session is already waiting, it **resumes** the same URL (does not mint a new key).

1. Run `--login`. Copy `error.action.url` or the stderr line to the user verbatim.
2. Tell them: sign in or register in the browser (same account as www.piax.org). If a window did not open, open that URL. If the page already shows an account, they can continue as that user or switch accounts there.
3. If the command returns `loggedIn: true`, greet with the display name and retry the generate. Do not print a token.
4. If it returns `auth_pending`, show the URL again, ask them to finish in the browser, then run `--login` again (resume). Timeout or expired → `--login` again.

```bash
python3 scripts/generate.py --login
python3 scripts/generate.py --who
```

Switch PIAX account:

```bash
python3 scripts/generate.py --logout
python3 scripts/generate.py --login
```

## Intake (before calling generate)

Ask at most 1–2 short questions. Prefer defaults.

- Image, purpose/ratio unclear → default square (`1:1` / 1024).
  Posters → `3:4` or `9:16`. Banners/hero → `16:9`.
- Edit existing image → `--kind image_edit` with `--image`, not a new generate.
- Bare "make a video" with no subject → ask one question, STOP.
- Video defaults: `5s` / `480p` / `16:9` on Seedance. Reels/stories → `9:16`.
- Local file or URL → pass `--image`.
- Midjourney video needs `--image`. If they have no still, pick another video model.

Write a specific prompt (subject, style, lighting, on-image text, motion/camera for video).

## Model

Pass `--model` only when the user names one. Otherwise omit it and use script defaults:

- image / image_edit → `gpt-image-2.5`
- video → `seedance-2.5`

```bash
python3 scripts/generate.py --list --kind image
python3 scripts/generate.py --list --kind video
```

Fuzzy-match common aliases (seedream, kling, flux, wan, sora, veo, gpt-image, nano banana, grok, imagen, ideogram).
If several variants match, the script picks the family default. Ask only if it still errors.
Do not enumerate the full catalog unless the user asks what is available.
Do not pass a ratio/duration/resolution the model's `--list` row does not allow.

## Size

Do not memorize sizes. If the user names a ratio, duration, or resolution, run `--list` for that `--kind` and copy values from **that model's row**.

- `--ratio` ← `ratios`. Pixel models also accept `sizes` (`1024x576` or `16:9`). Default image `1:1`, video `16:9`.
- `--duration` / `--resolution` ← those lists. Image `resolutions` are `1K`/`2K`/`4K` (Agnes also `3K`) when present.
- `"fixed": true` (`dall-e-3`, `imagen`) → always `1024x1024`; do not pass `--ratio`.

Defaults when omitted: image `1:1` (1024); Seedance 2.5 video `5` / `480p` / `16:9`.

## Commands

Image:

```bash
python3 scripts/generate.py --kind image --prompt "..."
python3 scripts/generate.py --kind image --model seedream5 --prompt "..." --ratio 16:9 --out ./hero.png
```

Edit:

```bash
python3 scripts/generate.py --kind image_edit --prompt "..." --image ./src.png
```

Video (text or image-to-video):

```bash
python3 scripts/generate.py --kind video --prompt "..."
python3 scripts/generate.py --kind video --model kling --image ./shot.png --out ./clip.mp4
```

Omit `--out` unless the user wants a specific path; the script writes a timestamped file.

## Billing errors — print URL, then STOP

Print `error.action.url`, then STOP. Do not retry. Do not switch kind unless the user asks.

| script error.code | API `code` | Tell the user | URL |
|---|---|---|---|
| auth_required / auth_invalid / auth_pending | `errorCode=auth_invalid` or `406` | Sign in via `--login` | `error.action.url` (prefer over the bare /connect page) |
| plan_required | `401` (signed in; plan too low) | Image/edit needs Pro; video needs Unlimited | https://www.piax.org/pricing |
| insufficient_credits | `409` | Top up credits or upgrade | https://www.piax.org/pricing/credits |
| generation_failed | other | Show the reason; offer another model | — |

After they say they upgraded / topped up / signed in, rerun once with the same prompt.

## Model failed — offer another model, then STOP

On `generation_failed` (timeout, provider error, no taskId, download fail):

1. Show the reason in the user's language. This is not a billing issue.
2. Print `error.context.alternatives` (or the “Try another model:” line). Ask which one to use. Do **not** retry the same `--model`.
3. If they pick one, rerun once with that `--model` and the same prompt. If they say “any” / “try another”, use the first alternative once.
4. If the second model also fails, STOP. Do not keep switching. Point to https://www.piax.org/ai-models.

```bash
python3 scripts/generate.py --kind image --model seedream5 --prompt "..."
```

## After success

Confirm in 1–2 sentences. Give the local `file` path. Do not dump the CDN URL as a fake download button.

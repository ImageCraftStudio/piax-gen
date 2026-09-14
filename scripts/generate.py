#!/usr/bin/env python3
"""PIAX Skill CLI: generate image / edit image / generate video via existing /ai-api/ai APIs."""

import argparse
import json
import mimetypes
import os
import sys
import time
import webbrowser
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_API = os.environ.get("PIAX_API_BASE", "https://piax-api.piax.org").rstrip("/")
CONNECT_PAGE = "https://www.piax.org/connect"
PRICING = "https://www.piax.org/pricing"
CREDITS = "https://www.piax.org/pricing/credits"
CREDENTIALS_FILE = os.path.expanduser(os.environ.get("PIAX_CREDENTIALS", "~/.piax/credentials.json"))
USER_AGENT = "piax-gen"
POLL_INTERVAL = 3
POLL_TIMEOUT = 600
LOGIN_HEARTBEAT = 15

# Homepage hub ids (pia-ui home imageModels / videoModels) minus chat redirects (27, 127)
# and Midjourney stills (4), which use a dedicated MJ flow.
IMAGE_MODELS = {
    "gpt-image-2.5": {
        "path": "/ai-api/ai/images/gptImage25TaskSubmit",
        "agentId": "211",
        "size": "pixel",
        "aliases": ["gpt-image-2.5", "gpt image 2.5", "gpt-image2.5", "gpt-image", "gpt image"],
        "default": True,
    },
    "agnes-image-2.1-flash": {
        "path": "/ai-api/ai/images/agnesImageTaskSubmit",
        "agentId": "205",
        "size": "ratio",
        "aliases": ["agnes-image", "agnes image", "agnes"],
        "image_size": "1K",
    },
    "muse-image": {
        "path": "/ai-api/ai/images/museImageTaskSubmit",
        "agentId": "204",
        "size": "ratio",
        "aliases": ["muse-image", "muse image", "muse"],
    },
    "grok-imagine-image-2.0": {
        "path": "/ai-api/ai/images/grokImagineImageTaskSubmit",
        "agentId": "198",
        "size": "ratio",
        "aliases": ["grok-imagine-image-2.0", "grok imagine 2", "grok image 2"],
        "family_default": True,
    },
    "qwen-image-3": {
        "path": "/ai-api/ai/images/qwenImageTaskSubmit",
        "agentId": "192",
        "size": "pixel",
        "aliases": ["qwen-image-3", "qwen image"],
    },
    "nano-banana-pro": {
        "path": "/ai-api/ai/images/geminiFlashImageTaskSubmit",
        "agentId": "117",
        "size": "ratio",
        "api_model": "gemini-3-pro-image",
        "aliases": ["nano-banana-pro", "nano banana pro", "banana pro", "gemini-3-pro-image"],
        "image_size": "1K",
    },
    "gpt-image2": {
        "path": "/ai-api/ai/images/gptImageTaskSubmit",
        "agentId": "181",
        "size": "pixel",
        "aliases": ["gpt-image2", "gpt-image-2", "gpt image 2"],
    },
    "nano-banana-2": {
        "path": "/ai-api/ai/images/geminiFlashImageTaskSubmit",
        "agentId": "142",
        "size": "ratio",
        "aliases": ["nano-banana-2", "nano banana 2", "nano banana", "banana"],
        "image_size": "1K",
        "family_default": True,
    },
    "nano-banana": {
        "path": "/ai-api/ai/images/geminiFlashImageTaskSubmit",
        "agentId": "91",
        "size": "ratio",
        "api_model": "gemini-2.5-flash-image",
        "aliases": ["nano-banana", "gemini-2.5-flash-image", "gemini flash image"],
    },
    "imagen": {
        "path": "/ai-api/ai/images/imagenTaskSubmit",
        "agentId": "73",
        "size": "imagen",
        "api_model": "imagen-4.0-ultra-generate-preview-06-06",
        "aliases": ["imagen", "imagen 4", "imagen-4"],
    },
    "dall-e-3": {
        "path": "/ai-api/ai/images/imageGenerationTaskSubmit",
        "agentId": "3",
        "size": "dalle",
        "api_model": "dall-e-3",
        "aliases": ["dall-e-3", "dalle", "dall e", "dall-e"],
    },
    "flux": {
        "path": "/ai-api/ai/flux/task/submit",
        "agentId": "2",
        "size": "flux",
        "api_model": "flux-2-pro",
        "aliases": ["flux", "flux 2", "flux 2 pro"],
    },
    "ideogram": {
        "path": "/ai-api/ai/ideogram/task/submit",
        "agentId": "25",
        "size": "ideogram",
        "aliases": ["ideogram", "ideogram 2"],
    },
    "grok-imagine-image": {
        "path": "/ai-api/ai/images/grokImagineImageTaskSubmit",
        "agentId": "135",
        "size": "ratio",
        "aliases": ["grok-imagine-image", "grok image"],
    },
    "z-image": {
        "path": "/ai-api/ai/images/z-imageTaskSubmit",
        "agentId": "133",
        "size": "pixel",
        "aliases": ["z-image", "z image"],
    },
    "seedream4.5": {
        "path": "/ai-api/ai/images/seedreamTaskSubmit",
        "agentId": "125",
        "size": "pixel",
        "aliases": ["seedream4.5", "seedream 4.5"],
    },
    "seedream5": {
        "path": "/ai-api/ai/images/seedreamTaskSubmit",
        "agentId": "155",
        "size": "pixel",
        "aliases": ["seedream5", "seedream 5", "seedream"],
        "family_default": True,
    },
    "wan2.7-pro": {
        "path": "/ai-api/ai/images/wanImageTaskSubmit",
        "agentId": "157",
        "size": "pixel",
        "aliases": ["wan2.7-pro", "wan 2.7 pro", "wan image"],
    },
}

VIDEO_MODELS = {
    "gemini-omni-flash-v1.1": {
        "path": "/ai-api/ai/gemini-omni-flash/task/submit",
        "agentId": "209",
        "aliases": ["gemini-omni-flash", "gemini omni", "omni flash"],
        "durations": [5, 8, 10],
        "resolutions": ["360p", "720p", "1080p", "4k"],
        "default_duration": 8,
        "default_resolution": "720p",
    },
    "agnes-video-2.5": {
        "path": "/ai-api/ai/agnes/video/task/submit",
        "agentId": "206",
        "aliases": ["agnes-video", "agnes video"],
        "durations": [5, 8, 10, 12],
        "resolutions": ["720P"],
        "default_duration": 5,
        "default_resolution": "720P",
        "video_style": "agnes",
    },
    "wan-3.0": {
        "path": "/ai-api/ai/wan/task/submit",
        "agentId": "202",
        "aliases": ["wan-3.0", "wan 3", "wan 3.0", "wan"],
        "family_default": True,
        "durations": [5, 10, 15, 20, 25, 30],
        "resolutions": ["480p", "720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
    "seedance-2.5": {
        "path": "/ai-api/ai/seedance/task/submit",
        "agentId": "195",
        "aliases": ["seedance-2.5", "seedance 2.5", "seedance"],
        "default": True,
        "durations": [5, 10, 15, 20],
        "resolutions": ["480p", "720p"],
        "default_duration": 5,
        "default_resolution": "480p",
    },
    "flux-3": {
        "path": "/ai-api/ai/flux-3/task/submit",
        "agentId": "191",
        "aliases": ["flux-3", "flux 3", "flux video"],
        "durations": [5, 8, 10, 15],
        "resolutions": ["720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
    "grok-imagine-video-1.5": {
        "path": "/ai-api/ai/grok-imagine-video/task/submit",
        "agentId": "190",
        "aliases": ["grok-imagine-video-1.5", "grok video 1.5", "grok video"],
        "family_default": True,
        "durations": [5, 8, 10],
        "resolutions": ["480p", "720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "480p",
    },
    "minimax-h3": {
        "path": "/ai-api/ai/minimax-h3/task/submit",
        "agentId": "189",
        "aliases": ["minimax-h3", "minimax h3", "minimax"],
        "durations": [5, 8, 12, 15],
        "resolutions": ["768p"],
        "default_duration": 5,
        "default_resolution": "768p",
    },
    "happy-horse-1.1": {
        "path": "/ai-api/ai/happy-horse/task/submit",
        "agentId": "179",
        "aliases": ["happy-horse-1.1", "happy horse", "happy-horse"],
        "family_default": True,
        "durations": [5, 10, 15],
        "resolutions": ["720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
    "wan-2.7": {
        "path": "/ai-api/ai/wan/task/submit",
        "agentId": "171",
        "aliases": ["wan-2.7", "wan 2.7"],
        "durations": [5, 10, 15],
        "resolutions": ["720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
    "veo3.1-fast": {
        "path": "/ai-api/ai/veo3/task/submit",
        "agentId": "104",
        "aliases": ["veo3.1-fast", "veo 3.1 fast", "veo"],
        "family_default": True,
        "durations": [4, 6, 8],
        "resolutions": ["720p", "1080p"],
        "default_duration": 4,
        "default_resolution": "720p",
    },
    "sora2": {
        "path": "/ai-api/ai/sora2/task/submit",
        "agentId": "114",
        "aliases": ["sora2", "sora"],
        "family_default": True,
        "durations": [4, 8, 12],
        "resolutions": ["720p"],
        "default_duration": 4,
        "default_resolution": "720p",
    },
    "sora2-pro": {
        "path": "/ai-api/ai/sora2/task/submit",
        "agentId": "115",
        "aliases": ["sora2-pro", "sora 2 pro", "sora pro"],
        "durations": [4, 8, 12],
        "resolutions": ["720p", "1080p"],
        "default_duration": 4,
        "default_resolution": "720p",
    },
    "veo3": {
        "path": "/ai-api/ai/veo3/task/submit",
        "agentId": "67",
        "aliases": ["veo3", "veo 3"],
        "durations": [8],
        "resolutions": ["720p", "1080p"],
        "default_duration": 8,
        "default_resolution": "720p",
    },
    "veo3.1": {
        "path": "/ai-api/ai/veo3/task/submit",
        "agentId": "103",
        "aliases": ["veo3.1", "veo 3.1"],
        "durations": [4, 6, 8],
        "resolutions": ["720p", "1080p"],
        "default_duration": 4,
        "default_resolution": "720p",
    },
    "midjourney-video": {
        "path": "/ai-api/ai/zeakai/mj/submit/video",
        "agentId": "74",
        "aliases": ["midjourney-video", "mj video", "midjourney video"],
        "durations": [5],
        "resolutions": ["720p"],
        "default_duration": 5,
        "default_resolution": "720p",
        "video_style": "mj",
        "requires_image": True,
    },
    "seedance-1-0-lite": {
        "path": "/ai-api/ai/seedance/task/submit",
        "agentId": "72",
        "aliases": ["seedance-1-0-lite", "seedance 1.0", "seedance lite"],
        "durations": [5, 10],
        "resolutions": ["480p", "720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "480p",
    },
    "vidu-q1": {
        "path": "/ai-api/ai/vidu/task/submit",
        "agentId": "71",
        "aliases": ["vidu-q1", "vidu"],
        "durations": [5],
        "resolutions": ["720p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
    "luma-ray-2-0": {
        "path": "/ai-api/ai/luma/task/submit",
        "agentId": "70",
        "aliases": ["luma-ray-2-0", "luma", "luma ray"],
        "durations": [5, 10],
        "resolutions": ["540p", "720p", "1080p", "4k"],
        "default_duration": 5,
        "default_resolution": "540p",
    },
    "runway-gen-4-turbo": {
        "path": "/ai-api/ai/runway/task/submit",
        "agentId": "69",
        "aliases": ["runway-gen-4-turbo", "runway", "runway gen 4"],
        "durations": [5, 10],
        "resolutions": ["720p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
    "kling": {
        "path": "/ai-api/ai/kling/task/submit",
        "agentId": "36",
        "aliases": ["kling"],
        "durations": [5, 10],
        "resolutions": ["720p"],
        "default_duration": 5,
        "default_resolution": "720p",
        "api_model": "V3.0-Std",
    },
    "wan-2.6": {
        "path": "/ai-api/ai/wan/task/submit",
        "agentId": "128",
        "aliases": ["wan-2.6", "wan 2.6"],
        "durations": [5, 10, 15],
        "resolutions": ["720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
    "seedance-1-5-pro": {
        "path": "/ai-api/ai/seedance/task/submit",
        "agentId": "156",
        "aliases": ["seedance-1-5-pro", "seedance 1.5"],
        "durations": [5, 10],
        "resolutions": ["480p", "720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "480p",
    },
    "grok-imagine-video": {
        "path": "/ai-api/ai/grok-imagine-video/task/submit",
        "agentId": "159",
        "aliases": ["grok-imagine-video", "grok imagine video"],
        "durations": [5, 8, 10],
        "resolutions": ["480p", "720p"],
        "default_duration": 5,
        "default_resolution": "480p",
    },
    "seedance-2-0": {
        "path": "/ai-api/ai/seedance/task/submit",
        "agentId": "158",
        "aliases": ["seedance-2-0", "seedance 2.0", "seedance 2"],
        "durations": [5, 8, 12, 15],
        "resolutions": ["720p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
    "happy-horse-1.0": {
        "path": "/ai-api/ai/happy-horse/task/submit",
        "agentId": "169",
        "aliases": ["happy-horse-1.0", "happy horse 1.0"],
        "durations": [5, 10, 15],
        "resolutions": ["720p", "1080p"],
        "default_duration": 5,
        "default_resolution": "720p",
    },
}

RATIO_TO_PIXEL = {
    "1:1": "1024x1024",
    "16:9": "1024x576",
    "9:16": "576x1024",
    "3:4": "768x1024",
    "4:3": "1024x768",
    "3:2": "1024x768",
    "2:3": "768x1024",
}


def eprint(message):
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def alternative_models(kind, slug):
    catalog = VIDEO_MODELS if kind == "video" else IMAGE_MODELS
    preferred = []
    rest = []
    for name, meta in catalog.items():
        if name == slug:
            continue
        if meta.get("default") or meta.get("family_default"):
            preferred.append(name)
        else:
            rest.append(name)
    return (preferred + rest)[:6]


def fail_generation(message, kind, slug, extra=None, exit_code=5):
    alts = alternative_models(kind, slug) if kind and slug else []
    ctx = dict(extra or {})
    if kind:
        ctx["kind"] = kind
    if slug:
        ctx["model"] = slug
    if alts:
        ctx["try_other_model"] = True
        ctx["alternatives"] = alts
        message = "%s Try another model: %s." % (message.rstrip("."), ", ".join(alts))
    fail("generation_failed", message, http=422, url="", cta="", extra=ctx, exit_code=exit_code)


def fail(code, message, http=401, url=CONNECT_PAGE, cta="Open", extra=None, exit_code=2):
    err = {
        "ok": False,
        "error": {
            "code": code,
            "http": http,
            "message": message,
            "action": {"cta": cta, "url": url},
        },
    }
    if extra:
        err["error"]["context"] = extra
    print(json.dumps(err, ensure_ascii=False))
    sys.exit(exit_code)


def load_credentials():
    if not os.path.isfile(CREDENTIALS_FILE):
        return {}
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_credentials(data):
    folder = os.path.dirname(CREDENTIALS_FILE)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    try:
        os.chmod(CREDENTIALS_FILE, 0o600)
    except Exception:
        pass


def load_api_key():
    env = os.environ.get("PIAX_API_KEY") or os.environ.get("PIA_API_KEY")
    if env:
        return env.strip()
    data = load_credentials()
    key = data.get("apiKey") or data.get("api_key") or data.get("token")
    return str(key).strip() if key else None


def save_login(token, display_name):
    data = load_credentials()
    data["apiKey"] = token
    data["displayName"] = display_name or ""
    data.pop("pending", None)
    save_credentials(data)


def save_pending(device_code, verification_url, expires_in):
    data = load_credentials()
    data["pending"] = {
        "deviceCode": device_code,
        "verificationUrl": verification_url,
        "expiresAt": int(time.time()) + int(expires_in),
        "interval": 2,
    }
    save_credentials(data)


def clear_pending():
    data = load_credentials()
    if "pending" in data:
        data.pop("pending", None)
        save_credentials(data)


def pending_login():
    pending = load_credentials().get("pending") or {}
    device = pending.get("deviceCode")
    url = pending.get("verificationUrl")
    expires_at = int(pending.get("expiresAt") or 0)
    if not device or not url or expires_at <= int(time.time()) + 5:
        return None
    return {
        "deviceCode": device,
        "verificationUrl": url,
        "expiresAt": expires_at,
        "interval": int(pending.get("interval") or 2),
    }


def open_browser(url):
    try:
        webbrowser.open(url)
    except Exception:
        pass


def whoami():
    key = load_api_key()
    if not key:
        return None
    payload = api_request("POST", "/ai-api/ai/auth/me", key, body={})
    if payload.get("code") not in (None, 1) or payload.get("errorCode") in ("auth_invalid", "auth_required"):
        return None
    return payload.get("displayName") or load_credentials().get("displayName") or ""


def cmd_who():
    name = whoami()
    if name is not None:
        print(json.dumps({"loggedIn": True, "displayName": name}, ensure_ascii=False, indent=2))
        return
    pending = pending_login()
    if pending:
        print(
            json.dumps(
                {
                    "loggedIn": False,
                    "status": "auth_pending",
                    "action": {"cta": "Sign in", "url": pending["verificationUrl"]},
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    print(json.dumps({"loggedIn": False}))


def cmd_logout():
    if os.path.isfile(CREDENTIALS_FILE):
        try:
            os.remove(CREDENTIALS_FILE)
        except Exception:
            pass
    print(json.dumps({"loggedIn": False}))


def emit_auth_pending(url, message):
    print(
        json.dumps(
            {
                "ok": False,
                "loggedIn": False,
                "status": "auth_pending",
                "error": {
                    "code": "auth_pending",
                    "http": 401,
                    "message": message,
                    "action": {"cta": "Sign in", "url": url},
                },
            },
            ensure_ascii=False,
        )
    )
    sys.exit(2)


def cmd_login():
    name = whoami()
    if name is not None:
        print(json.dumps({"loggedIn": True, "displayName": name}, ensure_ascii=False, indent=2))
        return

    pending = pending_login()
    if pending:
        url = pending["verificationUrl"]
        device = pending["deviceCode"]
        deadline = pending["expiresAt"]
        interval = pending["interval"]
        eprint("Continue signing in at: %s" % url)
        open_browser(url)
    else:
        payload = api_request("POST", "/ai-api/ai/auth/device", None, body={})
        if payload.get("code") not in (None, 1) or not payload.get("verificationUrl"):
            fail(
                "auth_required",
                payload.get("message") or "Could not start login.",
                http=401,
                url=CONNECT_PAGE,
                cta="Sign in",
                exit_code=2,
            )
        url = payload.get("verificationUrl")
        device = payload.get("deviceCode")
        expires = int(payload.get("expiresIn") or 600)
        interval = int(payload.get("interval") or 2)
        save_pending(device, url, expires)
        deadline = time.time() + expires
        eprint("Please sign in or register in the browser: %s" % url)
        open_browser(url)

    last_beat = 0
    while time.time() < deadline:
        now = time.time()
        if now - last_beat >= LOGIN_HEARTBEAT:
            eprint("Waiting for browser sign-in…")
            last_beat = now
        time.sleep(max(1, interval))
        polled = api_request("POST", "/ai-api/ai/auth/device/poll", None, body={"deviceCode": device})
        status = (polled.get("status") or "").lower()
        if status == "approved" and polled.get("token"):
            save_login(polled.get("token"), polled.get("displayName") or "")
            print(
                json.dumps(
                    {
                        "loggedIn": True,
                        "displayName": polled.get("displayName") or "",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        if status == "expired":
            clear_pending()
            fail(
                "auth_required",
                "Login expired. Run login again.",
                http=401,
                url=CONNECT_PAGE,
                cta="Sign in",
                exit_code=2,
            )
    emit_auth_pending(url, "Still waiting. Open the URL, finish signing in, then run login again.")


def resolve_model(kind, name):
    catalog = IMAGE_MODELS if kind in ("image", "image_edit") else VIDEO_MODELS
    if not name:
        for slug, meta in catalog.items():
            if meta.get("default"):
                return slug, meta
        slug = next(iter(catalog))
        return slug, catalog[slug]
    needle = name.strip().lower()
    if needle in catalog:
        return needle, catalog[needle]
    matches = []
    for slug, meta in catalog.items():
        aliases = [alias.lower() for alias in (meta.get("aliases") or [])] + [slug.lower()]
        for alias in aliases:
            if needle == alias:
                matches.append(slug)
                break
            if len(needle) >= 3 and (needle in alias or alias in needle):
                matches.append(slug)
                break
    uniq = list(dict.fromkeys(matches))
    if len(uniq) == 1:
        return uniq[0], catalog[uniq[0]]
    if len(uniq) > 1:
        for slug in uniq:
            if catalog[slug].get("default") or catalog[slug].get("family_default"):
                return slug, catalog[slug]
        fail(
            "generation_failed",
            "Ambiguous model %r. Choose one of: %s" % (name, ", ".join(uniq)),
            http=422,
            url="",
            cta="",
            exit_code=5,
        )
    fail(
        "generation_failed",
        "Unknown model %r. Run with --list --kind %s" % (name, "image" if kind != "video" else "video"),
        http=422,
        url="",
        cta="",
        exit_code=5,
    )


def api_request(method, path, key, body=None, files=None):
    url = DEFAULT_API + path
    headers = {
        "User-Agent": USER_AGENT,
        "X-PIAX-Channel": "skill",
        "Accept": "application/json",
    }
    if key:
        headers["Authorization"] = "Bearer " + key
    data = None
    if files:
        boundary = "----piaxskill%x" % int(time.time() * 1000)
        chunks = []
        for name, filepath in files:
            filename = os.path.basename(filepath)
            ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            with open(filepath, "rb") as f:
                content = f.read()
            chunks.append(
                ("--" + boundary + "\r\n").encode("utf-8")
                + ('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (name, filename)).encode("utf-8")
                + ("Content-Type: %s\r\n\r\n" % ctype).encode("utf-8")
                + content
                + b"\r\n"
            )
        chunks.append(("--" + boundary + "--\r\n").encode("utf-8"))
        data = b"".join(chunks)
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            return json.loads(raw) if raw else {"code": e.code, "message": str(e)}
        except Exception:
            return {"code": e.code, "message": raw or str(e)}
    except urllib.error.URLError as e:
        fail("generation_failed", "Network error: %s" % e.reason, http=500, url="", cta="", exit_code=5)


def map_api_error(payload, kind, model):
    if not payload:
        return
    code = payload.get("code")
    if code in (None, 1):
        return
    error_code = payload.get("errorCode")
    message = payload.get("message") or "Request failed"
    action_url = payload.get("actionUrl") or ""
    action_cta = payload.get("actionCta") or "Open"
    extra = {"kind": kind, "model": model}
    pending = pending_login()
    reconnect_url = (pending or {}).get("verificationUrl") or action_url or CONNECT_PAGE
    if error_code in ("auth_required", "auth_invalid") or code == 406:
        fail(
            error_code or "auth_required",
            message,
            http=401,
            url=reconnect_url,
            cta=action_cta or "Sign in",
            extra=extra,
            exit_code=2,
        )
    if error_code == "plan_required" or code == 401:
        fail(
            "plan_required",
            message,
            http=401,
            url=action_url or PRICING,
            cta=action_cta or "Upgrade",
            extra=extra,
            exit_code=3,
        )
    if error_code == "insufficient_credits" or code == 409:
        fail(
            "insufficient_credits",
            message,
            http=409,
            url=action_url or CREDITS,
            cta=action_cta or "Top up",
            extra=extra,
            exit_code=4,
        )
    fail_generation(message, kind, model, extra=extra)


def upload_local(key, path):
    payload = api_request("POST", "/ai-api/ai/storage/upload", key, files=[("files", path)])
    map_api_error(payload, "image", None)
    files = payload.get("files") or []
    if not files or not files[0].get("url"):
        fail("generation_failed", "Upload failed", http=422, url="", cta="", exit_code=5)
    return files[0]["url"]


def pixel_size(ratio):
    if not ratio:
        return "1024x1024"
    if "x" in ratio.lower():
        return ratio
    return RATIO_TO_PIXEL.get(ratio, "1024x1024")


def pick_allowed(value, allowed, fallback, label, model):
    if not allowed:
        return value if value is not None else fallback
    if value is None:
        if fallback in allowed:
            return fallback
        return allowed[0]
    if value in allowed:
        return value
    fail(
        "generation_failed",
        "%s %r is not supported by %s. Use one of: %s"
        % (label, value, model, ", ".join(str(item) for item in allowed)),
        http=422,
        url="",
        cta="",
        extra={"model": model},
        exit_code=5,
    )


def build_image_body(slug, meta, args, image_urls):
    style = meta.get("size") or "pixel"
    api_model = meta.get("api_model") or slug
    if style == "ideogram":
        ratio = args.ratio or "1:1"
        return {
            "productNo": "pia",
            "agentId": meta["agentId"],
            "image_request": {
                "aspect_ratio": "ASPECT_%s" % ratio.replace(":", "_"),
                "model": "V_2",
                "style_type": "AUTO",
                "negative_prompt": "",
                "prompt": args.prompt,
            },
        }
    body = {
        "productNo": "pia",
        "model": api_model,
        "agentId": meta["agentId"],
        "prompt": args.prompt,
        "n": 1,
    }
    if style == "pixel":
        body["imageSize"] = pixel_size(args.ratio)
    elif style in ("imagen", "dalle"):
        body["size"] = "1024x1024"
    elif style == "flux":
        px = pixel_size(args.ratio or "1:1")
        width, height = px.lower().split("x")
        body["width"] = int(width)
        body["height"] = int(height)
        body["aspect_ratio"] = args.ratio or "1:1"
        body["safety_tolerance"] = 2
        body["prompt_upsampling"] = False
    else:
        body["aspectRatio"] = args.ratio or "1:1"
        if meta.get("image_size"):
            body["imageSize"] = args.resolution or meta["image_size"]
            body["size"] = body["imageSize"]
    if image_urls:
        body["urls"] = image_urls
        if len(image_urls) == 1:
            body["url"] = image_urls[0]
    return body


def build_video_body(slug, meta, args, image_url):
    duration = pick_allowed(
        args.duration,
        meta.get("durations") or [],
        meta.get("default_duration") or 5,
        "duration",
        slug,
    )
    resolution = pick_allowed(
        args.resolution,
        meta.get("resolutions") or [],
        meta.get("default_resolution") or "720p",
        "resolution",
        slug,
    )
    aspect = args.ratio or "16:9"
    vtype = "image-to-video" if image_url else "text-to-video"
    api_model = meta.get("api_model") or slug
    style = meta.get("video_style") or "standard"
    if style == "mj":
        return {
            "productNo": "pia",
            "agentId": meta["agentId"],
            "type": "image-to-video",
            "motion": "High",
            "prompt": args.prompt,
            "imageUrl": image_url or "",
            "base64": "",
        }
    if style == "agnes":
        body = {
            "productNo": "pia",
            "model": api_model,
            "agentId": meta["agentId"],
            "prompt": args.prompt,
            "mode": "keyframe" if image_url else "text",
            "seconds": duration,
            "size": resolution,
            "aspectRatio": aspect,
        }
        if image_url:
            body["firstFrame"] = image_url
        return body
    body = {
        "productNo": "pia",
        "model": api_model,
        "agentId": meta["agentId"],
        "prompt": args.prompt,
        "type": vtype,
        "duration": duration,
        "length": duration,
        "seconds": duration,
        "resolution": resolution,
        "aspectRatio": aspect,
    }
    if image_url:
        body["imageUrl"] = image_url
    return body


def poll_task(key, task_id, kind, slug):
    deadline = time.time() + POLL_TIMEOUT
    started = time.time()
    last_beat = 0
    while time.time() < deadline:
        payload = api_request("POST", "/ai-api/ai/task/get", key, body={"taskId": str(task_id)})
        map_api_error(payload, kind, slug)
        task = payload.get("task") or {}
        status = (task.get("status") or "").lower()
        if status == "success":
            return task
        if status == "failed":
            reason = task.get("failedReason") or "generation failed"
            fail_generation(reason, kind, slug, extra={"task_id": task_id})
        now = time.time()
        if now - last_beat >= LOGIN_HEARTBEAT:
            eprint("Generating… task %s (%ds)" % (task_id, int(now - started)))
            last_beat = now
        time.sleep(POLL_INTERVAL)
    fail_generation("Timed out waiting for task %s" % task_id, kind, slug, extra={"task_id": task_id})


def download(url, out_path):
    folder = os.path.dirname(os.path.abspath(out_path))
    if folder:
        os.makedirs(folder, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp, open(out_path, "wb") as f:
        f.write(resp.read())


def default_out_path(kind):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    ext = "mp4" if kind == "video" else "png"
    return "./piax-%s-%s.%s" % (kind.replace("_", "-"), stamp, ext)


def list_models(kind):
    catalog = VIDEO_MODELS if kind == "video" else IMAGE_MODELS
    rows = []
    for slug, meta in catalog.items():
        row = {
            "slug": slug,
            "agentId": meta["agentId"],
            "default": bool(meta.get("default")),
            "aliases": meta.get("aliases", []),
        }
        if meta.get("durations"):
            row["durations"] = meta["durations"]
        if meta.get("resolutions"):
            row["resolutions"] = meta["resolutions"]
        rows.append(row)
    print(json.dumps({"ok": True, "kind": kind if kind == "video" else "image", "models": rows}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="PIAX generate")
    parser.add_argument("--who", action="store_true")
    parser.add_argument("--login", action="store_true")
    parser.add_argument("--logout", action="store_true")
    parser.add_argument("--kind", choices=["image", "image_edit", "video"])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--prompt")
    parser.add_argument("--model")
    parser.add_argument("--ratio")
    parser.add_argument("--resolution")
    parser.add_argument("--duration", type=int)
    parser.add_argument("--image", action="append", dest="images")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    kind = args.kind or "image"
    if args.who:
        cmd_who()
        return
    if args.logout:
        cmd_logout()
        return
    if args.login:
        cmd_login()
        return
    if args.list:
        list_models(kind)
        return

    if not args.prompt:
        fail("generation_failed", "prompt is required", http=422, url="", cta="", exit_code=5)

    slug, meta = resolve_model(kind, args.model)
    if kind == "image_edit" and not args.images:
        fail("generation_failed", "image_edit requires --image", http=422, url="", cta="", extra={"kind": kind}, exit_code=5)
    if meta.get("requires_image") and not args.images:
        fail_generation("This model needs a reference image. Pass --image or pick another model.", kind, slug)
    if kind == "video":
        build_video_body(slug, meta, args, None)

    key = load_api_key()
    if not key:
        pending = pending_login()
        fail(
            "auth_required",
            "Not signed in. Run login and complete it in the browser.",
            http=401,
            url=(pending or {}).get("verificationUrl") or CONNECT_PAGE,
            cta="Sign in",
            extra={"kind": kind},
            exit_code=2,
        )

    image_urls = []
    if args.images:
        for item in args.images:
            if item.startswith("http://") or item.startswith("https://"):
                image_urls.append(item)
            else:
                if not os.path.isfile(item):
                    fail("generation_failed", "Image not found: %s" % item, http=422, url="", cta="", exit_code=5)
                image_urls.append(upload_local(key, item))

    if kind == "video":
        body = build_video_body(slug, meta, args, image_urls[0] if image_urls else None)
    else:
        body = build_image_body(slug, meta, args, image_urls)
    out_path = args.out or default_out_path(kind)

    payload = api_request("POST", meta["path"], key, body=body)
    map_api_error(payload, kind, slug)
    task_id = payload.get("taskId")
    if not task_id:
        fail_generation("No taskId returned", kind, slug)

    eprint("Submitted %s task %s (%s)" % (kind, task_id, slug))
    task = poll_task(key, task_id, kind, slug)
    file_url = task.get("outputFileUrl") or ""
    if file_url:
        try:
            download(file_url, out_path)
        except Exception as e:
            fail_generation("Download failed: %s" % e, kind, slug, extra={"task_id": task_id})

    print(
        json.dumps(
            {
                "ok": True,
                "task_id": task_id,
                "kind": kind,
                "model": slug,
                "file": os.path.abspath(out_path),
                "file_url": file_url,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

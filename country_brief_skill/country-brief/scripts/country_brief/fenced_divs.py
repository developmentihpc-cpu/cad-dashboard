"""
fenced_divs.py — Dispatcher and renderers for all ::: components.

The public entry is render_fenced_divs(md). It walks the markdown text,
finds ::: class ... ::: blocks, and routes each to the appropriate
component renderer based on the class name.

Component renderers:
    render_verdict_strip
    render_risk_matrix
    render_snapshot
    render_faction_box
    render_severity_box
    render_stats_strip
    render_decision_implication
    render_leader_cards
    (charts and maps live in their own modules; this dispatcher imports them)
"""
import re
import sys
import os
import hashlib
import base64
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .charts import render_chart
from .maps import render_map
from .inline import _process_inline_markdown


# In-process cache for fetched leader photos so the same URL is fetched
# only once per render. Keyed by URL.
_LEADER_PHOTO_CACHE = {}

# Filesystem cache directory for leader photos — survives across renders.
# Honors XDG_CACHE_HOME on Linux/macOS; falls back to ~/.cache (which on
# Windows resolves under the user profile, e.g. C:\Users\<name>\.cache).
_LEADER_PHOTO_CACHE_DIR = Path(
    os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
) / "country-brief" / "photos"


# MIME type lookup by file extension. WeasyPrint embeds images via the
# data:URI, which needs the correct MIME type. Lowercase extension keys.
_PHOTO_MIME_BY_EXT = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".webp": "image/webp",
    ".gif":  "image/gif",
}

# Reverse map used by the auto-cache: when a photo is fetched successfully,
# we know its MIME type but not its original filename extension. Pick a
# canonical extension to write into the bundled directory.
_PHOTO_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png":  ".png",
    "image/webp": ".webp",
    "image/gif":  ".gif",
}

# Bundled leader-photo directory. Analysts can drop curated photos here
# under a deterministic slug derived from the leader's name (see
# _leader_slug). The renderer checks this directory before falling back
# to Wikipedia, so once a photo is curated it works for every future brief
# that references the same figure without needing an explicit URL in the
# markdown. This addresses the systematic gap where ambassadors and
# mid-tier officials have no Wikipedia coverage but do have official
# portraits hosted on foreign-ministry CMS pages with unstable URLs.
_PKG_ROOT_LEADERS = Path(__file__).resolve().parent.parent.parent / "assets" / "leaders"


# Honorific prefixes commonly attached to leader names in country briefs
# (especially in bilateral sections where ambassadors, ministers, and
# clerical / royal figures dominate). Wikipedia article URLs and bundled
# photo slugs are normalized without these prefixes, so the renderer must
# strip them before doing any name-based lookup. Order matters: longer /
# multi-word forms appear first so they match before their abbreviations.
_LEADER_HONORIFICS = [
    r"his\s+excellency",
    r"her\s+excellency",
    r"his\s+majesty",
    r"her\s+majesty",
    r"his\s+royal\s+highness",
    r"her\s+royal\s+highness",
    r"h\.?e\.?",
    r"h\.?r\.?h\.?",
    r"h\.?m\.?",
    r"professor",
    r"prof\.?",
    r"reverend",
    r"rev\.?",
    r"honou?rable",
    r"hon\.?",
    r"senator",
    r"sen\.?",
    r"president",
    r"pres\.?",
    r"minister",
    r"ambassador",
    r"general",
    r"gen\.?",
    r"colonel",
    r"col\.?",
    r"major",
    r"maj\.?",
    r"captain",
    r"capt\.?",
    r"admiral",
    r"adm\.?",
    r"ayatollah",
    r"sheikh",
    r"shaikh",
    r"imam",
    r"rabbi",
    r"father",
    r"fr\.?",
    r"pastor",
    r"dr\.?",
    r"mr\.?",
    r"mrs\.?",
    r"ms\.?",
    r"sir",
    r"lady",
    r"dame",
]


def _strip_honorific(name: str) -> str:
    """Strip leading honorifics from a name so Wikipedia/slug lookups work.

    The display name on the card is preserved unchanged; this function only
    affects lookups. Iterates to handle stacked titles like "H.R.H. Sheikh
    Mohamed bin Zayed" or "Dr. Hon. Smith". Returns the original string if
    no honorifics match.
    """
    if not name:
        return name
    import re as _re_h
    pattern = _re_h.compile(
        r"^\s*(?:" + "|".join(_LEADER_HONORIFICS) + r")\s+",
        _re_h.IGNORECASE,
    )
    prev = None
    cleaned = name
    while prev != cleaned:
        prev = cleaned
        cleaned = pattern.sub("", cleaned)
    return cleaned.strip()


# Arabic-name → English-slug mapping for the photo cascade. When an Arabic
# brief writes a leader-card with an Arabic name field, the standard NFKD
# normalization strips all Arabic characters and produces an empty slug,
# breaking the bundled-photo lookup even when a photo for the same figure
# exists under the English slug. This map bridges the gap.
#
# Keys are the Arabic full name AFTER honorific stripping (matching what
# _leader_slug() would see post-strip). Values are the English slug under
# which the photo is stored in assets/leaders/.
#
# Add new entries when an Arabic brief surfaces a new figure with a bundled
# photo. Keep this in sync with references/arabic-names.md.
_ARABIC_LEADER_SLUGS = {
    # Iran
    "علي خامنئي":              "ali-khamenei",
    "مجتبى خامنئي":            "mojtaba-khamenei",
    "مسعود بزشكيان":           "masoud-pezeshkian",
    "محمد باقر قاليباف":        "mohammad-bagher-ghalibaf",
    "أحمد وحيدي":              "ahmad-vahidi",
    "عباس عراقجي":             "abbas-araghchi",
    "علي لاريجاني":            "ali-larijani",
    "محمد إسلامي":             "mohammad-eslami",
    "عليرضا أعرافي":           "alireza-arafi",
    # UAE — used for bilateral leader-cards across briefs
    "محمد بن زايد آل نهيان":    "mohamed-bin-zayed",
    "عبدالله بن زايد آل نهيان": "abdullah-bin-zayed",
    "طحنون بن زايد آل نهيان":   "tahnoon-bin-zayed",
    # Sri Lanka
    "أنورا كومارا ديساناياكي":  "anura-kumara-dissanayake",
}


def _leader_slug(name: str) -> str:
    """Convert a leader name to a deterministic filesystem slug.

    The slug is the basename (without extension) the renderer looks up in
    assets/leaders/. Rules: strip honorifics first ("Dr.", "Sheikh", "Hon.",
    etc.), then lowercase, ASCII, hyphens between tokens, strip in-name
    punctuation. Name particles ("bin", "al", "de", "van") are preserved
    (unlike the monogram helper) because they're part of the canonical
    identifier.

    Arabic-name inputs short-circuit through _ARABIC_LEADER_SLUGS first —
    NFKD normalization would otherwise strip Arabic characters entirely
    and produce an empty slug, breaking bundled-photo lookups for figures
    that ARE cached under their English slugs.

    Examples:
        "Azali Assoumani"                       -> "azali-assoumani"
        "Nour El Fath Azali"                    -> "nour-el-fath-azali"
        "Sheikh Mohamed bin Zayed"              -> "mohamed-bin-zayed"
        "Dr. Thani bin Ahmed Al Zeyoudi"        -> "thani-bin-ahmed-al-zeyoudi"
        "Houmed M'saidie"                       -> "houmed-msaidie"
        "H.E. Jumaa Rashed Al Remeithi"         -> "jumaa-rashed-al-remeithi"
        "أحمد وحيدي"                            -> "ahmad-vahidi" (via map)
        "الشيخ محمد بن زايد آل نهيان"             -> "mohamed-bin-zayed" (strip + map)
    """
    import unicodedata
    if not name:
        return ""
    # Strip leading honorifics first so they don't end up in the slug.
    name = _strip_honorific(name)
    # Arabic short-circuit: if the stripped name is in the Arabic→slug map,
    # return the mapped English slug. The map covers figures with bundled
    # photos; analysts add entries when new Arabic-named figures need photos.
    if name in _ARABIC_LEADER_SLUGS:
        return _ARABIC_LEADER_SLUGS[name]
    # Normalize unicode (NFKD) and drop combining marks so accented chars
    # map to their ASCII base (é -> e, ḷ -> l, etc.).
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower()
    # Strip intra-token punctuation (apostrophes, periods in initials,
    # Arabic-style ʿʾ remnants) BEFORE tokenizing, so names like "M'saidié"
    # and "O'Brien" collapse to "msaidie" / "obrien" rather than splitting
    # on the apostrophe.
    import re as _re_slug
    ascii_only = _re_slug.sub(r"['’ʼ.]", "", ascii_only)
    # Replace remaining runs of non-alphanumeric with a single hyphen; trim.
    slug = _re_slug.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug


def _maybe_cache_to_bundled(name: str, photo_data) -> None:
    """Auto-cache a successfully-fetched photo into assets/leaders/{slug}.{ext}.

    Triggered after any successful photo resolution (explicit URL,
    Wikipedia hit, etc.) so that the next brief mentioning the same figure
    can hit the bundled directory directly without re-fetching. This makes
    the analyst's one-time effort to provide an official-source URL pay
    forward across every future brief that names the same person.

    Honors analyst curation: if a file already exists at the target slug
    (any extension), this function is a no-op. Analyst-curated photos win
    over auto-cached ones.

    Failures are logged but never raised — auto-caching is best-effort and
    must not break a render.
    """
    if not photo_data:
        return
    mime, b64 = photo_data
    ext = _PHOTO_EXT_BY_MIME.get(mime)
    if not ext:
        return
    slug = _leader_slug(name)
    if not slug:
        return
    # If any bundled photo already exists for this slug, don't overwrite.
    # This preserves analyst-curated photos against auto-cache.
    if _lookup_bundled_leader_photo(name) is not None:
        return
    try:
        _PKG_ROOT_LEADERS.mkdir(parents=True, exist_ok=True)
        target = _PKG_ROOT_LEADERS / f"{slug}{ext}"
        target.write_bytes(base64.b64decode(b64))
        print(
            f"Leader-cards note: auto-cached portrait for {name!r} to "
            f"{target.name} (future briefs will use the bundled copy)",
            file=sys.stderr,
        )
    except Exception as e:
        # Cache write failed; not fatal — the brief still renders with the
        # in-memory photo.
        print(
            f"Leader-cards note: auto-cache write failed for {name!r} "
            f"({type(e).__name__}: {e})",
            file=sys.stderr,
        )


def _lookup_bundled_leader_photo(name: str):
    """Look for a curated photo at assets/leaders/{slug}.{ext}.

    Returns (mime, base64) on hit, None on miss. Tries each supported
    extension (.jpg, .jpeg, .png, .webp, .gif) in order. The directory is
    versioned with the skill; analysts can add new figures by dropping
    files in.
    """
    slug = _leader_slug(name)
    if not slug:
        return None
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        candidate = _PKG_ROOT_LEADERS / f"{slug}{ext}"
        if candidate.exists() and candidate.is_file():
            return _load_local_photo(str(candidate))
    return None


def _load_local_photo(path_str: str):
    """
    Load a photo from a local filesystem path and return (mime, base64).
    Returns None if the path doesn't exist, isn't readable, or doesn't
    have a recognized image extension.

    The path can be absolute or relative; relative paths are resolved
    against the current working directory (typically wherever the
    renderer was invoked).
    """
    p = Path(path_str).expanduser()
    if not p.is_absolute():
        # Resolve relative to cwd, which is typically where the brief
        # markdown lives when an analyst runs `python render_brief.py`.
        p = Path.cwd() / p

    if not p.exists() or not p.is_file():
        print(
            f"Leader-cards note: local photo not found at '{p}' — "
            f"falling back to monogram placeholder.",
            file=sys.stderr,
        )
        return None

    ext = p.suffix.lower()
    mime = _PHOTO_MIME_BY_EXT.get(ext)
    if not mime:
        print(
            f"Leader-cards note: unrecognized image extension '{ext}' at '{p}' "
            f"(supported: .jpg, .jpeg, .png, .webp, .gif) — "
            f"falling back to monogram placeholder.",
            file=sys.stderr,
        )
        return None

    try:
        data = p.read_bytes()
    except Exception as e:
        print(
            f"Leader-cards note: failed to read local photo '{p}' "
            f"({type(e).__name__}: {e}) — falling back to monogram placeholder.",
            file=sys.stderr,
        )
        return None

    b64 = base64.b64encode(data).decode("ascii")
    return (mime, b64)


def _fetch_leader_photo(source: str, timeout: float = 5.0):
    """
    Resolve a photo source string to (mime_type, base64_data), or None on
    any failure. Source string can take four forms:

      1. wiki:Name with Spaces       — looks up Wikipedia REST API summary
                                       for the page and uses the canonical
                                       thumbnail URL it returns. The hash
                                       prefix in the Wikimedia URL comes
                                       from the API, not inference — this
                                       is the reliable way to get a working
                                       photo URL for any public figure who
                                       has a Wikipedia article.

      2. commons:Filename.jpg        — uses Wikimedia Special:FilePath to
                                       redirect to the canonical hashed
                                       Commons URL. Useful when you know
                                       the filename but not the hash.

      3. https://... or http://...   — explicit URL, fetched directly.

      4. /absolute/path  or          — local file, read from disk. Always
         relative/path                 works regardless of network access.

      5. Empty string                — returns None; caller renders the
                                       monogram placeholder.

    Why multiple source types: URL-based photo fetching has historically
    failed because Wikimedia thumbnail URLs require an MD5-hash prefix
    derived from the filename, which can't be reliably inferred. The
    `wiki:` and `commons:` prefixes route through APIs that produce the
    correct URL programmatically. This is the difference between guessing
    and looking up.

    All successful fetches are cached:
      1. In-process dict cache (per-render fast path)
      2. Filesystem cache under $XDG_CACHE_HOME/country-brief/photos/ or
         ~/.cache/country-brief/photos/ (persistent across renders, keyed
         by SHA1 of the canonical URL).

    Errors are logged to stderr with diagnostic detail but never raised —
    a broken photo source must never break the brief render. The caller
    falls back to a monogram placeholder.
    """
    if not source:
        return None
    source = source.strip()
    if not source:
        return None

    # --- Route by prefix ---
    if source.startswith("wiki:"):
        title = source[len("wiki:"):].strip()
        return _resolve_wikipedia_photo(title, timeout=timeout)
    # Language-specific Wikipedia lookup: wiki-fr:Name, wiki-es:Name, etc.
    # The two-letter code after "wiki-" is the Wikipedia language subdomain
    # (en, fr, es, de, ar, ru, pt, ja, zh, ...). Useful for figures who only
    # have non-English Wikipedia articles — Francophone African leaders are
    # the canonical case (Comoros, Senegal, Côte d'Ivoire, etc.).
    import re as _re_local
    lang_match = _re_local.match(r"^wiki-([a-z]{2,3}):(.*)$", source)
    if lang_match:
        lang = lang_match.group(1)
        title = lang_match.group(2).strip()
        return _resolve_wikipedia_photo(title, lang=lang, timeout=timeout)
    if source.startswith("commons:"):
        filename = source[len("commons:"):].strip()
        return _resolve_commons_photo(filename, timeout=timeout)
    if source.startswith(("http://", "https://")):
        return _fetch_url_photo(source, timeout=timeout)
    # Default: treat as local file path
    return _load_local_photo(source)


def _resolve_wikipedia_photo(title: str, lang: str = "en", timeout: float = 5.0):
    """
    Look up a Wikipedia page summary and use the returned thumbnail URL.

    The Wikipedia REST API endpoint
    `https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}` returns
    JSON including a `thumbnail.source` field, which is the canonical
    Wikimedia URL with the correct MD5-hash prefix. We use it directly.

    For higher-resolution photos, the API also returns `originalimage.source`
    which is the un-thumbnailed file. We prefer this when available because
    thumbnails are often only 200-320px wide — fine for tiny avatars, but
    a country brief renders cards at 4.5cm (~170px @ 96dpi or ~510px @
    300dpi), so we want at least 500px for crisp PDF rendering.

    The `lang` parameter selects the Wikipedia language edition (en, fr,
    ar, etc.). Defaults to English; callers can pass other codes for
    figures who only have non-English Wikipedia articles.
    """
    import urllib.parse
    if not title:
        return None
    api_url = (
        f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
        + urllib.parse.quote(title.replace(" ", "_"))
    )

    # Cache the resolved photo URL by the input title + lang to avoid hitting
    # the summary API twice for the same person across renders.
    title_cache_key = f"wiki-title:{lang}:{title}"
    if title_cache_key in _LEADER_PHOTO_CACHE:
        return _LEADER_PHOTO_CACHE[title_cache_key]

    try:
        import urllib.request
        import json as json_mod
        req = urllib.request.Request(
            api_url,
            headers={
                # Wikimedia's UA policy requires a meaningful, identifying
                # user-agent. Generic UAs sometimes get rate-limited or
                # 403'd. This identifies the tool and provides a contact.
                "User-Agent": (
                    "country-brief-renderer/1.0 "
                    "(https://github.com/anthropics/skills; analytical-briefs) "
                    "Python-urllib"
                ),
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json_mod.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(
            f"Leader-cards note: {lang}.wikipedia.org lookup for '{title}' failed "
            f"({type(e).__name__}: {e}).",
            file=sys.stderr,
        )
        result = None
        _LEADER_PHOTO_CACHE[title_cache_key] = result
        return result

    # Prefer originalimage (high-res) over thumbnail (typically 200-320px)
    photo_url = None
    if isinstance(payload.get("originalimage"), dict):
        photo_url = payload["originalimage"].get("source")
    if not photo_url and isinstance(payload.get("thumbnail"), dict):
        photo_url = payload["thumbnail"].get("source")

    if not photo_url:
        print(
            f"Leader-cards note: {lang}.wikipedia.org page '{title}' exists "
            f"but has no photo (the page may be a stub or about a topic "
            f"without an infobox image).",
            file=sys.stderr,
        )
        result = None
        _LEADER_PHOTO_CACHE[title_cache_key] = result
        return result

    # Found a URL — delegate to the URL fetcher and cache under both keys
    result = _fetch_url_photo(photo_url, timeout=timeout)
    _LEADER_PHOTO_CACHE[title_cache_key] = result
    return result


def _resolve_commons_photo(filename: str, timeout: float = 5.0):
    """
    Resolve a Wikimedia Commons filename to a working photo URL via
    Special:FilePath, which redirects to the canonical hashed URL.

    Useful when you know the exact filename but can't guess the hash
    prefix. For example, given
        commons:President_of_Sri_Lanka_Mr._Anura_Kumara_Dissanayake.jpg
    we fetch
        https://commons.wikimedia.org/wiki/Special:FilePath/<filename>
    which Wikimedia redirects to the actual hashed URL.

    The redirect is handled automatically by urllib. No hash inference.
    """
    if not filename:
        return None
    import urllib.parse
    # Strip "File:" prefix if present
    if filename.startswith("File:"):
        filename = filename[5:]
    url = (
        "https://commons.wikimedia.org/wiki/Special:FilePath/"
        + urllib.parse.quote(filename.replace(" ", "_"))
    )
    return _fetch_url_photo(url, timeout=timeout)


def _fetch_url_photo(url: str, timeout: float = 5.0):
    """
    Fetch a photo from an HTTP/HTTPS URL and return (mime, base64).
    Returns None on any failure. Uses both an in-process cache and a
    persistent filesystem cache so repeated renders don't re-fetch.
    """
    # Process-level cache
    if url in _LEADER_PHOTO_CACHE:
        return _LEADER_PHOTO_CACHE[url]

    # Filesystem cache
    _LEADER_PHOTO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    cache_path = _LEADER_PHOTO_CACHE_DIR / f"{url_hash}.bin"
    cache_meta = _LEADER_PHOTO_CACHE_DIR / f"{url_hash}.mime"

    if cache_path.exists() and cache_meta.exists():
        try:
            mime = cache_meta.read_text().strip()
            data = cache_path.read_bytes()
            b64 = base64.b64encode(data).decode("ascii")
            result = (mime, b64)
            _LEADER_PHOTO_CACHE[url] = result
            return result
        except Exception:
            pass  # Cache read failed; fall through to fetch

    # Fetch from network
    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(
            url,
            headers={
                # Wikimedia and many other sites require an identifying UA.
                # Generic UAs like "Python-urllib/3.x" or "Mozilla/5.0" alone
                # get rate-limited or 403'd. This UA identifies the tool,
                # provides a contact URL, and includes Python-urllib for
                # transparency.
                "User-Agent": (
                    "country-brief-renderer/1.0 "
                    "(https://github.com/anthropics/skills; analytical-briefs) "
                    "Python-urllib"
                ),
                "Accept": "image/*,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            # Strip charset suffix if present
            mime = content_type.split(";")[0].strip()
            if not mime.startswith("image/"):
                print(
                    f"Leader-cards note: URL did not return an image "
                    f"(content-type={mime}): {url[:80]}",
                    file=sys.stderr,
                )
                return None
            data = resp.read()
    except Exception as e:
        print(
            f"Leader-cards note: photo fetch failed ({type(e).__name__}): "
            f"{url[:80]} — falling back to monogram placeholder.",
            file=sys.stderr,
        )
        return None

    # Write to filesystem cache
    try:
        cache_path.write_bytes(data)
        cache_meta.write_text(mime)
    except Exception:
        pass  # Cache write failed; not fatal

    b64 = base64.b64encode(data).decode("ascii")
    result = (mime, b64)
    _LEADER_PHOTO_CACHE[url] = result
    return result


def _leader_monogram(name: str) -> str:
    """
    Compute a 1-3 character monogram from a person's name for the photo
    placeholder. Uses initials of up to 3 name parts.

    Examples:
      "Anura Kumara Dissanayake" → "AKD"
      "Harini Amarasuriya" → "HA"
      "Sheikh Mohamed bin Zayed Al Nahyan" → "SMZ"  (skips lowercase particles)
    """
    if not name:
        return "?"
    # Skip lowercase particles ("bin", "al", "de", "van", "von", "el")
    particles = {"bin", "al", "de", "del", "van", "von", "el", "la", "le", "da"}
    parts = [p for p in name.split() if p.lower() not in particles]
    if not parts:
        return name[0].upper()
    initials = [p[0].upper() for p in parts[:3] if p and p[0].isalpha()]
    return "".join(initials) or "?"


def _leader_color_from_name(name: str) -> str:
    """
    Compute a deterministic CSS color for a monogram placeholder, derived
    from the name. Used so each placeholder has a distinct (but consistent
    across renders) background color, avoiding a wall of identical gray.

    Returns a hex color string from a curated palette of muted, professional
    tones that look acceptable in a country brief context.
    """
    # Curated palette — muted, professional, no neon. Selected so every
    # color works as a background for white monogram text.
    palette = [
        "#3B5266",  # slate blue
        "#5B6B7C",  # cool gray
        "#7A6C5D",  # warm taupe
        "#5C7459",  # sage
        "#8B6F47",  # tobacco
        "#6B5876",  # mauve
        "#4F6D7A",  # ocean
        "#7D7461",  # khaki
    ]
    if not name:
        return palette[0]
    h = hashlib.sha1(name.encode("utf-8")).digest()[0]
    return palette[h % len(palette)]


def render_leader_cards(inner: str) -> str:
    """
    Render a grid of leader/counterpart cards with photos (or stylized
    initial-letter placeholders when photo is unavailable).

    Use cases:
      - Country political leadership (Section 2): heads of state, PM,
        opposition leader, key faction leaders.
      - Bilateral counterparts (Section 1.5): home-country side + host-
        country side leadership and ambassadors.
      - Project counterparts (Section 7): named signing principals or
        lead negotiators for a specific development project.

    Markdown syntax:
        ::: leader-cards
        title: Sri Lankan political leadership (May 2026)

        - Anura Kumara Dissanayake | President since Sept 2024 | NPP/JVP | https://...
        - Harini Amarasuriya | Prime Minister since Sept 2024 | NPP |
        - Sajith Premadasa | Leader of Opposition | SJB |
        :::

    Pipe-separated fields per row: name | role | affiliation | photo_url
    The photo_url field is optional — blank or missing falls back to a
    stylized monogram placeholder using the name's initials.

    The title line is optional; defaults to "Key leaders" if omitted.

    Cards render in a flex-wrap grid: typically 3 per row at brief width,
    wrapping to 2 or 1 on narrower output. Each card has a square photo
    (or placeholder), name in bold below, role in medium, affiliation in
    smaller italic. Consistent with the brief's typography.
    """
    # Phase 1: parse. Extract title + structured row dicts. No I/O.
    parsed_rows = []
    title = "Key leaders"
    for raw_line in inner.strip().splitlines():
        line = raw_line.strip()
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
            continue
        if not line.startswith("-"):
            continue
        body = line.lstrip("-").strip()
        parts = [p.strip() for p in body.split("|")]
        if len(parts) < 2:
            continue
        while len(parts) < 4:
            parts.append("")
        parsed_rows.append({
            "name":        parts[0],
            "role":        parts[1],
            "affiliation": parts[2],
            "photo_url":   parts[3],
        })

    if not parsed_rows:
        return ""

    # Phase 2: resolve photos in parallel. Each row's photo cascade is
    # independent and I/O-bound (network or filesystem), so a small thread
    # pool gives a substantial speedup when photos aren't yet bundle-cached.
    # The cascade itself is unchanged (explicit URL → bundled directory →
    # en/fr/ar Wikipedia → None).
    #
    # Auto-caching is deliberately deferred to Phase 3 (sequential) to
    # avoid filesystem races on the rare case where two rows resolve to
    # the same bundled slug — sequential writes are safe and predictable.
    def _resolve_one(row):
        name = row["name"]
        photo_url = row["photo_url"]
        source_is_network = False
        if photo_url:
            photo_data = _fetch_leader_photo(photo_url)
            source_is_network = photo_url.strip().startswith(
                ("http://", "https://", "wiki:", "wiki-", "commons:")
            )
        else:
            lookup_name = _strip_honorific(name)
            photo_data = _lookup_bundled_leader_photo(lookup_name)
            if not photo_data:
                for fallback_lang in ("en", "fr", "ar"):
                    photo_data = _fetch_leader_photo(
                        f"wiki-{fallback_lang}:{lookup_name}"
                    )
                    if photo_data:
                        source_is_network = True
                        break
        return photo_data, source_is_network

    max_workers = min(8, len(parsed_rows))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        photo_results = list(ex.map(_resolve_one, parsed_rows))

    # Phase 3: auto-cache successful network fetches (sequential, no races)
    # and build HTML.
    rows = []
    for row, (photo_data, source_is_network) in zip(parsed_rows, photo_results):
        name = row["name"]
        role = row["role"]
        affiliation = row["affiliation"]

        if photo_data and source_is_network:
            _maybe_cache_to_bundled(_strip_honorific(name), photo_data)

        if photo_data:
            mime, b64 = photo_data
            photo_html = (
                f'<div class="leader-photo">'
                f'<img src="data:{mime};base64,{b64}" alt="{name}" />'
                f'</div>'
            )
        else:
            monogram = _leader_monogram(name)
            bg_color = _leader_color_from_name(name)
            photo_html = (
                f'<div class="leader-photo leader-photo-placeholder" '
                f'style="background-color: {bg_color};">'
                f'<span class="leader-monogram">{monogram}</span>'
                f'</div>'
            )

        affiliation_html = (
            f'<div class="leader-affiliation">{affiliation}</div>'
            if affiliation else ''
        )

        rows.append(
            '<div class="leader-card">'
            + photo_html
            + '<div class="leader-card-text">'
            + f'<div class="leader-name">{name}</div>'
            + f'<div class="leader-role">{role}</div>'
            + affiliation_html
            + '</div>'
            + '</div>'
        )

    if not rows:
        return ""

    return (
        '<div class="leader-cards-container">'
        f'<div class="leader-cards-title">{title}</div>'
        '<div class="leader-cards-grid">'
        + "".join(rows)
        + '</div>'
        '</div>'
    )


def render_decision_implication(inner: str) -> str:
    """
    Render a decision-implication callout block.

    Used at the end of each section (spine sections 1-6 and optional modules)
    to give the reader an explicit "so what for the portfolio" callout that
    stands out from the surrounding prose.

    Markdown syntax:
        ::: decision-implication
        Your decision-implication text here. Can span multiple paragraphs.
        Supports normal markdown formatting including **bold** and *italic*.
        :::

    Renders as a styled block with a navy left-border, light tint background,
    and a "Decision implication" header. The header is fixed by design — every
    block uses the same label so the brief's visual vocabulary stays consistent
    (similar to how all stats-strips look the same).
    """
    # Since render_fenced_divs runs BEFORE markdown processing, we need to
    # handle inline markdown ourselves for content inside the callout:
    # bold (**text** -> <strong>), italic (*text* -> <em>), and footnote refs.
    # Footnote refs are left as-is and processed later by render_footnote_refs.
    body_md = inner.strip()

    # Inline markdown processing happens via the shared module-level helper
    # `_process_inline_markdown` (bold and italic). Same fix applies in the
    # default fenced-div case so scenario/key-judgment/etc. blocks also
    # support inline formatting.

    # Convert paragraphs (blank-line separated)
    paragraphs = re.split(r"\n\s*\n", body_md)
    body_html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        body_html_parts.append(f"<p>{_process_inline_markdown(para)}</p>")
    body_html = "".join(body_html_parts)

    # Detect Arabic content to switch the header label. Same heuristic as
    # the scoring-summary header: if the body contains Arabic characters,
    # use the Arabic header; otherwise use the English header. This avoids
    # forcing the analyst to specify language explicitly while preserving
    # backward compatibility for English briefs.
    body_has_arabic = any(
        "\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F"
        for ch in body_md
    )
    header_label = "التداعيات على القرار" if body_has_arabic else "Decision implication"

    return (
        '<div class="decision-implication">'
        f'<div class="decision-implication-header">{header_label}</div>'
        f'<div class="decision-implication-body">{body_html}</div>'
        '</div>'
    )


def render_delta_summary(inner: str) -> str:
    """
    Render a "what's changed since last brief" summary. Useful for repeat
    readers maintaining country watch lists who need to triage which sections
    are most worth re-reading.

    Input format: bullet list, one item per change, with optional directional
    arrow at start (↑ ↓ → ⇅) followed by category label, colon, and description.

    Example:
        ::: delta-summary
        title: Changes since prior brief (May 2026)
        - ↓ Coalition stability: Both Deputy PMs resigned after FICAC charges
        - → Macro: IMF Article IV maintained 2.5% growth projection
        - ↑ Security: Vuvale Union signed with Australia (May 8, 2026)
        - → Climate finance: UAE bilateral engagement continues at pace
        :::

    Renders as a styled block with the title as a section header and each
    delta as a row with arrow + bold label + description.
    """
    title = "Changes since prior brief"
    rows = []
    for raw_line in inner.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Title line: "title: ..."
        m_title = re.match(r"^title:\s*(.+)$", line, re.IGNORECASE)
        if m_title:
            title = m_title.group(1).strip()
            continue
        # Delta line: "- [arrow] Category: description"
        if not line.startswith("-"):
            continue
        body = line.lstrip("-").strip()
        # Optional leading arrow
        arrow = ""
        for arrow_candidate in ("↑", "↓", "→", "⇅"):
            if body.startswith(arrow_candidate):
                arrow = arrow_candidate
                body = body[len(arrow_candidate):].strip()
                break
        # Split "Category: description"
        if ":" in body:
            label, _, desc = body.partition(":")
            label = label.strip()
            desc = desc.strip()
        else:
            label = ""
            desc = body
        # Map arrow to color
        arrow_color = {"↑": "#16a34a", "↓": "#dc2626", "→": "#6b7280", "⇅": "#d97706"}.get(arrow, "#6b7280")
        rows.append((arrow, arrow_color, label, desc))

    if not rows:
        return '<div class="delta-summary"></div>'

    row_html = []
    for arrow, color, label, desc in rows:
        arrow_part = f'<span class="delta-arrow" style="color: {color};">{arrow}</span>' if arrow else ""
        label_part = f'<strong>{label}:</strong> ' if label else ""
        row_html.append(
            f'<div class="delta-row">{arrow_part}<span class="delta-text">{label_part}{_process_inline_markdown(desc)}</span></div>'
        )

    return (
        f'<div class="delta-summary">'
        f'<div class="delta-summary-title">{title}</div>'
        + "".join(row_html)
        + '</div>'
    )


def render_scoring_summary(inner: str) -> str:
    """
    Render a quantitative scoring table across standard portfolio-decision
    dimensions. Bridges the qualitative prose of the brief to quantitative
    portfolio decision models.

    Input format: bullet list, one row per dimension:
        - Dimension | score 0-100 | trend arrow | one-line justification

    Example:
        ::: scoring-summary
        title: Portfolio decision-relevance scoring (May 2026)
        - Macro stability | 55 | → | Tourism deceleration; fiscal pressure; debt 80% GDP
        - Political risk | 60 | ↓ | Coalition fraying; election uncertainty 2026-27
        - Sanctions exposure | 95 | → | No sanctions; clean compliance profile
        - Climate risk | 25 | ↓ | High vulnerability; 1.8% GDP annual SLR losses
        - ESG framework | 70 | → | Strong climate institutional architecture
        - Operational risk | 65 | → | Small market; labor shortages; capacity constraints
        :::

    Score interpretation:
    - 0-30: high risk / unfavorable
    - 30-60: moderate / mixed
    - 60-80: favorable
    - 80-100: strongly favorable
    """
    title = "Portfolio decision-relevance scoring"
    rows = []
    for raw_line in inner.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m_title = re.match(r"^title:\s*(.+)$", line, re.IGNORECASE)
        if m_title:
            title = m_title.group(1).strip()
            continue
        if not line.startswith("-"):
            continue
        body = line.lstrip("-").strip()
        parts = [p.strip() for p in body.split("|")]
        if len(parts) < 4:
            continue
        dimension = parts[0]
        try:
            score = int(parts[1])
        except ValueError:
            continue
        trend = parts[2]
        justification = " | ".join(parts[3:])  # rejoin any extra pipes
        rows.append((dimension, score, trend, justification))

    if not rows:
        return '<div class="scoring-summary"></div>'

    row_html = []
    for dimension, score, trend, justification in rows:
        # Color the score bar by quartile
        if score < 30:
            bar_color = "#dc2626"  # red
        elif score < 60:
            bar_color = "#d97706"  # amber
        elif score < 80:
            bar_color = "#65a30d"  # olive
        else:
            bar_color = "#16a34a"  # green
        trend_color = {"↑": "#16a34a", "↓": "#dc2626", "→": "#6b7280", "⇅": "#d97706"}.get(trend, "#6b7280")
        score_bar_width = max(2, score)  # at least 2% so it's visible
        row_html.append(
            f'<div class="scoring-row">'
            f'<div class="scoring-dimension">{dimension}</div>'
            f'<div class="scoring-bar-container">'
            f'<div class="scoring-bar" style="width: {score_bar_width}%; background-color: {bar_color};"></div>'
            f'<div class="scoring-value">{score}</div>'
            f'</div>'
            f'<div class="scoring-trend" style="color: {trend_color};">{trend}</div>'
            f'<div class="scoring-justification">{_process_inline_markdown(justification)}</div>'
            f'</div>'
        )

    # Header labels: detect Arabic in the title to switch to Arabic headers.
    # This is a heuristic — analysts can override by writing the title in
    # the document language. Arabic Unicode range: U+0600–U+06FF (plus
    # U+0750–U+077F supplement and U+FB50–U+FDFF presentation forms).
    has_arabic_chars = any(
        "\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F"
        for ch in title
    )
    if has_arabic_chars:
        lbl_dim = "البُعد"
        lbl_score = "الدرجة (0-100)"
        lbl_trend = "الاتجاه"
        lbl_just = "المبرر"
    else:
        lbl_dim = "Dimension"
        lbl_score = "Score (0-100)"
        lbl_trend = "Trend"
        lbl_just = "Justification"

    return (
        f'<div class="scoring-summary">'
        f'<div class="scoring-summary-title">{title}</div>'
        f'<div class="scoring-header">'
        f'<div class="scoring-dimension">{lbl_dim}</div>'
        f'<div class="scoring-bar-container">{lbl_score}</div>'
        f'<div class="scoring-trend">{lbl_trend}</div>'
        f'<div class="scoring-justification">{lbl_just}</div>'
        f'</div>'
        + "".join(row_html)
        + '</div>'
    )


def render_fenced_divs(md: str):
    """
    Convert ::: class-name ... ::: blocks into HTML.

    Most classes (exec-summary, snapshot, key-judgment, scenario, outlook)
    pass through as a styled <div>. Two classes are rendered specially:

      - verdict-strip: four-cell colored-dot dimension strip
      - risk-matrix:   2x2 Likelihood x Impact plot with markers

    Iterates until no more fences remain, which lets nested fenced blocks
    (e.g., a verdict-strip inside an exec-summary) render correctly: the
    innermost block matches first because the non-greedy regex prefers the
    shortest valid match, and once it's converted to HTML it no longer
    contains :::, so the next pass sees the outer block as the innermost.
    """
    # Match a fenced block whose body does NOT contain a "::: word" opener.
    # This guarantees we only process truly innermost blocks per pass.
    #
    # Inline whitespace ([ \t]*, not \s*) anchors the opener/closer to one
    # line each. Without this, `\s*` would consume newlines and let the
    # regex span an empty line plus a stray "---" horizontal rule, producing
    # spurious class captures. Iteration order makes this a latent rather
    # than active bug today, but the explicit form is safer.
    pattern = re.compile(
        r"^:::[ \t]*([\w-]+)[ \t]*$\n((?:(?!^:::[ \t]*[\w-]+[ \t]*$).)*?)^:::[ \t]*$",
        re.MULTILINE | re.DOTALL
    )

    def repl(m):
        cls = m.group(1)
        inner = m.group(2)
        if cls == "verdict-strip":
            return render_verdict_strip(inner)
        if cls == "risk-matrix":
            return render_risk_matrix(inner)
        if cls == "snapshot":
            return render_snapshot(inner)
        if cls == "faction-box":
            return render_faction_box(inner)
        if cls == "severity-box":
            return render_severity_box(inner)
        if cls == "bilateral-stats" or cls == "stats-strip":
            return render_stats_strip(inner)
        if cls == "chart":
            return render_chart(inner)
        if cls == "map":
            return render_map(inner)
        if cls == "decision-implication":
            return render_decision_implication(inner)
        if cls == "leader-cards":
            return render_leader_cards(inner)
        if cls == "delta-summary":
            return render_delta_summary(inner)
        if cls == "scoring-summary":
            return render_scoring_summary(inner)
        # Default case: wrap in a styled <div> for the class. Process inline
        # markdown (**bold**, *italic*) so scenario/key-judgment/etc. blocks
        # support inline formatting — markdown parsers otherwise skip the
        # content inside the <div> wrapper.
        return f'<div class="{cls}">\n{_process_inline_markdown(inner)}\n</div>'

    # Iterate until no further changes (handles arbitrary nesting depth).
    prev = None
    while prev != md:
        prev = md
        md = pattern.sub(repl, md)
    return md


def render_verdict_strip(inner: str) -> str:
    """
    Render a verdict strip. Input is a bullet list of:
        - Label: color | Caption text

    where color is one of: green, amber, red. Up to 4 cells display in a row.
    """
    cells = []
    for line in inner.strip().splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        body = line.lstrip("-").strip()
        # Format: "Label: color | Caption"
        m = re.match(r"^(.+?):\s*(green|amber|red)\s*\|\s*(.+)$", body, re.IGNORECASE)
        if not m:
            continue
        label = m.group(1).strip()
        color = m.group(2).lower()
        caption = m.group(3).strip()
        cells.append((label, color, caption))

    if not cells:
        return '<div class="verdict-strip"></div>'

    cell_html = []
    for label, color, caption in cells[:4]:  # cap at 4
        cell_html.append(
            f'<div class="verdict-cell">'
            f'<div class="verdict-label">'
            f'<span class="verdict-dot {color}"></span>{label}'
            f'</div>'
            f'<div class="verdict-caption">{caption}</div>'
            f'</div>'
        )
    return '<div class="verdict-strip">' + "".join(cell_html) + "</div>"


def render_risk_matrix(inner: str) -> str:
    """
    Render a 2x2 Likelihood x Impact risk matrix.

    Input is a bullet list of:
        - Risk label | likelihood: low|medium|high|very high|critical | impact: low|medium|high|very high|critical

    Up to 7 risks display as numbered markers on the plot, with a key list
    below the matrix. (Was 3-risk cap; expanded to support exec summaries
    with broader risk inventories.)

    Vocabulary: low/medium/high are the canonical three tiers. "very high"
    and "critical" are accepted as synonyms for "high" and land in the same
    cell visually but flag the risk as more severe in the key list (with a
    "(very high)" or "(critical)" annotation after the label). This handles
    state-collapse and crisis-tier briefs where multiple risks genuinely live
    at the top of the distribution without changing the 3x3 visual structure.
    """
    # Three-step axis: positions for low/medium/high as percentages
    # within the plot region. We nudge the medium slightly so markers
    # don't sit exactly on the quadrant lines.
    pos_x = {"low": 16, "medium": 50, "high": 84}
    pos_y = {"low": 16, "medium": 50, "high": 84}

    # Map extended vocabulary to canonical 3-tier values, preserving the
    # original term so we can annotate it in the key list.
    def normalize_severity(raw: str) -> tuple:
        """Returns (canonical_value, original_label_if_extended). The
        original label is None for canonical values, or the original
        string for extended values."""
        raw_lower = raw.strip().lower()
        if raw_lower in ("low", "medium", "high"):
            return (raw_lower, None)
        if raw_lower in ("very high", "very-high", "veryhigh", "critical"):
            return ("high", raw_lower)
        return (None, None)

    risks = []
    for line in inner.strip().splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        body = line.lstrip("-").strip()
        # Format: "Label | likelihood: X | impact: Y"
        parts = [p.strip() for p in body.split("|")]
        if len(parts) < 3:
            continue
        label = parts[0]
        lk = im = None
        lk_orig = im_orig = None
        for p in parts[1:]:
            # Accept extended vocabulary in the value pattern
            m = re.match(
                r"(likelihood|impact):\s*(low|medium|high|very[\s-]?high|critical)",
                p, re.IGNORECASE,
            )
            if m:
                axis = m.group(1).lower()
                canonical, original = normalize_severity(m.group(2))
                if canonical is None:
                    continue
                if axis == "likelihood":
                    lk, lk_orig = canonical, original
                else:
                    im, im_orig = canonical, original
        if not (label and lk and im):
            continue
        # If either axis used extended vocabulary, annotate the label
        annotations = []
        if lk_orig:
            annotations.append(f"likelihood: {lk_orig}")
        if im_orig:
            annotations.append(f"impact: {im_orig}")
        if annotations:
            label = f"{label} <span class=\"risk-annotation\">({'; '.join(annotations)})</span>"
        risks.append((label, lk, im))

    if not risks:
        return ""

    # Build matrix HTML — support up to 7 risks.
    # When multiple risks land at the same (likelihood, impact) cell,
    # we offset their markers slightly so they don't fully overlap.
    cell_counts = {}  # (lk, im) → count of risks landing here
    markers = []
    key_items = []
    for i, (label, lk, im) in enumerate(risks[:7], start=1):
        cell = (lk, im)
        cell_idx = cell_counts.get(cell, 0)
        cell_counts[cell] = cell_idx + 1

        x_pct = pos_x.get(lk, 50)
        y_pct = 100 - pos_y.get(im, 50)  # invert: high impact at top

        # Offset markers in the same cell so they don't fully overlap.
        # Stagger horizontally and vertically in a zigzag pattern.
        if cell_idx > 0:
            offsets = [(0, 0), (8, 4), (-8, -4), (8, -4), (-8, 4)]
            dx, dy = offsets[cell_idx % len(offsets)]
            x_pct = max(5, min(95, x_pct + dx))
            y_pct = max(5, min(95, y_pct + dy))

        markers.append(
            f'<div class="risk-marker" style="left:{x_pct}%; top:{y_pct}%;">'
            f'<div class="risk-marker-dot">{i}</div>'
            f'</div>'
        )
        key_items.append(
            f'<div><span class="marker-key">{i}</span>{label} '
            f'<em>(L: {lk} / I: {im})</em></div>'
        )

    return (
        '<div class="risk-matrix-wrapper">'
        '<div class="risk-matrix-title">Critical Risks</div>'
        '<div class="risk-matrix">'
        # Y-axis labels (high at top, low at bottom)
        '<div class="risk-y-axis">'
        '<div>High</div><div>Med</div><div>Low</div>'
        '</div>'
        # Plot region with quadrant shading and markers
        '<div class="risk-plot">'
        '<div class="risk-quad q-hh"></div>'
        '<div class="risk-quad q-hm"></div>'
        '<div class="risk-quad q-mh"></div>'
        + "".join(markers) +
        '</div>'
        # X-axis labels and title
        '<div></div>'  # corner spacer
        '<div class="risk-x-axis">'
        '<div class="axis-labels">'
        '<span>Low</span><span>Med</span><span>High</span>'
        '</div>'
        '<div class="axis-title">Likelihood →</div>'
        '</div>'
        '</div>'
        '<div class="risk-marker-list">' + "".join(key_items) + '</div>'
        '</div>'
    )


def render_snapshot(inner: str) -> str:
    """
    Render the country snapshot box.

    Structure:
      ### Block Name
      - Key: Value [optional trend arrow]
      - Key: Value
      ...

      Last reviewed: [Month YYYY]
      Sources: [comma-separated list of institutions]

    Up to 4 sub-blocks are placed in a 2x2 grid. Trend arrows (↑ → ↓ ⇅) at
    the end of a value get wrapped in a colored span. The "Last reviewed"
    and "Sources" lines are rendered as styled metadata at the bottom of
    the box.
    """
    arrow_class = {
        "↑": ("up", "↑"),
        "→": ("stable", "→"),
        "↓": ("down", "↓"),
        "⇅": ("volatile", "⇅"),
    }

    def format_value(val: str) -> str:
        """Detect a trailing trend arrow and wrap it in a styled span."""
        val = val.strip()
        for arrow, (cls, sym) in arrow_class.items():
            # Match the arrow at the end, with optional surrounding whitespace
            pattern = re.compile(r"\s*" + re.escape(arrow) + r"\s*$")
            if pattern.search(val):
                base = pattern.sub("", val).strip()
                return f'{base}<span class="snapshot-trend {cls}">{sym}</span>'
        return val

    # Parse the inner content
    blocks = []                # list of (header, [(key, value), ...])
    current_block = None       # currently-being-filled block
    last_reviewed = None
    sources = None

    for raw_line in inner.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Sub-block header: "### BlockName"
        m = re.match(r"^###\s+(.+)$", line)
        if m:
            if current_block is not None:
                blocks.append(current_block)
            current_block = (m.group(1).strip(), [])
            continue

        # Meta lines (treated case-insensitively)
        m = re.match(r"^Last reviewed\s*:\s*(.+)$", line, re.IGNORECASE)
        if m:
            last_reviewed = m.group(1).strip()
            continue
        m = re.match(r"^Sources?\s*:\s*(.+)$", line, re.IGNORECASE)
        if m:
            sources = m.group(1).strip()
            continue

        # Bullet item: "- Key: Value" OR "- Key | Value"
        # Both separators are accepted for consistency with other components
        # (stats-strip, severity-box, etc.) which use `|`. The snapshot
        # historically used `:` only, which caused friction when analysts
        # mixed formats across components in the same brief. Pipe is
        # preferred for new content since it avoids ambiguity with values
        # that contain colons (e.g., URLs, time formats).
        if line.startswith("-"):
            body = line.lstrip("-").strip()
            # Try pipe first (the more visually distinct separator)
            if "|" in body:
                key, value = body.split("|", 1)
            elif ":" in body:
                key, value = body.split(":", 1)
            else:
                continue
            key = key.strip()
            value = format_value(value)
            if current_block is None:
                # Items before any block header — make a default block
                current_block = ("Snapshot", [])
            current_block[1].append((key, value))
            continue

    if current_block is not None:
        blocks.append(current_block)

    if not blocks:
        # Fall back to a plain pass-through for older briefs that haven't
        # been migrated to the new convention yet
        return f'<div class="snapshot">\n{inner}\n</div>'

    # Build the HTML
    block_html_parts = []
    for header, items in blocks[:4]:  # cap at 4 sub-blocks
        item_html = "".join(
            f'<div class="snapshot-item">'
            f'<span class="key">{k}</span>'
            f'<span class="val">{v}</span>'
            f'</div>'
            for k, v in items
        )
        block_html_parts.append(
            f'<div class="snapshot-block">'
            f'<div class="snapshot-block-header">{header}</div>'
            f'{item_html}'
            f'</div>'
        )

    grid_html = '<div class="snapshot-blocks">' + "".join(block_html_parts) + '</div>'

    reviewed_html = (
        f'<div class="snapshot-reviewed"><strong>Last reviewed:</strong> {last_reviewed}</div>'
        if last_reviewed else ""
    )
    sources_html = (
        f'<div class="snapshot-source"><strong>Sources:</strong> {sources}</div>'
        if sources else ""
    )

    return (
        '<div class="snapshot">'
        + grid_html
        + reviewed_html
        + sources_html
        + '</div>'
    )


def render_faction_box(inner: str, default_title: str = "Key Factions") -> str:
    """
    Render a faction listing box, or a sub-national severity listing.

    The same component renders both — they share the structure of
    "labeled rows with color-coded category badges and a one-line stance".
    Reused for:
      - Political factions in section 2 (ruling/opposition/insurgent/
        mixed/military, plus religious-authority for theocratic states)
      - Sub-national conflict severity in section 4 (severe/high/medium/
        contained/stable)

    Input format:
        - Name | Category | One-line stance/driver
    where Category is one of: ruling, opposition, insurgent, mixed,
    military, religious-authority (for political) or severe, high, medium,
    contained, stable (for severity).

    The "military" category is for cases where the armed forces are a
    political-economic actor in their own right (Pakistan, Egypt, Sudan,
    Myanmar, Algeria), not just an institution under civilian control.
    The "religious-authority" category is for theocratic or semi-theocratic
    states where clerical bodies hold independent decision-making power
    (Iran's Supreme Leader and Assembly of Experts, the Saudi religious
    establishment, etc.).

    Optional first line:
        title: Custom Box Title
    to override the default "Key Factions" header.
    """
    position_class_map = {
        # Political faction categories
        "ruling": "ruling",
        "opposition": "opposition",
        "opposition / extra-system": "opposition",
        "insurgent": "insurgent",
        "mixed": "mixed",
        # Military as political-economic actor — distinct from "insurgent"
        # (which connotes anti-state armed groups). "military" indicates
        # the state's own armed forces operating as an independent power
        # center: e.g., Pakistan Army, Egyptian military, Myanmar SAC,
        # Algeria's pouvoir, Sudan's SAF.
        "military": "military",
        "armed forces": "military",
        "praetorian": "military",
        # Religious authority as independent power center — for theocratic
        # or semi-theocratic states. Distinct from religious *parties*
        # (which are political and fit under ruling/opposition).
        "religious-authority": "religious-authority",
        "religious authority": "religious-authority",
        "clerical": "religious-authority",
        # Severity categories
        "severe": "severe",
        "high": "high",
        "medium": "medium",
        "contained": "contained",
        "stable": "stable",
        "escalating": "severe",
        "deteriorating": "high",
        "chronic": "medium",
        "re-escalating": "severe",
    }

    rows = []
    title = default_title
    for raw_line in inner.strip().splitlines():
        line = raw_line.strip()
        # Optional title override
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
            continue
        if not line.startswith("-"):
            continue
        body = line.lstrip("-").strip()
        parts = [p.strip() for p in body.split("|")]
        if len(parts) < 2:
            continue
        while len(parts) < 3:
            parts.append("")
        name, position, stance = parts[0], parts[1], parts[2]

        # Map position to a CSS class (lowercase, simple normalization)
        pos_key = position.lower().strip()
        pos_class = position_class_map.get(pos_key, "other")

        rows.append(
            '<div class="faction-row">'
            f'<span class="faction-name">{name}</span>'
            f'<span class="faction-position {pos_class}">{position}</span>'
            + (f'<div class="faction-stance">{stance}</div>' if stance else '')
            + '</div>'
        )

    if not rows:
        return ""

    return (
        '<div class="faction-box">'
        f'<div class="faction-box-title">{title}</div>'
        + "".join(rows)
        + '</div>'
    )


def render_severity_box(inner: str) -> str:
    """Alias for render_faction_box with a severity-oriented default title."""
    return render_faction_box(inner, default_title="Sub-National Severity")


def render_stats_strip(inner: str) -> str:
    """
    Render a stats strip with 1-4 headline numbers in tiles.

    Used at the top of:
      - Section 1.5 (bilateral relations) — headline bilateral numbers
      - Section 4 (security & stability)  — sub-national severity headline
      - Section 8 (humanitarian severity) — PIN, IDPs, funding, INFORM Risk
      - Any other section that needs a 4-tile summary

    Input format:
        - Value | Label | Optional source/footnote
    e.g.,
        ::: stats-strip
        - 18.9M | People in need (2025) | OCHA
        - 3.3M  | IDPs nationally | IOM DTM
        - $311M | Funding tracked 2025 | FTS
        - Very High | INFORM Risk Index | 2025 release
        :::

    The component is also addressable as `::: bilateral-stats` for
    backwards compatibility with existing briefs.
    """
    stats = []
    for raw_line in inner.strip().splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        body = line.lstrip("-").strip()
        parts = [p.strip() for p in body.split("|")]
        if len(parts) < 2:
            continue
        # Pad to 3 fields (value, label, footnote)
        while len(parts) < 3:
            parts.append("")
        value, label, footnote = parts[0], parts[1], parts[2]
        stats.append((value, label, footnote))

    if not stats:
        return ""

    # Cap at 4 tiles to keep the strip clean
    tile_html = []
    for value, label, footnote in stats[:4]:
        footnote_html = (
            f'<div class="footnote">{footnote}</div>'
            if footnote else ""
        )
        tile_html.append(
            '<div class="stats-tile">'
            f'<div class="value">{value}</div>'
            f'<div class="label">{label}</div>'
            f'{footnote_html}'
            '</div>'
        )

    return '<div class="stats-strip">' + "".join(tile_html) + '</div>'



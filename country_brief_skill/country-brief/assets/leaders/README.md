# Curated leader photos

This directory is the **official-source-first** tier of the leader-cards photo cascade. Drop a portrait file here under a deterministic slug and every future brief that names that figure will pick it up automatically, with no markdown changes required.

## Slug rule

The renderer derives the filename from the leader's `name` field in the `::: leader-cards` block. Rules:

- Lowercase the name.
- NFKD-normalize and strip combining marks (so `Houmed M'saidié` → `houmed-msaidie`).
- Replace any run of non-alphanumeric characters with a single hyphen.
- Trim leading/trailing hyphens.

Examples:

| Leader name | Slug | Filename to drop |
|---|---|---|
| Azali Assoumani | `azali-assoumani` | `azali-assoumani.jpg` |
| Nour El Fath Azali | `nour-el-fath-azali` | `nour-el-fath-azali.jpg` |
| Sheikh Mohamed bin Zayed Al Nahyan | `sheikh-mohamed-bin-zayed-al-nahyan` | `sheikh-mohamed-bin-zayed-al-nahyan.jpg` |
| Houmed Msaidie | `houmed-msaidie` | `houmed-msaidie.jpg` |
| Khaled Belhoul | `khaled-belhoul` | `khaled-belhoul.jpg` |

Supported extensions (checked in order): `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`.

## Cascade ordering

The renderer resolves a leader-card photo in this order:

1. Explicit `photo_source` field in the markdown (e.g., `https://...`, `wiki:Name`, local path).
2. **This directory** — `assets/leaders/{slug}.{ext}`.
3. Wikipedia REST API cascade — `en` → `fr` → `ar`.
4. Monogram placeholder.

If the analyst supplies an explicit source, that wins. Otherwise the bundled directory is checked before the network is touched, so curated photos render even in sandboxed environments without internet access.

## Photo discipline

- **Use official sources.** Foreign-ministry pages, AU/UN press hubs, government communiqués. Don't substitute social-media avatars or random news-site thumbnails.
- **Reasonable resolution.** ~500 px on the short side is enough for crisp PDF rendering at the 4.5 cm card size. Don't bother with 4K originals.
- **Aspect ratio.** Roughly square or portrait works best with the card layout. Landscape group photos will be center-cropped.
- **Licensing.** Use only photos you have the right to redistribute. Government-issued portraits are usually fine; press-agency photos generally aren't.
- **Refresh on incumbency change.** When a leader leaves office, replace the file (or rename to `{slug}-2024.jpg` and add a successor file under the new slug).

## Not in version control by default

This directory is intentionally near-empty in the skill distribution. Each deployment curates the set relevant to its country portfolio. Add a `.gitignore` entry locally if photos shouldn't ship with your fork.

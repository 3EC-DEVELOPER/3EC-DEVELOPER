# Visitor Analytics System Notes

## Current status

The GitHub profile visitor analytics system is now live and working end-to-end using:

- Cloudflare Workers
- Cloudflare KV
- Dynamic SVG generation
- GitHub profile README integration
- LinkedIn redirect click tracking

## Live endpoints

- SVG analytics panel:
  `https://3ec-visitor-analytics.3ec-visitor-analytics.workers.dev/visitor-stats.svg`
- Health check:
  `https://3ec-visitor-analytics.3ec-visitor-analytics.workers.dev/health`
- LinkedIn tracking redirect:
  `https://3ec-visitor-analytics.3ec-visitor-analytics.workers.dev/r/linkedin`

## Current features

- Persistent total visitor count
- Best-effort unique visitor count
- Daily average
- LinkedIn click count
- GitHub-style SVG dashboard
- Durable storage in Cloudflare KV

## Important implementation notes

- The README now uses the live Worker SVG endpoint instead of the local `assets/visitor-stats.svg` file.
- The old GitHub Actions-based visitor updater has been archived and should not be used as the source of truth anymore.
- The Worker includes both:
  - `GET /r/linkedin` for real README click tracking
  - `POST /events/linkedin` as a protected future-ready endpoint
- Cloudflare KV is eventually consistent, so counts are best-effort rather than strictly transactional.

## Key files

- `README.md`
- `scripts/cloudflare-visitor-worker/wrangler.jsonc`
- `scripts/cloudflare-visitor-worker/src/index.ts`
- `data/visitor-analytics-kv-schema.md`
- `data/legacy/update-visitor-stats.disabled.yml`

## Current config values

- Worker name:
  `3ec-visitor-analytics`
- workers.dev subdomain:
  `3ec-visitor-analytics`
- LinkedIn profile URL:
  `https://www.linkedin.com/in/douglasforbes-scott-3ecltd`

## Known behavior

- Clicking the SVG panel itself in GitHub opens the image source. This is expected because the dashboard is rendered as an image, not an interactive HTML widget.
- LinkedIn click tracking works through the README text link, not by clicking the SVG tile.

## Suggested next TODO steps

1. Add lightweight bot filtering for LinkedIn click tracking.
2. Clean up the public Worker URL naming if a shorter URL is preferred.
3. Add a small deployment and maintenance guide for future updates.
4. Consider moving write-sensitive counting to a Durable Object if stronger consistency is ever needed.
5. Optionally add additional tracked outbound links using the same redirect pattern.

## Recommended next phase

Phase 3: bot filtering for redirect-based click tracking while keeping the current README link and Worker endpoint structure unchanged.

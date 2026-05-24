# Visitor Analytics KV Schema

This documents the Cloudflare KV keys used by the visitor analytics Worker.

## Summary key

Key: `stats:summary`

Example value:

```json
{
  "totalVisitors": 42,
  "uniqueVisitors": 19,
  "linkedinClicks": 0,
  "firstSeenDate": "2026-05-24",
  "lastUpdatedAt": "2026-05-24T12:34:56.000Z"
}
```

## Unique marker keys

Key pattern: `unique:v1:<sha256 fingerprint>`

Purpose:
- Marks a visitor fingerprint as already counted for unique totals.
- Best-effort only. This is not identity-grade tracking.

Example value:

```json
{
  "firstSeenAt": "2026-05-24T12:34:56.000Z"
}
```

## Notes

- `totalVisitors` increments on every request to `/visitor-stats.svg`.
- `uniqueVisitors` increments only when a fingerprint has not been seen before.
- `linkedinClicks` is reserved for future tracking via a protected Worker endpoint.

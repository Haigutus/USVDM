# Vendored Ace editor (offline)

Ace **1.36.5** files used by the XML Validator. Served from `/assets/ace/` with
`basePath` set in `../bridge.js`. No CDN at runtime.

Refresh with:

```bash
../scripts/vendor_ace.sh 1.36.5
```

| File | Purpose |
|------|---------|
| `ace.min.js` | Core editor |
| `mode-xml.js` | XML syntax highlighting |
| `mode-text.js` | Log pane |
| `theme-monokai.js` | Dark theme |
| `worker-*.js` | Optional workers (disabled in bridge, kept for completeness) |
| `ext-*.js` | Search box / menus if invoked |

# XML Validator

Live browser UI to validate **IEC 62325** / **EDIGAS** (and other bundled) XML messages against local XSDs.

- In-memory validation with **lxml** (no temp files, no subprocess pipes)
- **Ace** editor vendored under `assets/ace/` (XML + monokai; fully offline — no CDN)
- **Dash/React** UI JS served from the installed `dash` package (`serve_locally=True`)
- Bundled schemas under `XSD/`
- Initial demo document under `examples/ACK_demo_with_error.xml` (deliberate errors)

Production: [https://xsd.cimtools.eu/](https://xsd.cimtools.eu/)

## Run locally (Python 3.13)

```bash
cd Tools/XML_VALIDATOR
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# → http://0.0.0.0:8030
```

## Docker

```bash
cd Tools/XML_VALIDATOR
docker compose up --build
# → http://localhost:8030
```

Runtime is self-contained (no outbound network to boot the UI):

| Piece | Source |
|-------|--------|
| Ace editor (core, XML mode, monokai, workers, searchbox, …) | `assets/ace/` |
| Ace ↔ Dash bridge | `assets/bridge.js` |
| App CSS, favicon, GitHub mark | `assets/` |
| React / Dash renderer / dcc / html | installed `dash` package → `/_dash-component-suites/` |
| XSD schemas | `XSD/` |

Only optional `update_xsds.sh` needs the internet. To refresh Ace after upgrading the version:

```bash
./scripts/vendor_ace.sh 1.36.5
```

## Refresh ENTSO-E CIM / ESMP XSDs

Only replaces `XSD/CIM_*`. EDIGAS, CGMES, OPDM, etc. are left as-is.

```bash
# needs curl/wget + p7zip-full (7z) for the current .7z package
./update_xsds.sh

# or override URL when ENTSO-E renames the package:
XSD_URL=https://www.entsoe.eu/Documents/EDI/Library/CIM_xsd_package_v2026.7z ./update_xsds.sh
```

Package names change over time — check the [ENTSO-E EDI Library](https://www.entsoe.eu/publications/electronic-data-interchange-edi-library/).

After refresh, restart the app or rebuild the image so the XSD index reloads.

## Example messages

Small official samples under `examples/` (from [ENTSO-E Transparency xml-examples](https://gitlab.entsoe.eu/transparency/xml-examples)):

- `examples/ACK_positive.xml` / `ACK_negative.xml` — Acknowledgement_MarketDocument  
- `examples/Actual_Total_Load_6_1_A.xml` — load series  
- `examples/PSD.xml` — Problem Statement  

```bash
python xsd.py examples/ACK_positive.xml
```

## CLI

```bash
python xsd.py path/to/message.xml
```

## Layout

| Area | Role |
|------|------|
| Thin header | Title + GitHub link |
| Main Ace | Paste XML (live validate, gutter errors) |
| Log Ace | Status + error messages |

Repo: [Haigutus/USVDM · Tools/XML_VALIDATOR](https://github.com/Haigutus/USVDM/tree/master/Tools/XML_VALIDATOR)

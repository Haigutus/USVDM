"""XML Validator UI — Dash + Ace (CDN, full XML mode), live XSD validation."""

import os
from pathlib import Path

from dash import Dash, html, dcc, Input, Output, clientside_callback, callback

from xsd import validate

GITHUB_URL = "https://github.com/Haigutus/USVDM/tree/master/Tools/XML_VALIDATOR"
EXAMPLES = Path(__file__).resolve().parent / "examples"
DEMO_FILE = EXAMPLES / "ACK_demo_with_error.xml"

INITIAL_XML = DEMO_FILE.read_text(encoding="utf-8") if DEMO_FILE.is_file() else (
    "<!-- Demo file missing; paste IEC 62325 / EDIGAS XML here -->\n<root/>\n"
)

ACE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/ace/1.36.5"

app = Dash(
    __name__,
    title="XML Validator",
    external_scripts=[f"{ACE_CDN}/ace.min.js"],
)
server = app.server

app.layout = html.Div(
    className="page",
    children=[
        html.Header(
            className="header",
            children=[
                html.H1("XML Validator"),
                html.A(
                    html.Img(src="/assets/github-mark-white.svg", alt="GitHub"),
                    href=GITHUB_URL,
                    target="_blank",
                    title="View on GitHub",
                ),
            ],
        ),
        html.Div(
            className="main",
            children=[
                html.Div(
                    className="xml-editor",
                    children=[html.Div(id="xml-ace")],
                ),
                html.Div(
                    className="log-editor",
                    children=[html.Div(id="log-ace")],
                ),
            ],
        ),
        dcc.Store(id="xml-initial", data=INITIAL_XML),
        dcc.Store(id="xml-store", data=""),
        dcc.Store(id="log-store", data=""),
        dcc.Store(id="ann-store", data=[]),
        dcc.Interval(id="ace-init", interval=200, max_intervals=1),
        html.Div(id="ace-sink", style={"display": "none"}),
    ],
)

clientside_callback(
    """
    function(n, initialXml) {
        return window.dash_clientside.ace_bridge.init(n, initialXml);
    }
    """,
    Output("xml-store", "data"),
    Input("ace-init", "n_intervals"),
    Input("xml-initial", "data"),
    prevent_initial_call=False,
)

clientside_callback(
    """
    function(logText, annotations) {
        return window.dash_clientside.ace_bridge.applyResults(logText, annotations);
    }
    """,
    Output("ace-sink", "children"),
    Input("log-store", "data"),
    Input("ann-store", "data"),
    prevent_initial_call=False,
)


def _annotations(errors):
    """Ace annotation shape: row (0-based), column, type, text (hover).

    One annotation per error (not deduped) so multiple issues on different
    lines all get gutter marks. Same-line issues stack in the hover tooltip.
    """
    out = []
    for e in errors:
        line = e.get("line") or 1
        row = max(int(line) - 1, 0)
        col = max(int(e.get("column") or 1) - 1, 0)
        out.append({
            "row": row,
            "column": col,
            "type": "error",
            "text": e.get("message", "error"),
        })
    return out


@callback(
    Output("log-store", "data"),
    Output("ann-store", "data"),
    Input("xml-store", "data"),
)
def on_xml(content):
    # Ignore empty initial store so we don't flash a clear over real results
    if content is None or content == "":
        return "", []
    if not str(content).strip():
        return "", []

    result = validate(content)
    log = "\n".join(result["status_lines"])
    return log, _annotations(result["errors"])


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8030"))
    app.run(debug=False, host="0.0.0.0", port=port)

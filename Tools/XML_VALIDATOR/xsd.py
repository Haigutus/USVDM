"""Minimal in-memory XML / XSD validation (lxml, no temp files)."""

from datetime import datetime, timezone
from pathlib import Path
from lxml import etree

XSD_DIR = Path(__file__).resolve().parent / "XSD"


def _index_xsds(root=XSD_DIR):
    """namespace -> sorted list of xsd paths."""
    index = {}
    if not root.is_dir():
        return index
    for path in sorted(root.rglob("*.xsd")):
        try:
            ns = etree.parse(str(path)).getroot().get("targetNamespace", "")
        except etree.XMLSyntaxError:
            continue
        if ns:
            index.setdefault(ns, []).append(path)
    return index


XSD_INDEX = _index_xsds()


def _pick_xsd(paths):
    """Prefer CIM_* package paths; else first sorted path."""
    cim = [p for p in paths if "CIM_" in p.parts]
    return sorted(cim or paths)[0]


def _root_namespace(doc):
    tag = doc.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return doc.nsmap.get(None) or ""


def _parse_xml(xml):
    if isinstance(xml, (bytes, bytearray)):
        return etree.fromstring(xml)
    if isinstance(xml, str):
        text = xml.strip()
        if not text or text.startswith("Copy your"):
            raise ValueError("empty XML")
        return etree.fromstring(text.encode("utf-8"))
    raise TypeError("xml must be str or bytes")


def _load_schema(xsd):
    """xsd: path | str | bytes. Paths resolve xs:include; strings are self-contained."""
    if isinstance(xsd, Path) or (isinstance(xsd, str) and Path(xsd).is_file()):
        return etree.XMLSchema(etree.parse(str(xsd)))
    if isinstance(xsd, (bytes, bytearray)):
        return etree.XMLSchema(etree.fromstring(xsd))
    if isinstance(xsd, str):
        return etree.XMLSchema(etree.fromstring(xsd.encode("utf-8")))
    raise TypeError("xsd must be path, str, or bytes")


def _error_entries(error_log):
    """Collect every entry from an lxml error log (no dedupe / no cap)."""
    errors = []
    for e in error_log:
        errors.append({
            "line": e.line or 0,
            "column": e.column or 0,
            "message": e.message or str(e),
            "domain_name": getattr(e, "domain_name", "") or "",
            "type_name": getattr(e, "type_name", "") or "",
            "path": getattr(e, "path", "") or "",
        })
    return errors


def _ts():
    """UTC ISO 8601 with T separator and Z, e.g. 2026-08-08T12:09:34.090Z (server clock, UTC)."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )

def _log_lines(ts, *parts):
    """One timestamped line per part."""
    return [f"[{ts}] {p}" for p in parts]


def validate(xml, xsd=None):
    """
    Validate XML in memory.

    Returns dict:
      ok, errors[{line, column, message, ...}], xsd_used, status_lines[str]
    """
    ts = _ts()
    status = []
    errors = []

    # XML
    try:
        doc = _parse_xml(xml)
        status.extend(_log_lines(ts, "XML      OK - loaded"))
    except Exception as exc:
        msg = str(exc)
        line = getattr(exc, "lineno", None) or 0
        if not line:
            pos = getattr(exc, "position", None)
            if isinstance(pos, tuple) and pos:
                line = pos[0] or 0
        errors.append({"line": line, "column": 0, "message": msg})
        status.extend(_log_lines(
            ts,
            "XML      ERROR - Loading failed",
            f"L{line or '?':<6} {msg}",
        ))
        return {
            "ok": False,
            "errors": errors,
            "xsd_used": "",
            "status_lines": status,
        }

    # XSD resolve
    xsd_used = ""
    try:
        if xsd:
            schema = _load_schema(xsd)
            xsd_used = "provided XSD" if not isinstance(xsd, Path) else Path(xsd).name
        else:
            ns = _root_namespace(doc)
            paths = XSD_INDEX.get(ns, [])
            if not paths:
                status.extend(_log_lines(
                    ts,
                    "XSD      ERROR - no schema for namespace",
                    f"         {ns or '(none)'}",
                ))
                return {
                    "ok": False,
                    "errors": errors,
                    "xsd_used": "",
                    "status_lines": status,
                }
            path = _pick_xsd(paths)
            schema = _load_schema(path)
            xsd_used = path.name
        status.extend(_log_lines(ts, f"XSD      {xsd_used}"))
    except Exception as exc:
        status.extend(_log_lines(ts, "XSD      ERROR - Loading failed", f"         {exc}"))
        return {
            "ok": False,
            "errors": errors,
            "xsd_used": xsd_used,
            "status_lines": status,
        }

    # Validate in memory — use a fresh error log via assertValid-style collect
    # schema.validate() fills schema.error_log with all libxml2 messages
    ok = bool(schema.validate(doc))
    errors = _error_entries(schema.error_log)

    # Also pull from doc if any (usually empty for schema errs)
    n = len(errors)
    status.extend(_log_lines(
        ts,
        f"Result   {n} error(s)" if n else "Result   valid",
    ))
    for e in errors:
        line = e["line"] or "?"
        status.extend(_log_lines(ts, f"L{line:<6} {e['message']}"))

    return {
        "ok": ok and not errors,
        "errors": errors,
        "xsd_used": xsd_used,
        "status_lines": status,
    }


if __name__ == "__main__":
    import sys

    xml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not xml_path or not xml_path.is_file():
        print(f"Indexed {sum(len(v) for v in XSD_INDEX.values())} XSDs, {len(XSD_INDEX)} namespaces")
        print("Usage: python xsd.py <file.xml>")
        sys.exit(0)

    result = validate(xml_path.read_text(encoding="utf-8", errors="replace"))
    print("\n".join(result["status_lines"]))
    sys.exit(0 if result["ok"] else 1)

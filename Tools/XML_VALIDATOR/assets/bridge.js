/* Bridge: vendored Ace <-> Dash Stores — XML mode + monokai + gutter annotations */
(function () {
  // Local Ace only (assets/ace/) — no CDN / network at runtime
  var ACE_BASE = "/assets/ace/";
  var xmlEditor = null;
  var logEditor = null;
  var markerIds = [];
  var changeTimer = null;
  var lastXmlSent = null;
  var pendingLog = null;
  var pendingAnns = null;
  var lastAnns = [];
  var initDone = false;

  function ensureAceConfig() {
    if (!window.ace) return false;
    ace.config.set("basePath", ACE_BASE);
    ace.config.set("workerPath", ACE_BASE);
    ace.config.set("modePath", ACE_BASE);
    ace.config.set("themePath", ACE_BASE);
    return true;
  }

  function clearMarkers() {
    if (!xmlEditor) return;
    markerIds.forEach(function (id) {
      xmlEditor.session.removeMarker(id);
    });
    markerIds = [];
  }

  function applyAnnotationsAndMarkers(annotations) {
    if (!xmlEditor) {
      pendingAnns = annotations;
      return;
    }
    // Keep last non-empty application intent (including explicit clear)
    var anns = Array.isArray(annotations) ? annotations : [];
    lastAnns = anns;
    pendingAnns = null;

    // Disable worker every time — XML worker overwrites our annotations
    try {
      xmlEditor.session.setUseWorker(false);
    } catch (e) {}

    xmlEditor.session.clearAnnotations();
    if (anns.length) {
      xmlEditor.session.setAnnotations(anns);
    }

    clearMarkers();
    if (anns.length) {
      var Range = ace.require("ace/range").Range;
      var seen = {};
      anns.forEach(function (a) {
        var row = typeof a.row === "number" ? a.row : parseInt(a.row, 10) || 0;
        // one full-line marker per row; all annotations still listed for hover
        if (seen[row]) return;
        seen[row] = true;
        var id = xmlEditor.session.addMarker(
          new Range(row, 0, row, 1),
          "ace_error-line",
          "fullLine"
        );
        markerIds.push(id);
      });
    }

    try {
      xmlEditor.renderer.updateFull();
    } catch (e) {}
  }

  /** Re-apply after Ace theme/mode/worker settles (initial-load race). */
  function reapplyAnnotationsSoon() {
    [0, 50, 150, 400].forEach(function (ms) {
      setTimeout(function () {
        if (!xmlEditor) return;
        applyAnnotationsAndMarkers(lastAnns);
      }, ms);
    });
  }

  function setLog(text) {
    if (!logEditor) {
      pendingLog = text;
      return;
    }
    pendingLog = null;
    logEditor.session.setValue(text == null ? "" : String(text), -1);
  }

  function flushPending() {
    if (pendingLog !== null) {
      setLog(pendingLog);
    }
    if (pendingAnns !== null) {
      applyAnnotationsAndMarkers(pendingAnns);
    } else if (lastAnns && lastAnns.length) {
      applyAnnotationsAndMarkers(lastAnns);
    }
  }

  function initXmlEditor(initialValue) {
    if (!ensureAceConfig()) return null;
    var host = document.getElementById("xml-ace");
    if (!host) return null;
    if (xmlEditor) return xmlEditor;

    xmlEditor = ace.edit(host);
    xmlEditor.setTheme("ace/theme/monokai");
    xmlEditor.session.setMode("ace/mode/xml");
    // Critical: Ace XML worker replaces session annotations — turn it off
    xmlEditor.session.setUseWorker(false);
    xmlEditor.setOptions({
      fontSize: 14,
      showPrintMargin: false,
      highlightActiveLine: true,
      showGutter: true,
      displayIndentGuides: true,
      tabSize: 2,
      useSoftTabs: true,
      wrap: false,
      fixedWidthGutter: true,
      useWorker: false,
    });
    xmlEditor.renderer.setShowGutter(true);

    xmlEditor.session.setValue(initialValue || "", -1);
    lastXmlSent = xmlEditor.getValue();

    xmlEditor.session.on("change", function () {
      clearTimeout(changeTimer);
      changeTimer = setTimeout(function () {
        var v = xmlEditor.getValue();
        if (v === lastXmlSent) return;
        lastXmlSent = v;
        if (window.dash_clientside && dash_clientside.set_props) {
          dash_clientside.set_props("xml-store", { data: v });
        }
      }, 400);
    });

    setTimeout(function () {
      if (xmlEditor) {
        xmlEditor.session.setUseWorker(false);
        xmlEditor.resize(true);
      }
    }, 50);

    return xmlEditor;
  }

  function initLogEditor() {
    if (!ensureAceConfig()) return null;
    var host = document.getElementById("log-ace");
    if (!host) return null;
    if (logEditor) return logEditor;

    logEditor = ace.edit(host);
    logEditor.setTheme("ace/theme/monokai");
    logEditor.session.setMode("ace/mode/text");
    logEditor.session.setUseWorker(false);
    logEditor.setOptions({
      fontSize: 13,
      showPrintMargin: false,
      highlightActiveLine: false,
      readOnly: true,
      showGutter: false,
      highlightGutterLine: false,
      wrap: true,
      useWorker: false,
    });
    if (logEditor.renderer.$cursorLayer) {
      logEditor.renderer.$cursorLayer.element.style.display = "none";
    }
    setTimeout(function () {
      if (logEditor) logEditor.resize(true);
    }, 50);
    return logEditor;
  }

  function doInit(initialXml) {
    if (!ensureAceConfig()) return false;
    if (!document.getElementById("xml-ace") || !document.getElementById("log-ace")) {
      return false;
    }
    initXmlEditor(initialXml || "");
    initLogEditor();
    flushPending();
    initDone = !!(xmlEditor && logEditor);
    return initDone;
  }

  function pushXmlToDash(initialXml) {
    var v = (xmlEditor && xmlEditor.getValue()) || initialXml || "";
    lastXmlSent = v;
    if (window.dash_clientside && dash_clientside.set_props) {
      dash_clientside.set_props("xml-store", { data: v });
    }
    return v;
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    ace_bridge: {
      init: function (n, initialXml) {
        if (!n) {
          return window.dash_clientside.no_update;
        }
        if (initDone && xmlEditor) {
          return window.dash_clientside.no_update;
        }

        function attempt(left) {
          if (doInit(initialXml || "")) {
            return pushXmlToDash(initialXml);
          }
          if (left > 0) {
            setTimeout(function () {
              attempt(left - 1);
            }, 100);
          }
          return window.dash_clientside.no_update;
        }

        if (!window.ace) {
          setTimeout(function () {
            attempt(20);
          }, 100);
          return window.dash_clientside.no_update;
        }
        return attempt(20);
      },

      applyResults: function (logText, annotations) {
        pendingLog = logText;
        // Remember even when editor not ready yet
        if (Array.isArray(annotations)) {
          lastAnns = annotations;
          pendingAnns = annotations;
        }
        if (xmlEditor || logEditor) {
          setLog(logText);
          applyAnnotationsAndMarkers(annotations);
          // Re-apply after Ace async theme/mode load on first paint
          reapplyAnnotationsSoon();
        }
        if (xmlEditor) {
          try {
            xmlEditor.session.setUseWorker(false);
            xmlEditor.resize(true);
          } catch (e) {}
        }
        if (logEditor) {
          try {
            logEditor.resize(true);
          } catch (e) {}
        }
        return window.dash_clientside.no_update;
      },
    },
  });

  window.addEventListener("resize", function () {
    if (xmlEditor) xmlEditor.resize(true);
    if (logEditor) logEditor.resize(true);
  });
})();

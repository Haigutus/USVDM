# Example XML messages

Official samples from **ENTSO-E Transparency Platform** XML examples:

- Repo: https://gitlab.entsoe.eu/transparency/xml-examples  
- Branch: `main`

| File | Document | Namespace / XSD (auto-matched) |
|------|----------|--------------------------------|
| `ACK_demo_with_error.xml` | **UI initial load** — bad datetime + `THIS_IS_WRONG` | same as positive (2 errors) |
| `ACK_positive.xml` | Acknowledgement (accept) | `iec62325-451-1-acknowledgement_v7_0.xsd` |
| `ACK_negative.xml` | Acknowledgement (reject) | same |
| `ACK_positive_sourceXML.xml` | Source doc for positive ACK | generation/load v3 |
| `Actual_Total_Load_6_1_A.xml` | Actual Total Load [6.1.A] | generation/load v3 |
| `PSD.xml` | Problem Statement Document | `iec62325-451-5-problem_v3_0.xsd` |

All of the above validate with **0 errors** against the bundled `XSD/` tree (checked with `python xsd.py <file>`).

```bash
cd Tools/XML_VALIDATOR
python xsd.py examples/ACK_positive.xml
# paste contents into the UI at http://localhost:8030
```

To re-fetch from GitLab API:

```bash
# example
curl -sSL \
  "https://gitlab.entsoe.eu/api/v4/projects/669/repository/files/Acknowledgements%2FACK_positive.xml/raw?ref=main"
```

import json
from collections import Counter

with open("bandit_report.json", "r", encoding="utf-8") as fh:
    report = json.load(fh)

results = report.get("results", [])
print("Total findings:", len(results))
print("Severity:", Counter(x.get("issue_severity") for x in results))
print("Confidence:", Counter(x.get("issue_confidence") for x in results))

for finding in results:
    print(
        finding.get("test_id"),
        finding.get("issue_severity"),
        finding.get("issue_confidence"),
        finding.get("filename"),
        finding.get("line_number"),
        finding.get("issue_text"),
    )

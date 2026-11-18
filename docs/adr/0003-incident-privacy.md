# ADR-0003: Incident reporting and safe GitHub issue creation

Status: PROPOSED / REQUIRED POLICY. Development worker automatically files or updates issues under scoped GitHub authority after sanitization; end-user client collects local minimal incidents and only uploads with reporting enabled. GitHub credentials never reside in shipping client. Private security vulnerabilities never enter a public ticket. Dedup, rate controls, local offline spool and verified closure are mandatory. See [incident spec](../operations/ISSUE_AUTOMATION.md).

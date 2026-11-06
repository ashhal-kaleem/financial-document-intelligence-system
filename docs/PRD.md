# Product requirements: FDIS V1

## User outcome

A signed-in analyst uploads a text-based annual report, gets clear processing status, asks report-specific questions, and checks every answer against page-level evidence. No cross-user document access.

## Required behavior

- Private document library and authenticated file viewing.
- Queued processing, bounded retries, lease heartbeats and fenced DB writes.
- Preserve page/source metadata, financial scale, currency, year, signs and reporting basis.
- Cite only retrieved sources; no-source queries return a fixed non-disclosure answer.
- Provider failures, incomplete streams and invalid citation identifiers are failures, not successful answers.
- Explicit empty/loading/error/partial/ready UI states.
- Reject unsupported encrypted or image-only PDFs rather than mark them ready with no text.

## Release gates, not claimed results

Real login/upload/answer/delete flow; two-user isolation; hostile input and prompt-injection fixtures; queue crash/restart tests; provider timeouts/429 and interrupted SSE; labeled financial/citation benchmark; measured latency and usage; private storage; alerts and backup/restore drill.

Use 30-50 labeled questions initially and report the actual dataset, metrics and errors. Set quality/latency acceptance thresholds after baseline measurement, before release. No absolute hallucination, free-cost or speed guarantee.

## Not V1

Investment advice, autonomous external actions, OCR, cross-device saved memos or team collaboration unless separately implemented and verified.

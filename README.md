# HUNT — Trade Journal (EOD, Mongo edition)

## Feature flag
- `FEATURE_HUNT_TRADE_JOURNAL_ENABLED=true`

## Accounts (seeded)
- 9863032 — “Portfolio 1” — USD — ingest at **22:30 SAST**
- 9063957 — “Portfolio 2” — USD — ingest at **22:30 SAST**

## ENV (backend)
- `INTERNAL_JOB_TOKEN=&lt;strong-random&gt;`
- `MONGO_URL=&lt;protected&gt;`
- `TZ=Africa/Johannesburg`
- (later) `SFTP_HOST`, `SFTP_PORT`, `SFTP_USER`, `SFTP_KEY`, `SFTP_PASSPHRASE`, `SFTP_BASE`
- (later) `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_KEY`, `S3_SECRET`

## File patterns (strict)
- `balances_{accountId}_{YYYYMMDD}.csv`
- `positions_{accountId}_{YYYYMMDD}.csv`
- `orders_{accountId}_{YYYYMMDD}.csv`
- `executions_{accountId}_{YYYYMMDD}.csv`
- `cash_{accountId}_{YYYYMMDD}.csv`

## Seed EOD for local runs
Place CSVs here:
```
tests/seed_eod/
  9863032/
    2025-08-11/
      balances_9863032_20250811.csv
      positions_9863032_20250811.csv
      orders_9863032_20250811.csv
      executions_9863032_20250811.csv
      cash_9863032_20250811.csv
  9063957/
    2025-08-11/
      balances_9063957_20250811.csv
      positions_9063957_20250811.csv
      orders_9063957_20250811.csv
      executions_9063957_20250811.csv
      cash_9063957_20250811.csv
```

## Rule Engine (English only)
- Config file: `config/rules.yaml`  
- Example: see `config/rules.sample.yaml`
- Output: nightly chips stored on `positions_eod` (`computed_flags`) and in `position_flags_daily`

## Manual ingest (idempotent)
```bash
curl -X POST "$API/api/ingest/eod/9863032?date=2025-08-11" \
  -H "Authorization: Bearer $INTERNAL_JOB_TOKEN" \
  -H "X-Idempotency-Key: seed-9863032-20250811"
```

Use `?force=true` to bypass identical `artifact_hash`.

## Endpoints (read models use precomputes)
- `GET /api/journal/trades?accountId=&from=&to=&symbol=&tag=&strategy=&limit=&cursor=`
- `GET /api/journal/daily?accountId=&from=&to=`
- `GET /api/risk/overview?accountId=&from=&to=`
- `GET /api/calendar?accountId=&month=YYYY-MM`
- `GET /api/changes?accountId=&date=YYYY-MM-DD`
- `POST /api/journal/entry/upsert`
- `POST /api/journal/tags/apply`

## Cursor pagination (Trade Log)
- Sort: `filled_at DESC, _id DESC`
- Cursor: `base64(filled_at|_id)`
- Query:
  - `filled_at < last.filled_at OR (filled_at == last.filled_at AND _id < last._id)`
- Index: `{ account_id:1, filled_at:-1, _id:-1 }`

## Precomputed collections (nightly “materialized” docs)
- `trades_net_daily` — closed round trips per day
- `risk_equity_daily` — `{account_id, date, equity, drawdown}`
- `position_flags_daily` — computed chips per position/day
- `journal_daily_agg` — `{date, pnl, r, wins, losses, tagsHistogram}`

## Ingest + idempotency
- Row-level `raw_hash = sha256(normalized_line)`
- Batch `artifact_hash = sha256(sorted(file_hashes))`
- Uniques:
  - `orders (account_id, external_order_id)`
  - `executions (account_id, external_execution_id)`
  - `positions_eod (account_id, as_of, instrument_id)`
  - `balances_eod (account_id, as_of)`
  - `cash_events (account_id, posted_at, amount, description)`
  - `tags (name)`
  - `execution_tags (execution_id, tag_id)`
  - `ingest_jobs (account_id, as_of_date, artifact_hash)` (partial) + `(idempotency_key)`

## Round-trip builder (FIFO)
- Walk executions FIFO by instrument
- Handle partial fills/shorts
- Persist `trades_net` with: entry/exit times, avg prices, fees, `net_pnl`, resolved `risk_per_trade`, `r_multiple`

## Risk math
- Default `risk_per_trade`: `min(1% of latest net_equity, cap)`; allow per-strategy override
- Expectancy = mean(R), Payoff = `avg(win)/abs(avg(loss))`
- Max DD from `risk_equity_daily`

## “What changed today?”
Based on yesterday→today diffs:
- `openedPositions`, `closedPositions`
- `dividends` from `cash_events`
- `alerts` from first-seen flags in `position_flags_daily`

## Tests (CI gates)
- ETL validators + hashing
- Idempotency: re-run same batch → 0 new rows
- FIFO builder correctness (long, short, partial)
- Equity/DD math
- Cursor pagination determinism
- TZ schedule at 22:30 SAST
- API snapshots

## Final gaps to close (don’t skip)
- Instrument normalization: decide canonical instrument_id (EXCHANGE:SYMBOL). Create a lookup to merge duplicates (e.g., STX40 vs JSE:STX40).
- Currency handling: persist instrument currency and account currency; compute P&L in account currency only (no FX unless you add rates).
- Empty/day-missing files: ETL must tolerate missing one file (warn, don’t abort).
- File size limits & CSV injection: cap max bytes per file; trim dangerous leading = + - @ in string fields when storing raw.
- Monitoring: count metrics per ingest (rows upserted by file; warnings; duration). Expose a /metrics or structured logs.

## Definition of Done per milestone (tight)
- C/D: ETL upserts + precomputes + scheduler wired + manual ingest works end-to-end using seed pack.
- E: PF1/PF2/Combined header; chips rendering from position_flags_daily; KPI cards populated; calendar & risk charts read precomputes.
- F: All tests above green; PR includes runbook + screenshots + coverage.
import sys, os, _bootstrap
import sqlite3

if len(sys.argv) <= 1:
    sys.exit(1)

conn = sqlite3.connect(_bootstrap.project_resolver.resolved("Orchestration/db/runs.sqlite"))
c = conn.cursor()

c.execute(
f"""
    SELECT
        status,
        created_at,
        uuid,
        time((julianday(completed_at) - julianday(created_at)) * 86400, 'unixepoch') AS duration_hms
    FROM runs
    WHERE
        workflow LIKE '%{sys.argv[1]}%';
"""
)

rows = c.fetchall()

for row in rows:
    print(*row)

conn.close()

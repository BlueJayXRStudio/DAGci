import sys, os, _bootstrap
import sqlite3

conn = sqlite3.connect(_bootstrap.project_resolver.resolved("Orchestration/db/runs.sqlite"))
c = conn.cursor()

c.execute("SELECT * FROM runs")

rows = c.fetchall()

for row in rows:
    print(row)

conn.close()
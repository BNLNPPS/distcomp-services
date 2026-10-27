#!/usr/bin/env python3
"""Remove duplicate rows of a harvester worker from Harvester_Workers.

A worker with more than one row breaks every later update of it: updateWorkers
sets lastUpdate on all of its rows, the partitioned table moves them into the
day's partition, and they collide on that partition's key, so the harvester's
whole batch is rolled back (UniqueViolation, "failed to update workers with
database error in the PanDA server"). Each duplicated worker keeps the row with
the latest lastUpdate (then the latest endTime); the others are deleted by row
address, in one transaction. Dry run unless --apply.

Run on pandaserver01 as root, with the system Python, from /tmp/upgrade-<date>/
(UPGRADE.md, Rules 1):

    python3 dedupe_harvester_workers.py [--apply]
"""
import configparser
import sys

import psycopg2

cfg = configparser.ConfigParser(interpolation=None)
cfg.read('/etc/panda/panda_server.cfg')
c = cfg[next(s for s in cfg.sections() if cfg.has_option(s, 'dbhost'))]
schema = c.get('schemaPANDA')
apply = '--apply' in sys.argv

conn = psycopg2.connect(host=c['dbhost'], port=c.get('dbport', '5432'), user=c['dbuser'],
                        password=c['dbpasswd'], dbname=c['dbname'])
cur = conn.cursor()
cur.execute(f"SELECT harvesterid, workerid FROM {schema}.harvester_workers GROUP BY 1, 2 HAVING count(*) > 1 ORDER BY 1, 2")
dups = cur.fetchall()
plan = []
for harvester, worker in dups:
    cur.execute(f"SELECT tableoid::regclass::text, ctid::text, status, lastupdate, endtime, batchid "
                f"FROM {schema}.harvester_workers WHERE harvesterid=%s AND workerid=%s "
                f"ORDER BY lastupdate DESC NULLS LAST, endtime DESC NULLS LAST", [harvester, worker])
    rows = cur.fetchall()
    print(f'{harvester} worker {worker}: keep {rows[0][0]} {rows[0][1]} {rows[0][2]} {rows[0][3]}')
    for r in rows[1:]:
        print(f'    delete {r[0]} {r[1]} {r[2]} {r[3]}')
        plan.append((r[0], r[1]))
print(f'{len(dups)} duplicated workers, {len(plan)} rows to delete')
if not apply or not plan:
    conn.rollback()
    sys.exit(0)
for table, ctid in plan:
    # Through the parent table: the database account may not touch a partition directly.
    cur.execute(f"DELETE FROM {schema}.harvester_workers WHERE tableoid=%s::regclass AND ctid=%s::tid", [table, ctid])
    if cur.rowcount != 1:
        conn.rollback()
        sys.exit(f'ERROR: {table} {ctid} deleted {cur.rowcount} rows; rolled back')
cur.execute(f"SELECT count(*) FROM (SELECT 1 FROM {schema}.harvester_workers GROUP BY harvesterid, workerid HAVING count(*) > 1) d")
left = cur.fetchone()[0]
if left:
    conn.rollback()
    sys.exit(f'ERROR: {left} duplicated workers remain; rolled back')
conn.commit()
print(f'deleted {len(plan)} rows; no duplicated workers remain')

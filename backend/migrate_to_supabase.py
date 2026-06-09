#!/usr/bin/env python3
"""
migrate_to_supabase.py — one-off MySQL → Supabase (PostgreSQL) data migration

Prerequisites
-------------
1. Run `alembic upgrade head` against your Supabase DB first (creates empty tables).
2. Install deps:  pip install pymysql psycopg2-binary

Usage
-----
    python migrate_to_supabase.py \
        --mysql   "mysql+pymysql://user:pass@localhost:3306/eduai_copilot" \
        --pg      "postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres"

Both URLs can also be set via env vars MYSQL_URL / SUPABASE_URL instead of flags.

Notes
-----
- Use the DIRECT connection URL (port 5432), not the pooler (6543), for this script.
- The script temporarily disables FK checks on Postgres so tables can load in any order,
  then resets all serial sequences so future INSERTs don't collide with migrated IDs.
- Re-running is safe: every INSERT uses ON CONFLICT DO NOTHING.
"""

import argparse
import os
import sys
import time
from contextlib import contextmanager
from urllib.parse import urlparse, unquote

import pymysql
import pymysql.cursors
import psycopg2
import psycopg2.extras


# ── Ordered table list (parents before children; matters for FK validation) ──
# Tuple: (table_name, primary_key_column)
TABLES = [
    # Root — no foreign keys
    ("districts",                        "id"),
    ("users",                            "id"),
    # Level 2
    ("mandals",                          "id"),
    # Level 3
    ("schools",                          "id"),
    # Level 4 — reference schools + users
    ("teachers",                         "id"),
    ("students",                         "id"),
    # Level 5 — reference schools / teachers / students
    ("attendance",                       "id"),
    ("assessments",                      "id"),
    ("notifications",                    "id"),
    ("risk_alerts",                      "id"),
    ("risk_scans",                       "id"),
    ("ai_insights",                      "id"),
    ("generated_reports",                "id"),
    ("generated_letters",                "id"),
    ("generated_school_health_analyses", "id"),
    # Level 6 — reference assessments / students
    ("assessment_results",               "id"),
    ("student_ml_input",                 "id"),
    ("student_predictions",              "id"),
    ("tutor_concept_mastery",            "id"),
    ("tutor_knowledge_chunks",           "id"),
    # DEO / MEO copilot — reference users / districts / mandals / schools
    ("circular_summaries",               "id"),
    ("district_briefs",                  "id"),
    ("district_communications",          "id"),
    ("document_translations",            "id"),
    ("generated_meo_reports",            "id"),
    ("translations",                     "id"),
    ("teacher_rationalization",          "id"),
    ("teacher_rationalization_plans",    "id"),
    ("career_recommendations",           "id"),
]

BATCH_SIZE = 500  # rows per INSERT batch


# ── Connection helpers ────────────────────────────────────────────────────────

@contextmanager
def mysql_connection(url: str):
    p = urlparse(url.replace("mysql+pymysql://", "mysql://"))
    conn = pymysql.connect(
        host=p.hostname,
        port=p.port or 3306,
        user=p.username,
        password=unquote(p.password or ""),
        database=p.path.lstrip("/"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def pg_connection(url: str):
    conn = psycopg2.connect(url)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.close()


# ── Per-table migration ────────────────────────────────────────────────────────

def get_boolean_columns(pg_cur, table: str) -> set:
    """Return the set of column names that PostgreSQL typed as boolean."""
    pg_cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = %s
          AND data_type    = 'boolean'
        """,
        (table,),
    )
    return {row[0] for row in pg_cur.fetchall()}


def migrate_table(table: str, pk: str, my_cur, pg_cur, pg_conn) -> int:
    # Check row count in MySQL
    my_cur.execute(f"SELECT COUNT(*) AS cnt FROM `{table}`")
    total = my_cur.fetchone()["cnt"]
    if total == 0:
        print(f"  {table}: (empty)")
        return 0

    # Discover columns from MySQL
    my_cur.execute(f"SHOW COLUMNS FROM `{table}`")
    columns = [row["Field"] for row in my_cur.fetchall()]
    mysql_cols = ", ".join(f"`{c}`" for c in columns)
    pg_cols    = ", ".join(f'"{c}"' for c in columns)

    # MySQL stores booleans as TINYINT(1); PostgreSQL rejects plain 0/1 for
    # boolean columns — cast those values to Python bool before inserting.
    bool_cols = get_boolean_columns(pg_cur, table)

    inserted = 0
    offset = 0

    while offset < total:
        my_cur.execute(
            f"SELECT {mysql_cols} FROM `{table}` "
            f"ORDER BY `{pk}` LIMIT {BATCH_SIZE} OFFSET {offset}"
        )
        rows = my_cur.fetchall()
        if not rows:
            break

        values = [
            tuple(
                bool(row[c]) if (c in bool_cols and row[c] is not None) else row[c]
                for c in columns
            )
            for row in rows
        ]
        sql = (
            f'INSERT INTO "{table}" ({pg_cols}) VALUES %s '
            f'ON CONFLICT DO NOTHING'
        )
        psycopg2.extras.execute_values(pg_cur, sql, values, page_size=BATCH_SIZE)
        pg_conn.commit()

        inserted += len(rows)
        offset   += BATCH_SIZE
        print(f"  {table}: {inserted}/{total}", end="\r", flush=True)

    print(f"  {table}: {inserted}/{total} rows  ")
    return inserted


# ── Sequence reset ─────────────────────────────────────────────────────────────

def reset_sequences(pg_cur, pg_conn):
    """Advance every serial sequence to max(id) so new rows don't collide."""
    print("\nResetting sequences...")
    for table, pk in TABLES:
        try:
            pg_cur.execute(
                f"SELECT setval("
                f"  pg_get_serial_sequence('{table}', '{pk}'),"
                f"  COALESCE((SELECT MAX(\"{pk}\") FROM \"{table}\"), 0) + 1,"
                f"  false"
                f")"
            )
        except Exception as e:
            # Table may not have a sequence (e.g. uuid PK) — safe to skip
            pg_conn.rollback()
            print(f"  skipped {table}.{pk}: {e}")
            continue
    pg_conn.commit()
    print("  Done.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Migrate MySQL → Supabase PostgreSQL")
    parser.add_argument("--mysql", default=os.getenv("MYSQL_URL"),
                        help="MySQL URL: mysql+pymysql://user:pass@host:port/db")
    parser.add_argument("--pg",    default=os.getenv("SUPABASE_URL"),
                        help="Supabase PostgreSQL URL: postgresql://user:pass@host:5432/postgres")
    args = parser.parse_args()

    if not args.mysql or not args.pg:
        print(
            "ERROR: supply --mysql and --pg connection URLs\n"
            "       or set MYSQL_URL / SUPABASE_URL environment variables."
        )
        sys.exit(1)

    print(f"Source : {args.mysql.split('@')[-1]}")   # hide credentials in log
    print(f"Target : {args.pg.split('@')[-1]}")
    print()

    total_rows = 0
    skipped    = []
    start      = time.time()

    with mysql_connection(args.mysql) as my, pg_connection(args.pg) as pg:
        my_cur = my.cursor()
        pg_cur = pg.cursor()

        # Disable FK constraint enforcement so tables can load without ordering issues
        pg_cur.execute("SET session_replication_role = 'replica'")
        pg.commit()

        for table, pk in TABLES:
            try:
                n = migrate_table(table, pk, my_cur, pg_cur, pg)
                total_rows += n
            except Exception as exc:
                pg.rollback()
                skipped.append(table)
                print(f"\n  ERROR on {table}: {exc}")
                print("  Skipping and continuing...\n")

        # Re-enable FK checks
        pg_cur.execute("SET session_replication_role = 'origin'")
        pg.commit()

        reset_sequences(pg_cur, pg)

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"Migration complete: {total_rows:,} rows in {elapsed:.1f}s")
    if skipped:
        print(f"Tables skipped due to errors: {', '.join(skipped)}")
    else:
        print("All tables migrated successfully.")
    print(f"{'='*50}")
    print("\nNext steps:")
    print("  1. Update .env: swap DATABASE_URL to the Supabase postgresql+asyncpg:// URL")
    print("  2. Restart the backend and smoke-test login + dashboards")
    print("  3. Once confirmed, remove aiomysql / pymysql from requirements.txt")


if __name__ == "__main__":
    main()

"""Run every SQL file in sql/reports/ and print the results."""

import sys

import duckdb

from currency_exchange.config import PROJECT_ROOT, load_settings

REPORTS_DIR = PROJECT_ROOT / "sql" / "reports"


def main():
    settings = load_settings()
    if not settings.database.exists():
        print(f"Database not found: {settings.database}. Run fx-pipeline first.")
        sys.exit(1)

    con = duckdb.connect(str(settings.database), read_only=True)
    try:
        for sql_file in sorted(REPORTS_DIR.glob("*.sql")):
            sql = sql_file.read_text(encoding="utf-8")
            title = (
                sql.splitlines()[0].lstrip("- ").strip()
            )  # first comment line = title
            print(f"\n{title}")
            con.sql(sql).show(max_rows=40)
    finally:
        con.close()


if __name__ == "__main__":
    main()

import os
import psycopg2

# Path to your .sql file (can contain any SQL: tables, views, policies, RLS, grants)
SQL_PATH = "schema.sql"


def run_sql_file(db_url: str, path: str):
    """
    Reads a .sql file and executes statements one by one.
    A statement is detected when a line ends with ';'.
    This is helpful for debugging which specific block fails.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"SQL file not found: {path}")

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    print(f"Executing SQL file: {path}\n")

    statement_buffer = ""

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            # Accumulate lines of SQL statement
            statement_buffer += line

            # When ';' is detected at end of line → execute the statement
            if line.strip().endswith(";"):
                sql_to_run = statement_buffer.strip()

                try:
                    cur.execute(sql_to_run)
                    print(f"✔ OK: {sql_to_run[:60]}...")
                except Exception as e:
                    print("\n✖ ERROR executing statement:")
                    print(sql_to_run)
                    print(f"→ {e}\n")

                # Reset buffer for the next statement
                statement_buffer = ""

    cur.close()
    conn.close()
    print("\nSQL execution completed.\n")


if __name__ == "__main__":
    db_url = os.getenv("SUPABASE_DB_URL")

    if not db_url:
        print("ERROR: SUPABASE_DB_URL environment variable is missing.")
        exit(1)

    run_sql_file(db_url, SQL_PATH)


import pandas as pd
from sqlalchemy import create_engine, text, NVARCHAR
import os
import time
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# =========================
# CONFIGURATION
# =========================
BASE_PATH = r"C:\Users\sw\Desktop\dforDc\cricket"
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = "CricketStats"

CONN_STR = f"mssql+pyodbc://@{DB_SERVER}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"


# =========================
# DATABASE SETUP
# =========================
def create_database():
    master_conn_str = f"mssql+pyodbc://@{DB_SERVER}/master?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    engine = create_engine(master_conn_str)

    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT name FROM sys.databases WHERE name = '{DB_NAME}'"))
        exists = result.fetchone()

        if not exists:
            conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            print(f"Database '{DB_NAME}' created.")
        else:
            print(f"Database '{DB_NAME}' already exists.")


# =========================
# CLEANING
# =========================
def clean_columns(df):
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # Replace spaces with underscores
    df.columns = df.columns.str.replace(' ', '_', regex=False)
    # Remove special characters like (, ), /
    df.columns = df.columns.str.replace(r'[^\w]', '', regex=True)
    return df

def load_file(csv_path, table_name, engine, format_name=None, if_exists='replace'):
    start_time = time.time()

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df = clean_columns(df)

    # Force NVARCHAR(4000) on all string columns
    str_cols = df.select_dtypes(include=['object', 'str']).columns
    dtype_dict = {col: NVARCHAR(4000) for col in str_cols}

    df.to_sql(
        table_name,
        con=engine,
        if_exists=if_exists,
        index=False,
        chunksize=500,
        dtype=dtype_dict
    )

    elapsed = time.time() - start_time
    rows = len(df)
    print(f"Loaded {os.path.basename(csv_path)} → {table_name} | Rows: {rows} | Time: {elapsed:.2f}s")
    return rows, elapsed

# =========================
# MAIN
# =========================
def main():
    total_start = time.time()
    total_rows = 0

    create_database()

    #engine = create_engine(CONN_STR, fast_executemany=True)

    # To this
    engine = create_engine(
        CONN_STR,
        fast_executemany=False  # ← disable this
    )

    # Matches — separate per format
    load_file(f"{BASE_PATH}/odi/odi_Matches_Data.csv", "ODI_Matches", engine)
    load_file(f"{BASE_PATH}/t20/t20i_Matches_Data.csv", "T20_Matches", engine)
    load_file(f"{BASE_PATH}/test/test_Matches_Data.csv", "TEST_Matches", engine)

    # Batting — separate per format
    load_file(f"{BASE_PATH}/odi/odi_Batting_Card.csv", "ODI_Batting", engine)
    load_file(f"{BASE_PATH}/t20/t20i_Batting_Card.csv", "T20_Batting", engine)
    load_file(f"{BASE_PATH}/test/test_Batting_Card.csv", "TEST_Batting", engine)

    # Bowling — separate per format
    load_file(f"{BASE_PATH}/odi/odi_Bowling_Card.csv", "ODI_Bowling", engine)
    load_file(f"{BASE_PATH}/t20/t20i_Bowling_Card.csv", "T20_Bowling", engine)
    load_file(f"{BASE_PATH}/test/test_Bowling_Card.csv", "TEST_Bowling", engine)

    # Partnerships — separate per format
    load_file(f"{BASE_PATH}/odi/odi_Partnership_Card.csv", "ODI_Partnerships", engine)
    load_file(f"{BASE_PATH}/t20/t20i_Partnership_Card.csv", "T20_Partnerships", engine)
    load_file(f"{BASE_PATH}/test/test_Partnership_Card.csv", "TEST_Partnerships", engine)

    # FallOfWickets — separate per format
    load_file(f"{BASE_PATH}/odi/odi_Fow_Card.csv", "ODI_FallOfWickets", engine)
    load_file(f"{BASE_PATH}/t20/t20i_Fow_Card.csv", "T20_FallOfWickets", engine)
    load_file(f"{BASE_PATH}/test/test_Fow_Card.csv", "TEST_FallOfWickets", engine)

    # Players — shared
    load_file(f"{BASE_PATH}/odi/players_info.csv", "Players", engine)

    total_time = time.time() - total_start

    print("\n=== LOAD COMPLETE ===")
    print(f"Total Rows Loaded: {total_rows}")
    print(f"Total Time: {total_time:.2f}s")


if __name__ == "__main__":
    main()
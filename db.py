import os
import time
import warnings

from dotenv import load_dotenv
from sqlalchemy import create_engine, text,exc,inspect
from logger import log_sql, log_execution_time, log_error, logger
from config import QUERY_TIMEOUT_SECONDS, MAX_ROWS_RETURNED

warnings.filterwarnings("ignore", category=exc.SAWarning)

# Load environment variables
load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")

# Create connection string
connection_string = (
    f"mssql+pyodbc://@{DB_SERVER}/{DB_NAME}"
    "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

# Create SQLAlchemy engine
engine = create_engine(connection_string)

def get_schema() -> str:
    """
    Retrieves the complete database schema with tables, columns, and relationships.
    
    Uses SQLAlchemy's inspector to extract schema metadata from the database,
    formatting it as human-readable text for use in AI prompts. This provides
    Claude with the necessary context to generate accurate SQL queries.
    
    Returns:
        str: A formatted string containing tables, columns with types, primary keys,
            and foreign key relationships.
        
    Raises:
        Exception: If database inspection fails or connection is unavailable.
    """
    inspector = inspect(engine)

    output = []

    # Iterate through all tables to build comprehensive schema documentation
    tables = inspector.get_table_names()

    for table in tables:
        output.append(f"{table}:")

        # Extract all columns with their data types for Claude to understand schema structure
        columns = inspector.get_columns(table)
        for col in columns:
            col_name = col["name"]
            col_type = str(col["type"])
            output.append(f"  - {col_name} ({col_type})")

        # Include primary key constraints so Claude knows which columns uniquely identify records
        pk = inspector.get_pk_constraint(table)
        pk_cols = pk.get("constrained_columns", [])
        if pk_cols:
            output.append(f"  Primary Key: {', '.join(pk_cols)}")

        # Include foreign key relationships so Claude understands how tables join together
        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            local_cols = fk.get("constrained_columns", [])
            ref_table = fk.get("referred_table")
            ref_cols = fk.get("referred_columns", [])

            for lc, rc in zip(local_cols, ref_cols):
                output.append(f"  FK: {table}.{lc} -> {ref_table}.{rc}")

        output.append("")  # blank line between tables for readability

    return "\n".join(output)

def run_query(sql: str, timeout: int = 10):
    """
    Executes a SQL query against the database with safety checks and performance monitoring.
    
    Connects to the database, executes the provided SQL query, and returns results as
    a list of dictionaries. Includes timeout checks to prevent long-running queries from
    consuming resources, and row truncation to manage memory usage.
    
    Args:
        sql (str): The SQL query to execute.
        timeout (int, optional): Timeout threshold in seconds. Defaults to 10.
        
    Returns:
        dict: A dictionary containing:
            - rows (list[dict]): Query results as list of dictionaries.
            - execution_time (float): Time taken to execute query in seconds.
            - row_count (int): Total number of rows before truncation.
        
    Raises:
        TimeoutError: If query execution exceeds QUERY_TIMEOUT_SECONDS.
        Exception: If SQL execution fails or database connection is unavailable.
    """
    start_time = time.time()

    try:
        log_sql(sql)

        with engine.connect() as conn:
            result = conn.execute(text(sql))
            # Convert SQLAlchemy Row objects to dictionaries for easier consumption
            rows = [dict(row._mapping) for row in result]

        execution_time = time.time() - start_time

        # Enforce timeout to prevent resource exhaustion from slow queries
        if execution_time > QUERY_TIMEOUT_SECONDS:
            raise TimeoutError(f"Query exceeded {QUERY_TIMEOUT_SECONDS} seconds")

        row_count = len(rows)

        # Truncate large result sets to prevent memory issues and UI rendering problems
        if row_count > MAX_ROWS_RETURNED:
            logger.warning(f"Result truncated from {row_count} to {MAX_ROWS_RETURNED} rows")
            rows = rows[:MAX_ROWS_RETURNED]

        log_execution_time("Query execution", execution_time)

        return {
            "rows": rows,
            "execution_time": execution_time,
            "row_count": row_count
        }

    except Exception as e:
        log_error(str(e))
        raise


if __name__ == "__main__":
    schema = get_schema()
    logger.info(f"Schema loaded:\n{schema}")

    # Test run_query
    results = run_query("SELECT TOP 5 CustomerID, CompanyName, Country FROM Customers")
    
    rows = results["rows"]
    for row in rows:
        logger.info(row)
    
    logger.info(f"Rows returned: {results['row_count']}")
    logger.info(f"Query execution time: {results['execution_time']} seconds")
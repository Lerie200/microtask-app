import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Open a new connection to Postgres. Caller is responsible for closing it."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def get_dict_cursor(conn):
    """Return a cursor that yields rows as dicts instead of tuples."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

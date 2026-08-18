import sqlite3
import os


def create_connection(db_name="costs.db"): #make a connection to the database
    conn = sqlite3.connect(db_name)
    return conn


def create_table(conn): #create the costs table if it doesn't exist
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project TEXT NOT NULL,
            service TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()


def insert_row(conn, project, service, amount, date): #insert a single row into the costs table
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO costs (project, service, amount, date)
        VALUES (?, ?, ?, ?)
    """, (project, service, amount, date))
    conn.commit()


def insert_many(conn, rows): #insert multiple rows into the costs table
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO costs (project, service, amount, date)
        VALUES (:project, :service, :amount, :date)
    """, rows)
    conn.commit()


def select_all(conn): #return all rows from the costs table
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM costs")
    return cursor.fetchall()


def select_where(conn, column, value): #return rows from the costs table where a specific column matches a value
    cursor = conn.cursor()
    query = f"SELECT * FROM costs WHERE {column} = ?"
    cursor.execute(query, (value,))
    return cursor.fetchall()


def group_by_project(conn): #return the total amount spent on each project, ordered by total amount descending
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project, SUM(amount) as total_amount
        FROM costs
        GROUP BY project
        ORDER BY total_amount DESC
    """)
    return cursor.fetchall()
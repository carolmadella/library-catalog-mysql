"""
library_catalog.py
Library Catalog - a command-line program that stores books, authors,
members, and loans in a MySQL relational database.

CSE 310 - SQL Relational Databases module
Author: Carolina Madella
"""

import getpass
import os

import mysql.connector

# File that holds the CREATE DATABASE and CREATE TABLE commands
SCHEMA_FILE = "schema.sql"


# ---------------------------------------------------------------
# Database connection and setup
# ---------------------------------------------------------------

def get_password():
    """Use the MYSQL_PASSWORD environment variable if it is set,
    otherwise ask for the password. It is never stored in the code."""
    return os.environ.get("MYSQL_PASSWORD") or getpass.getpass("MySQL root password: ")


def connect_to_server():
    """Connect to the MySQL server running on this computer."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=get_password(),
    )


def read_sql_commands(filename):
    """Read a .sql file and return a list of its SQL commands.
    Comment lines (starting with --) are skipped, and the
    commands are separated by semicolons."""
    with open(filename, encoding="utf-8") as file:
        lines = [line for line in file if not line.strip().startswith("--")]
    text = "".join(lines)
    return [command.strip() for command in text.split(";") if command.strip()]


def create_tables(connection):
    """Run every command in schema.sql to create the database and tables."""
    cursor = connection.cursor()
    for command in read_sql_commands(SCHEMA_FILE):
        cursor.execute(command)
    connection.commit()
    cursor.close()


def list_tables(connection):
    """Return the names of the tables in the library database."""
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def main():
    """Connect, make sure the tables exist, and show them."""
    connection = connect_to_server()
    create_tables(connection)
    print("Connected to MySQL. Tables in the library_catalog database:")
    for table in list_tables(connection):
        print(" -", table)
    connection.close()


if __name__ == "__main__":
    main()
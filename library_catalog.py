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


# ---------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------

def ask_text(prompt, required=True):
    """Ask for text. If the field is required, keep asking until it is not empty."""
    while True:
        answer = input(prompt).strip()
        if answer or not required:
            return answer
        print("  This field is required. Please try again.")


def ask_number(prompt, minimum, maximum, allow_blank=False):
    """Ask for a whole number between minimum and maximum.
    If allow_blank is True, pressing Enter returns None."""
    while True:
        answer = input(prompt).strip()
        if answer == "" and allow_blank:
            return None
        if answer.isdigit() and minimum <= int(answer) <= maximum:
            return int(answer)
        print(f"  Please enter a number from {minimum} to {maximum}.")


# ---------------------------------------------------------------
# Authors
# ---------------------------------------------------------------

def get_authors(connection):
    """SELECT: return every author as (author_id, first_name, last_name),
    sorted by last name."""
    cursor = connection.cursor()
    cursor.execute(
        "SELECT author_id, first_name, last_name FROM authors "
        "ORDER BY last_name, first_name"
    )
    authors = cursor.fetchall()
    cursor.close()
    return authors


def add_author(connection):
    """INSERT: add a new author and return the new author's ID."""
    first_name = ask_text("Author first name: ")
    last_name = ask_text("Author last name: ")
    cursor = connection.cursor()
    # %s placeholders let the connector insert the values safely
    cursor.execute(
        "INSERT INTO authors (first_name, last_name) VALUES (%s, %s)",
        (first_name, last_name),
    )
    connection.commit()
    new_id = cursor.lastrowid   # the ID MySQL just created with AUTO_INCREMENT
    cursor.close()
    print(f"Author {first_name} {last_name} was added.")
    return new_id


def choose_author(connection):
    """Show the authors and let the user pick one by number,
    or type 0 to add a new author. Returns the chosen author_id."""
    authors = get_authors(connection)
    print("\nAuthors:")
    for number, (_, first_name, last_name) in enumerate(authors, start=1):
        print(f"  {number}. {first_name} {last_name}")
    print("  0. Add a new author")
    choice = ask_number("Choose the author: ", 0, len(authors))
    if choice == 0:
        return add_author(connection)
    return authors[choice - 1][0]


# ---------------------------------------------------------------
# Books
# ---------------------------------------------------------------

# Every book list uses this JOIN so it can show the author's name
# instead of just the author_id number
BOOK_QUERY = (
    "SELECT b.book_id, b.title, a.first_name, a.last_name, "
    "b.genre, b.year_published, b.copies_available "
    "FROM books AS b "
    "JOIN authors AS a ON b.author_id = a.author_id"
)


def add_book(connection):
    """INSERT: ask for the book details and save a new row in 'books'."""
    print("\n--- Add a Book ---")
    title = ask_text("Title: ")
    author_id = choose_author(connection)
    genre = ask_text("Genre (optional): ", required=False) or None
    year = ask_number("Year published (optional): ", 0, 2100, allow_blank=True)
    copies = ask_number("Copies available (Enter = 1): ", 0, 999, allow_blank=True)
    if copies is None:
        copies = 1

    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO books (title, author_id, genre, year_published, copies_available) "
        "VALUES (%s, %s, %s, %s, %s)",
        (title, author_id, genre, year, copies),
    )
    connection.commit()
    print(f"'{title}' was added (book ID {cursor.lastrowid}).")
    cursor.close()


def display_books(rows):
    """Print a table of books from the rows returned by BOOK_QUERY."""
    if not rows:
        print("No books found.")
        return
    print(f"\n{'ID':<5}{'Title':<32}{'Author':<24}{'Genre':<14}{'Year':<6}Copies")
    print("-" * 87)
    for book_id, title, first_name, last_name, genre, year, copies in rows:
        author = f"{first_name} {last_name}"
        print(f"{book_id:<5}{title[:30]:<32}{author[:22]:<24}"
              f"{(genre or '-')[:12]:<14}{str(year or '-'):<6}{copies}")


def list_books(connection):
    """SELECT: show every book with its author, sorted by title."""
    print("\n--- All Books ---")
    cursor = connection.cursor()
    cursor.execute(BOOK_QUERY + " ORDER BY b.title")
    display_books(cursor.fetchall())
    cursor.close()


def search_books(connection):
    """SELECT with WHERE: find books by title, author, or genre.
    LIKE with % matches the search text anywhere in the value."""
    print("\n--- Search Books ---")
    print("1. By title")
    print("2. By author")
    print("3. By genre")
    choice = ask_number("Search by: ", 1, 3)
    text = ask_text("Search for: ")
    pattern = f"%{text}%"

    if choice == 1:
        where = " WHERE b.title LIKE %s"
        values = (pattern,)
    elif choice == 2:
        where = " WHERE a.first_name LIKE %s OR a.last_name LIKE %s"
        values = (pattern, pattern)
    else:
        where = " WHERE b.genre LIKE %s"
        values = (pattern,)

    cursor = connection.cursor()
    cursor.execute(BOOK_QUERY + where + " ORDER BY b.title", values)
    display_books(cursor.fetchall())
    cursor.close()


# ---------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------

def show_menu():
    """Print the main menu options."""
    print("\n===== LIBRARY CATALOG =====")
    print("1. Add a book")
    print("2. List all books")
    print("3. Search books")
    print("0. Exit")


def main():
    """Connect, make sure the tables exist, then run the menu until the user exits."""
    connection = connect_to_server()
    create_tables(connection)
    print("Connected to the library_catalog database.")

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_book(connection)
        elif choice == "2":
            list_books(connection)
        elif choice == "3":
            search_books(connection)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from the menu.")

    connection.close()


if __name__ == "__main__":
    main()
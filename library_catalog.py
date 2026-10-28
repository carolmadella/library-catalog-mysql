"""
library_catalog.py
Library Catalog - a command-line program that stores books, authors,
genres, members, and loans in a MySQL relational database.

CSE 310 - SQL Relational Databases module
Author: Carolina Madella
"""

import getpass
import os
from datetime import date, datetime, timedelta

import mysql.connector
from mysql.connector import errorcode

# File that holds the CREATE DATABASE and CREATE TABLE commands
SCHEMA_FILE = "schema.sql"

# Library rules
LOAN_DAYS = 14             # a book is due 14 days after checkout
LATE_FEE_PER_DAY = 0.25    # fee charged for each day a book is late
DATE_FORMAT = "%Y-%m-%d"


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


def fetch_all(connection, sql, values=()):
    """Run a SELECT command and return all of its rows."""
    cursor = connection.cursor()
    cursor.execute(sql, values)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def run_change(connection, sql, values=()):
    """Run an INSERT, UPDATE, or DELETE command, save it with commit(),
    and return the new row's ID (useful after an INSERT)."""
    cursor = connection.cursor()
    cursor.execute(sql, values)
    connection.commit()
    new_id = cursor.lastrowid
    cursor.close()
    return new_id


# ---------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------

def ask_text(prompt, required=True, max_length=None):
    """Ask for text. If the field is required, keep asking until it is not empty.
    max_length matches the column size in schema.sql (for example VARCHAR(50)),
    so the user gets a clear message instead of a database error."""
    while True:
        answer = input(prompt).strip()
        if not answer and required:
            print("  This field is required. Please try again.")
        elif max_length and len(answer) > max_length:
            print(f"  Please use {max_length} characters or fewer.")
        else:
            return answer


def ask_email(prompt):
    """Ask for an email address and do a simple format check:
    one @, something before it, and a dot in the part after it."""
    while True:
        email = ask_text(prompt, max_length=100).lower()
        name, at_sign, domain = email.partition("@")
        if name and at_sign and "." in domain and "@" not in domain and " " not in email:
            return email
        print("  Please enter a valid email address (example: name@example.com).")


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


def ask_date(prompt, default):
    """Ask for a date in YYYY-MM-DD format. Pressing Enter uses the default."""
    while True:
        answer = input(f"{prompt} (YYYY-MM-DD, Enter = {default}): ").strip()
        if answer == "":
            return default
        try:
            return datetime.strptime(answer, DATE_FORMAT).date()
        except ValueError:
            print("  Please use the format YYYY-MM-DD (example: 2026-11-15).")


def choose_id(prompt, valid_ids):
    """Ask for one of the IDs shown in a list. Pressing Enter cancels (returns None)."""
    while True:
        answer = input(f"{prompt} (or press Enter to cancel): ").strip()
        if answer == "":
            return None
        if answer.isdigit() and int(answer) in valid_ids:
            return int(answer)
        print("  Please enter one of the IDs shown in the list.")


def confirm(question):
    """Ask a yes/no question and return True only for 'y'."""
    return input(f"{question} (y/n): ").strip().lower() == "y"


# ---------------------------------------------------------------
# Authors
# ---------------------------------------------------------------

def get_authors(connection):
    """SELECT: return every author as (author_id, first_name, last_name)."""
    return fetch_all(
        connection,
        "SELECT author_id, first_name, last_name FROM authors "
        "ORDER BY last_name, first_name",
    )


def add_author(connection):
    """INSERT: add a new author and return the new author's ID."""
    first_name = ask_text("Author first name: ", max_length=50)
    last_name = ask_text("Author last name: ", max_length=50)
    # %s placeholders let the connector insert the values safely
    new_id = run_change(
        connection,
        "INSERT INTO authors (first_name, last_name) VALUES (%s, %s)",
        (first_name, last_name),
    )
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
# Genres
# ---------------------------------------------------------------

def add_genre(connection):
    """INSERT: add a new genre and return its ID. If the genre already
    exists, the UNIQUE rule blocks the duplicate and we reuse the existing one."""
    name = ask_text("New genre name: ", max_length=50).title()
    try:
        new_id = run_change(connection, "INSERT INTO genres (name) VALUES (%s)", (name,))
        print(f"Genre '{name}' was added.")
        return new_id
    except mysql.connector.IntegrityError:
        print(f"'{name}' already exists, so the existing genre was used.")
        return fetch_all(
            connection, "SELECT genre_id FROM genres WHERE name = %s", (name,)
        )[0][0]


def choose_genre(connection):
    """Show the genres and let the user pick one by number, type 0 to add
    a new genre, or press Enter for no genre. Returns a genre_id or None."""
    genres = fetch_all(connection, "SELECT genre_id, name FROM genres ORDER BY name")
    print("\nGenres:")
    for number, (_, name) in enumerate(genres, start=1):
        print(f"  {number}. {name}")
    print("  0. Add a new genre")
    choice = ask_number("Choose the genre (Enter = none): ", 0, len(genres), allow_blank=True)
    if choice is None:
        return None
    if choice == 0:
        return add_genre(connection)
    return genres[choice - 1][0]


# ---------------------------------------------------------------
# Books
# ---------------------------------------------------------------

# Every book list uses these JOINs so it can show the author's and genre's
# names instead of just ID numbers. LEFT JOIN keeps books that have no genre.
BOOK_QUERY = (
    "SELECT b.book_id, b.title, a.first_name, a.last_name, "
    "g.name, b.year_published, b.copies_available "
    "FROM books AS b "
    "JOIN authors AS a ON b.author_id = a.author_id "
    "LEFT JOIN genres AS g ON b.genre_id = g.genre_id"
)


def add_book(connection):
    """INSERT: ask for the book details and save a new row in 'books'."""
    print("\n--- Add a Book ---")
    title = ask_text("Title: ", max_length=200)
    author_id = choose_author(connection)
    genre_id = choose_genre(connection)
    year = ask_number("Year published (optional): ", 0, 2100, allow_blank=True)
    copies = ask_number("Copies available (Enter = 1): ", 0, 999, allow_blank=True)
    if copies is None:
        copies = 1

    new_id = run_change(
        connection,
        "INSERT INTO books (title, author_id, genre_id, year_published, copies_available) "
        "VALUES (%s, %s, %s, %s, %s)",
        (title, author_id, genre_id, year, copies),
    )
    print(f"'{title}' was added (book ID {new_id}).")


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
    """SELECT: show every book with its author, sorted by title.
    Returns the rows so other features can let the user pick a book."""
    rows = fetch_all(connection, BOOK_QUERY + " ORDER BY b.title")
    display_books(rows)
    return rows


def search_books(connection):
    """SELECT with WHERE: find books by title, author, or genre.
    LIKE with % matches the search text anywhere in the value."""
    print("\n--- Search Books ---")
    print("1. By title")
    print("2. By author")
    print("3. By genre")
    choice = ask_number("Search by: ", 1, 3)
    pattern = f"%{ask_text('Search for: ')}%"

    if choice == 1:
        where = " WHERE b.title LIKE %s"
        values = (pattern,)
    elif choice == 2:
        where = " WHERE a.first_name LIKE %s OR a.last_name LIKE %s"
        values = (pattern, pattern)
    else:
        where = " WHERE g.name LIKE %s"
        values = (pattern,)

    display_books(fetch_all(connection, BOOK_QUERY + where + " ORDER BY b.title", values))


def choose_book(connection):
    """List all books and let the user pick one by its ID."""
    rows = list_books(connection)
    if not rows:
        return None
    return choose_id("\nEnter the book ID", [row[0] for row in rows])


def update_book(connection):
    """UPDATE: change the details of a book. Pressing Enter keeps the current value."""
    print("\n--- Update a Book ---")
    book_id = choose_book(connection)
    if book_id is None:
        return
    title, genre, year, copies = fetch_all(
        connection,
        "SELECT b.title, g.name, b.year_published, b.copies_available "
        "FROM books AS b LEFT JOIN genres AS g ON b.genre_id = g.genre_id "
        "WHERE b.book_id = %s",
        (book_id,),
    )[0]
    print("\nPress Enter to keep the current value shown in [brackets].")

    # Only the fields the user changes go into this dictionary
    changes = {}
    new_title = ask_text(f"Title [{title}]: ", required=False, max_length=200)
    if new_title:
        changes["title"] = new_title
    if confirm("Change the author?"):
        changes["author_id"] = choose_author(connection)
    if confirm(f"Change the genre [{genre or '-'}]?"):
        changes["genre_id"] = choose_genre(connection)
    new_year = ask_number(f"Year published [{year or '-'}]: ", 0, 2100, allow_blank=True)
    if new_year is not None:
        changes["year_published"] = new_year
    new_copies = ask_number(f"Copies available [{copies}]: ", 0, 999, allow_blank=True)
    if new_copies is not None:
        changes["copies_available"] = new_copies

    if not changes:
        print("No changes made.")
        return
    # Builds, for example: UPDATE books SET genre_id = %s, year_published = %s WHERE book_id = %s
    # The column names come from this code; the user's values are sent separately.
    set_clause = ", ".join(f"{column} = %s" for column in changes)
    run_change(
        connection,
        f"UPDATE books SET {set_clause} WHERE book_id = %s",
        (*changes.values(), book_id),
    )
    print(f"Book updated: {', '.join(changes)} changed.")


def delete_book(connection):
    """DELETE: remove a book, but only if it has never been loaned out."""
    print("\n--- Delete a Book ---")
    book_id = choose_book(connection)
    if book_id is None:
        return
    # The loans table points to books, so MySQL would block this delete.
    # We check first and explain why instead of showing an error.
    loan_count = fetch_all(
        connection, "SELECT COUNT(*) FROM loans WHERE book_id = %s", (book_id,)
    )[0][0]
    if loan_count > 0:
        print(f"This book can't be deleted because it has {loan_count} loan record(s).")
        return
    if not confirm("Are you sure you want to delete this book?"):
        print("Delete cancelled.")
        return
    run_change(connection, "DELETE FROM books WHERE book_id = %s", (book_id,))
    print("Book deleted.")


# ---------------------------------------------------------------
# Members
# ---------------------------------------------------------------

def add_member(connection):
    """INSERT: add a library member. The email must be unique, so if it is
    already used, the user is asked for a different one."""
    print("\n--- Add a Member ---")
    first_name = ask_text("First name: ", max_length=50)
    last_name = ask_text("Last name: ", max_length=50)
    while True:
        email = ask_email("Email: ")
        # SELECT: check whether another member already uses this email
        taken = fetch_all(
            connection, "SELECT COUNT(*) FROM members WHERE email = %s", (email,)
        )[0][0]
        if not taken:
            break
        print("  That email is already used by another member. Please enter a different one.")
    try:
        new_id = run_change(
            connection,
            "INSERT INTO members (first_name, last_name, email, join_date) "
            "VALUES (%s, %s, %s, %s)",
            (first_name, last_name, email, date.today()),
        )
        print(f"{first_name} {last_name} is now a member (member ID {new_id}).")
    except mysql.connector.IntegrityError:
        # Safety net: the UNIQUE rule on email still blocks duplicates
        print("A member with that email already exists.")

def list_members(connection):
    """SELECT: show every member, sorted by last name. Returns the rows."""
    rows = fetch_all(
        connection,
        "SELECT member_id, first_name, last_name, email, join_date FROM members "
        "ORDER BY last_name, first_name",
    )
    if not rows:
        print("No members yet.")
        return rows
    print(f"\n{'ID':<5}{'Name':<26}{'Email':<34}Joined")
    print("-" * 75)
    for member_id, first_name, last_name, email, join_date in rows:
        name = f"{first_name} {last_name}"
        print(f"{member_id:<5}{name[:24]:<26}{email[:32]:<34}{join_date}")
    return rows


def choose_member(connection):
    """List all members and let the user pick one by ID."""
    rows = list_members(connection)
    if not rows:
        return None
    return choose_id("\nEnter the member ID", [row[0] for row in rows])


def delete_member(connection):
    """DELETE: remove a member, but only if they have no loan records."""
    print("\n--- Delete a Member ---")
    member_id = choose_member(connection)
    if member_id is None:
        return
    loan_count = fetch_all(
        connection, "SELECT COUNT(*) FROM loans WHERE member_id = %s", (member_id,)
    )[0][0]
    if loan_count > 0:
        print(f"This member can't be deleted because they have {loan_count} loan record(s).")
        return
    if not confirm("Are you sure you want to delete this member?"):
        print("Delete cancelled.")
        return
    run_change(connection, "DELETE FROM members WHERE member_id = %s", (member_id,))
    print("Member deleted.")


# ---------------------------------------------------------------
# Loans (check out and return)
# ---------------------------------------------------------------

# Books that are checked out right now: loans with no return date yet.
# This JOIN combines three tables to show the title and the member's name.
ACTIVE_LOANS_QUERY = (
    "SELECT l.loan_id, l.book_id, b.title, m.first_name, m.last_name, "
    "l.checkout_date, l.due_date "
    "FROM loans AS l "
    "JOIN books AS b ON l.book_id = b.book_id "
    "JOIN members AS m ON l.member_id = m.member_id "
    "WHERE l.return_date IS NULL "
    "ORDER BY l.due_date"
)


def list_checked_out(connection):
    """SELECT with JOIN: show the books that are checked out and who has them."""
    rows = fetch_all(connection, ACTIVE_LOANS_QUERY)
    if not rows:
        print("No books are checked out right now.")
        return rows
    print(f"\n{'Loan':<6}{'Title':<30}{'Member':<22}{'Checked out':<13}Due")
    print("-" * 84)
    for loan_id, _, title, first_name, last_name, checkout_date, due_date in rows:
        name = f"{first_name} {last_name}"
        overdue = "  OVERDUE" if due_date < date.today() else ""
        print(f"{loan_id:<6}{title[:28]:<30}{name[:20]:<22}"
              f"{str(checkout_date):<13}{due_date}{overdue}")
    return rows


def check_out_book(connection):
    """INSERT a loan and UPDATE the book's copies. Both changes are saved
    together with one commit, so the database never has only half of them."""
    print("\n--- Check Out a Book ---")
    member_id = choose_member(connection)
    if member_id is None:
        return

    available = fetch_all(
        connection, BOOK_QUERY + " WHERE b.copies_available > 0 ORDER BY b.title"
    )
    print("\nBooks available to check out:")
    display_books(available)
    if not available:
        return
    book_id = choose_id("\nEnter the book ID", [row[0] for row in available])
    if book_id is None:
        return

    checkout_date = ask_date("Checkout date", date.today())
    due_date = checkout_date + timedelta(days=LOAN_DAYS)

    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO loans (book_id, member_id, checkout_date, due_date) "
            "VALUES (%s, %s, %s, %s)",
            (book_id, member_id, checkout_date, due_date),
        )
        cursor.execute(
            "UPDATE books SET copies_available = copies_available - 1 WHERE book_id = %s",
            (book_id,),
        )
        connection.commit()
        print(f"Book checked out. It is due on {due_date}.")
    except mysql.connector.Error as error:
        connection.rollback()   # undo both changes if either one failed
        print("The checkout could not be saved:", error)
    finally:
        cursor.close()


def return_book(connection):
    """UPDATE the loan with its return date and late fee, and add the copy back."""
    print("\n--- Return a Book ---")
    rows = list_checked_out(connection)
    if not rows:
        return
    loan_id = choose_id("\nEnter the loan number", [row[0] for row in rows])
    if loan_id is None:
        return
    loan = next(row for row in rows if row[0] == loan_id)
    book_id, checkout_date, due_date = loan[1], loan[5], loan[6]

    while True:
        return_date = ask_date("Return date", date.today())
        if return_date >= checkout_date:
            break
        print(f"  The return date can't be before the checkout date ({checkout_date}).")

    days_late = max(0, (return_date - due_date).days)
    late_fee = round(days_late * LATE_FEE_PER_DAY, 2)

    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE loans SET return_date = %s, late_fee = %s WHERE loan_id = %s",
            (return_date, late_fee, loan_id),
        )
        cursor.execute(
            "UPDATE books SET copies_available = copies_available + 1 WHERE book_id = %s",
            (book_id,),
        )
        connection.commit()
        if days_late:
            print(f"Book returned {days_late} day(s) late. Late fee: ${late_fee:.2f}")
        else:
            print("Book returned on time. No late fee.")
    except mysql.connector.Error as error:
        connection.rollback()
        print("The return could not be saved:", error)
    finally:
        cursor.close()


# ---------------------------------------------------------------
# Reports (aggregate functions: COUNT, AVG, SUM)
# ---------------------------------------------------------------

def report_books_per_genre(connection):
    """COUNT books in each genre (JOIN books to genres to get the names)."""
    rows = fetch_all(
        connection,
        "SELECT COALESCE(g.name, '(no genre)') AS genre_name, COUNT(*) AS total "
        "FROM books AS b LEFT JOIN genres AS g ON b.genre_id = g.genre_id "
        "GROUP BY genre_name ORDER BY total DESC, genre_name",
    )
    print(f"\n{'Genre':<20}Books")
    print("-" * 26)
    for genre, total in rows:
        print(f"{genre[:18]:<20}{total}")


def report_books_per_author(connection):
    """COUNT books for each author. LEFT JOIN keeps authors with 0 books."""
    rows = fetch_all(
        connection,
        "SELECT a.first_name, a.last_name, COUNT(b.book_id) AS total "
        "FROM authors AS a LEFT JOIN books AS b ON a.author_id = b.author_id "
        "GROUP BY a.author_id, a.first_name, a.last_name "
        "ORDER BY total DESC, a.last_name",
    )
    print(f"\n{'Author':<28}Books")
    print("-" * 34)
    for first_name, last_name, total in rows:
        name = f"{first_name} {last_name}"
        print(f"{name[:26]:<28}{total}")


def report_member_activity(connection):
    """COUNT each member's loans and SUM their late fees."""
    rows = fetch_all(
        connection,
        "SELECT m.first_name, m.last_name, COUNT(l.loan_id) AS loans, "
        "COALESCE(SUM(l.late_fee), 0) AS fees "
        "FROM members AS m LEFT JOIN loans AS l ON m.member_id = l.member_id "
        "GROUP BY m.member_id, m.first_name, m.last_name "
        "ORDER BY loans DESC, m.last_name",
    )
    print(f"\n{'Member':<26}{'Loans':<8}Late fees")
    print("-" * 43)
    for first_name, last_name, loans, fees in rows:
        name = f"{first_name} {last_name}"
        print(f"{name[:24]:<26}{loans:<8}${float(fees):.2f}")


def report_loan_statistics(connection):
    """COUNT loans, AVG loan length in days, and SUM of all late fees.
    AVG skips loans that are not returned yet, because their return_date is NULL."""
    total, returned, average_days, total_fees = fetch_all(
        connection,
        "SELECT COUNT(*), COUNT(return_date), "
        "AVG(DATEDIFF(return_date, checkout_date)), SUM(late_fee) "
        "FROM loans",
    )[0]
    print(f"\nTotal loans:          {total}")
    print(f"Returned:             {returned}")
    print(f"Still checked out:    {total - returned}")
    if average_days is None:
        print("Average loan length:  no returned loans yet")
    else:
        print(f"Average loan length:  {float(average_days):.1f} days")
    print(f"Total late fees:      ${float(total_fees or 0):.2f}")


def reports_menu(connection):
    """Show the reports menu until the user goes back."""
    while True:
        print("\n----- REPORTS -----")
        print("1. Books per genre")
        print("2. Books per author")
        print("3. Member activity (loans and late fees)")
        print("4. Loan statistics")
        print("0. Back to main menu")
        choice = input("Choose a report: ").strip()
        if choice == "1":
            report_books_per_genre(connection)
        elif choice == "2":
            report_books_per_author(connection)
        elif choice == "3":
            report_member_activity(connection)
        elif choice == "4":
            report_loan_statistics(connection)
        elif choice == "0":
            break
        else:
            print("Invalid option. Please choose a number from the menu.")


# ---------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------

def explain_connection_error(error):
    """Turn a MySQL connection error into a friendly message with a next step."""
    if error.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Could not log in: the MySQL password is wrong. Please run the program again.")
    elif error.errno in (errorcode.CR_CONNECTION_ERROR, errorcode.CR_CONN_HOST_ERROR):
        print("Could not reach MySQL. The server may not be running.")
        print("Start it with: sudo /usr/local/mysql/support-files/mysql.server start")
    else:
        print("Could not connect to MySQL:", error.msg)


def ensure_connected(connection):
    """If MySQL closed the connection (for example after a long idle time),
    reconnect and select the library_catalog database again."""
    if not connection.is_connected():
        print("(Reconnecting to MySQL...)")
        connection.reconnect(attempts=2, delay=1)
        create_tables(connection)


# ---------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------

def show_menu():
    """Print the main menu options."""
    print("\n===== LIBRARY CATALOG =====")
    print("Books:    1. Add    2. List    3. Search    4. Update    5. Delete")
    print("Members:  6. Add    7. List    8. Delete")
    print("Loans:    9. Check out    10. Return    11. Checked-out books")
    print("Reports:  12. Reports")
    print("          0. Exit")


def run_menu_choice(connection, choice):
    """Run the feature that matches the menu number the user typed."""
    if choice == "1":
        add_book(connection)
    elif choice == "2":
        print("\n--- All Books ---")
        list_books(connection)
    elif choice == "3":
        search_books(connection)
    elif choice == "4":
        update_book(connection)
    elif choice == "5":
        delete_book(connection)
    elif choice == "6":
        add_member(connection)
    elif choice == "7":
        print("\n--- Members ---")
        list_members(connection)
    elif choice == "8":
        delete_member(connection)
    elif choice == "9":
        check_out_book(connection)
    elif choice == "10":
        return_book(connection)
    elif choice == "11":
        print("\n--- Checked-Out Books ---")
        list_checked_out(connection)
    elif choice == "12":
        reports_menu(connection)
    else:
        print("Invalid option. Please choose a number from the menu.")


def main():
    """Connect, make sure the tables exist, then run the menu until the user exits."""
    try:
        connection = connect_to_server()
        create_tables(connection)
    except mysql.connector.Error as error:
        explain_connection_error(error)
        return
    except FileNotFoundError:
        print(f"Could not find {SCHEMA_FILE}. Run the program from the project folder.")
        return
    print("Connected to the library_catalog database.")

    try:
        while True:
            show_menu()
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Goodbye!")
                break
            # If one action fails, show the problem, undo any half-saved
            # changes, and return to the menu instead of crashing
            try:
                ensure_connected(connection)
                run_menu_choice(connection, choice)
            except mysql.connector.Error as error:
                try:
                    connection.rollback()   # undo anything half-saved
                except mysql.connector.Error:
                    pass                    # the connection itself may be gone
                print(f"Database error: {error.msg}")
                print("Nothing was saved. Please try again.")
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C (or closing the input) ends the program cleanly
        print("\nGoodbye!")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
"""
test_connection.py
Quick check that Python can connect to the local MySQL server.
"""

import getpass

import mysql.connector

# Ask for the password instead of writing it in the code,
# so it never ends up on GitHub
password = getpass.getpass("MySQL root password: ")

# Connect to the MySQL server running on this computer
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=password,
)

# Send a SQL command and read the result
cursor = connection.cursor()
cursor.execute("SELECT VERSION()")
version = cursor.fetchone()[0]
print("Connected! MySQL version:", version)

cursor.close()
connection.close()
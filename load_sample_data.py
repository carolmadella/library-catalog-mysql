"""
load_sample_data.py
Loads the commands in sample_data.sql into the library_catalog database.
Optionally deletes the whole database first, to start from a clean copy.

Run it with: python load_sample_data.py
"""

import library_catalog as lc

connection = lc.connect_to_server()
cursor = connection.cursor()

# Starting fresh deletes every table and row, then schema.sql rebuilds them
if lc.confirm("Delete ALL existing data and start fresh?"):
    cursor.execute("DROP DATABASE IF EXISTS library_catalog")
    print("Old database deleted.")

lc.create_tables(connection)          # make sure the tables exist first

# Run every command in sample_data.sql, then save them all at once
for command in lc.read_sql_commands("sample_data.sql"):
    cursor.execute(command)
connection.commit()

cursor.close()
connection.close()
print("Sample data loaded!")
"""
load_sample_data.py
Loads the commands in sample_data.sql into the library_catalog database.
Run it once: python load_sample_data.py
"""

import library_catalog as lc

connection = lc.connect_to_server()
lc.create_tables(connection)          # make sure the tables exist first
cursor = connection.cursor()

# Run every command in sample_data.sql, then save them all at once
for command in lc.read_sql_commands("sample_data.sql"):
    cursor.execute(command)
connection.commit()

cursor.close()
connection.close()
print("Sample data loaded!")
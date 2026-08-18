from db import create_connection, create_table, insert_many, select_all, select_where, group_by_project
from file_utils import read_csv

# make a connection to the database and create the costs table if it doesn't exist
conn = create_connection("costs.db")
create_table(conn)

# read the csv data and insert them into the costs table
data = read_csv("data/sample.csv")
insert_many(conn, data)

# query the database and print the results
print("All data:")
print(select_all(conn))

print("\nProject Alpha only:")
print(select_where(conn, "project", "Alpha"))

print("\nTotal amount by project:")
print(group_by_project(conn))

conn.close()
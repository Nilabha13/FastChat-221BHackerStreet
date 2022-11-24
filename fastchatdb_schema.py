import psycopg2
from constants import *

conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)

cur = conn.cursor()


users_create_query = '''CREATE TABLE IF NOT EXISTS USERS (
                        username TEXT,
                        salt TEXT,
                        password_hash TEXT,
                        current_server_number INT
                        );'''

groups_create_query = '''CREATE TABLE IF NOT EXISTS GROUPS (
                        group_name TEXT,
                        group_admin TEXT,
                        group_members TEXT
                        );'''

individual_messages_create_query = '''CREATE TABLE IF NOT EXISTS INDIVIDUAL_MESSAGES(
                                    from_user_name TEXT,
                                    to_user_name TEXT,
                                    message_content TEXT,
                                    message_type TEXT,
                                    filename TEXT,
                                    class TEXT,
                                    groupname TEXT,
                                    time_sent TEXT
                                    );'''

group_messages_create_query = '''CREATE TABLE IF NOT EXISTS GROUP_MESSAGES(
                                group_message_id INT PRIMARY KEY,
                                group_id INT,
                                from_user_id INT,
                                message_type TEXT,
                                filename TEXT
                                );'''
                                
keyserver_create_query = '''CREATE TABLE IF NOT EXISTS KEYSERVER(
							username TEXT PRIMARY KEY,
							public_key TEXT,
                            type TEXT
							);'''

cur.execute("""DROP TABLE IF EXISTS USERS""")
cur.execute("""DROP TABLE IF EXISTS GROUPS""")
cur.execute("""DROP TABLE IF EXISTS INDIVIDUAL_MESSAGES""")
cur.execute("""DROP TABLE IF EXISTS GROUP_MESSAGES""")
cur.execute("""DROP TABLE IF EXISTS KEYSERVER""")
cur.execute(users_create_query)
cur.execute(groups_create_query)
cur.execute(individual_messages_create_query)
cur.execute(group_messages_create_query)
cur.execute(keyserver_create_query)

conn.commit()

cur.close()
conn.close()

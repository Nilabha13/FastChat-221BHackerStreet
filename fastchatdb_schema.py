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

messages_create_query = '''CREATE TABLE IF NOT EXISTS MESSAGES(
                                    from_user_name TEXT,
                                    to_user_name TEXT,
                                    message_content TEXT,
                                    message_type TEXT,
                                    filename TEXT,
                                    class TEXT,
                                    groupname TEXT,
                                    time_sent TEXT
                                    );'''
                                
keyserver_create_query = '''CREATE TABLE IF NOT EXISTS KEYSERVER(
							username TEXT,
							public_key TEXT,
                            type TEXT
							);'''

cur.execute("""DROP TABLE IF EXISTS USERS""")
cur.execute("""DROP TABLE IF EXISTS GROUPS""")
cur.execute("""DROP TABLE IF EXISTS MESSAGES""")
cur.execute("""DROP TABLE IF EXISTS KEYSERVER""")
cur.execute(users_create_query)
cur.execute(groups_create_query)
cur.execute(messages_create_query)
cur.execute(keyserver_create_query)

conn.commit()

cur.close()
conn.close()

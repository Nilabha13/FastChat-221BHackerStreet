import psycopg2

conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")

cur = conn.cursor()


users_create_query = '''CREATE TABLE IF NOT EXISTS USERS (
                        user_id INT PRIMARY KEY,
                        username TEXT,
                        password_hash TEXT,
                        is_online BOOLEAN,
                        pending_individiual_messages_queue TEXT,
                        pending_group_messages_queue TEXT,
                        current_server_number INT
                        );'''

groups_create_query = '''CREATE TABLE IF NOT EXISTS GROUPS (
                        group_id INT PRIMARY KEY,
                        group_name TEXT,
                        group_admin TEXT,
                        group_members TEXT
                        );'''

individual_messages_create_query = '''CREATE TABLE IF NOT EXISTS INDIVIDUAL_MESSAGES(
                                    individual_message_id INT PRIMARY KEY,
                                    from_user_name TEXT,
                                    to_user_name TEXT,
                                    message_content TEXT
                                    );'''

group_messages_create_query = '''CREATE TABLE IF NOT EXISTS GROUP_MESSAGES(
                                group_message_id INT PRIMARY KEY,
                                group_id INT,
                                from_user_id INT
                                );'''
                                
keyserver_create_query = '''CREATE TABLE IF NOT EXISTS KEYSERVER(
							username TEXT PRIMARY KEY,
							public_key TEXT
							);'''

cur.execute("""DROP TABLE IF EXISTS USERS""")
cur.execute(users_create_query)
cur.execute(groups_create_query)
cur.execute(individual_messages_create_query)
cur.execute(group_messages_create_query)
cur.execute(keyserver_create_query)

conn.commit()

cur.close()
conn.close()

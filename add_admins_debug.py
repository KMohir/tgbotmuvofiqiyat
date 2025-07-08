import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('DB_NAME', 'mydatabase'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASS', '7777')
)
cursor = conn.cursor()

# Добавить супер-админа, если его нет
cursor.execute('''
    INSERT INTO admins (user_id, is_superadmin) VALUES (%s, %s)
    ON CONFLICT (user_id) DO UPDATE SET is_superadmin = EXCLUDED.is_superadmin
''', (5657091547, True))
conn.commit()

cursor.execute('SELECT user_id, is_superadmin FROM admins')
admins = cursor.fetchall()

print('user_id\tis_superadmin')
for user_id, is_superadmin in admins:
    print(f'{user_id}\t{is_superadmin}')

cursor.close()
conn.close() 
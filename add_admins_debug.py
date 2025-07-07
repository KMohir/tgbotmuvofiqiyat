import sqlite3

conn = sqlite3.connect('centris.db')
cursor = conn.cursor()

# Добавить супер-админа, если его нет
cursor.execute('''
    INSERT OR IGNORE INTO admins (user_id, is_superadmin) VALUES (?, ?)
''', (5657091547, 1))
conn.commit()

cursor.execute('SELECT user_id, is_superadmin FROM admins')
admins = cursor.fetchall()

print('user_id\tis_superadmin')
for user_id, is_superadmin in admins:
    print(f'{user_id}\t{is_superadmin}')

cursor.close()
conn.close() 
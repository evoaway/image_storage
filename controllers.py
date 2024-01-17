# from app import mysql
#
#
# def get_user(name, password):
#     cur = mysql.connection.cursor()
#     cur.execute('''SELECT * FROM users WHERE name = %s and password = %s''', (name, password))
#     data = cur.fetchall()
#     cur.close()
#     return data
#
#
# def add_user(name, password):
#     cur = mysql.connection.cursor()
#     cur.execute('''INSERT INTO table_name (name, age) VALUES (%s, %s)''', (name, password))
#     mysql.connection.commit()
#     cur.close()
#     return 'Data added successfully'

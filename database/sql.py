import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="123password!",
    database="hakadb"
)

mycursor = mydb.cursor()
# mycursor.execute("SHOW TABLES")
#
# sqlFormula = "INSERT INTO users (name, age) VALUES (%s, %s)"
# users = [("savva", 18),
#          ("Blyad", 16)]

#mycursor.executemany(sqlFormula, users) #засунуть в базу
#mycursor.execute("SELECT * FROM users")
# mycursor.execute("SELECT age FROM users")

# myresult = mycursor.fetchall()#взять и запомнить результат
# myresult = mycursor.fetchone()#берёт первый
# for row in myresult:
#     print(row)

# mydb.commit()   #отправляем таблицу
#
#mycursor.execute("SELECT * FROM users WHERE age = 18")     #показываем при каком условии выбирать
# mycursor.execute("SELECT * FROM users WHERE age LIKE '%6'")   #не безопасный вариант
# sql = "SELECT * FROM users WHERE name LIKE %s"  #безопасный
# mycursor.execute(sql, ('savva',))
#
# sql = "UPDATE users SET name = 'fifa' WHERE age = '18'" #изменяем _что то_ где _условие_
# mycursor.execute(sql)
#
# mycursor.execute("SELECT * FROM users LIMIT 3 OFFSET 1")#до определённого момента offset это с какого индекса
# sql = "SELECT * FROM users ORDER BY age" #....DESC наоборот порядок
sql = "DROP TABLE IF EXISTS users"    #удаление всей таблице

mycursor.execute(sql)



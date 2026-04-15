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
def nickname_used(cursor, nickname):
    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (nickname,)
    )
    return cursor.fetchone() is not None

def sign_up(cursor, name, username, age, password):
    print("CALLING SIGN UP")
    print(name, username, age, password)
    cursor.execute(
        "INSERT INTO users (name, username, age, password) VALUES (%s,%s,%s,%s)",
        (name, username, age, password))
    mydb.commit()

def login(cursor, username, password):
    if nickname_used(cursor, username):
        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username ,password,)
        )
        return cursor.fetchone() is not None
    else:
        return False

def add_to_friends(cursor, mydb, username, username_friend):
    if username == username_friend:
        return "Нельзя добавить самого себя"

    username, username_friend = sorted((username, username_friend))

    cursor.execute(
        "INSERT INTO friends (username, username_friend) VALUE (%s,%s)",
        (username, username_friend,)
    )
    mydb.commit()

def show_my_friends(cursor, nickname):
    cursor.execute("SELECT * FROM friends WHERE user_name = %s", (nickname,))
    result = cursor.fetchall()
    if result:
        return result
    else:
        return 0

def set_cur_place(cursor,nickname, loc):
    cursor.execute("UPDATE users SET place = %s WHERE ")

def set_hobbies(cursor, username, hobbies):
    for i in range(len(hobbies)):
        cursor.execute(
            "INSERT INTO hobbies (user_name, hobby) VALUES (%s,%s)",
            (username, hobbies[i]))
    mydb.commit()

# mycursor.execute("INSERT INTO users (username) VALUES (%s)",("alice",))



mydb.commit()
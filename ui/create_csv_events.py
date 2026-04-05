import csv

def export_to_csv(mycursor, filename="events.csv"):
    # берём все мероприятия
    mycursor.execute("SELECT id, title, author, tags, time_start, time_end, place, lat, lng, desc FROM activities")
    activities = mycursor.fetchall()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # заголовок
        writer.writerow(["id", "title", "author", "tags", "time_start", "time_end", "place", "lat", "lng", "desc", "participants"])

        for activity in activities:
            activity_id = activity[0]

            # берём участников этого мероприятия
            mycursor.execute("SELECT username FROM activity_users WHERE activity_id = %s", (activity_id,))
            users = mycursor.fetchall()
            participants = "|".join([u[0] for u in users])

            writer.writerow([*activity, participants])

export_to_csv(mycursor)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pika
import json
from sqlalchemy.orm import sessionmaker
from DataBase.database import engine
from Schema import Model

SessionLocal = sessionmaker(bind=engine)

def callback(ch, method, properties, body):
    data = json.loads(body)
    db = SessionLocal()

    notification = Model.Notification(
        userid=data["userid"],
        type=data["type"],
        postlink=data.get("postlink")
    )

    db.add(notification)
    db.commit()
    db.close()
    print("✅ Notification saved:", data)

def start_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()

    channel.queue_declare(queue="notifications")
    channel.basic_consume(queue="notifications", on_message_callback=callback, auto_ack=True)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()

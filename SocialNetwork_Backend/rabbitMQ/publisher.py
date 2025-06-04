import pika
import json

def send_notification_to_queue(data: dict):
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()

    channel.queue_declare(queue="notifications")

    channel.basic_publish(
        exchange='',
        routing_key='notifications',
        body=json.dumps(data)
    )

    connection.close()

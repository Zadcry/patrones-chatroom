# backend/worker.py
import pika
import json
import os
import sys

# Ajuste de path para que encuentre el paquete 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models import Message
from app.core.config import settings

def save_to_db(ch, method, properties, body):
    data = json.loads(body)
    db = SessionLocal()
    try:
        # Aquí ignoramos 'username' porque la DB solo necesita user_id
        # Ignoramos 'type': 'system' si decidimos no guardar notificaciones de sistema
        if data.get('type') == 'system':
             ch.basic_ack(delivery_tag=method.delivery_tag)
             return

        new_msg = Message(
            room_id=data['room_id'],
            user_id=data['user_id'],
            content=data['content']
        )
        db.add(new_msg)
        db.commit()
        print(f" [x] Persisted message from User {data['user_id']} in Room {data['room_id']}")
        
        # Confirmar procesamiento a RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f" [!] Error saving to DB: {e}")
        db.rollback()
        # No hacemos ack para que RabbitMQ lo reintente o lo mande a Dead Letter Queue
    finally:
        db.close()

def main():
    print(" [*] Starting Worker...")
    while True:
        try:
            params = pika.URLParameters(settings.BROKER_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue='chat_messages', durable=True)
            
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='chat_messages', on_message_callback=save_to_db)
            
            print(' [*] Worker waiting for messages. To exit press CTRL+C')
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            print(" [!] Connection failed, retrying in 5s...")
            import time
            time.sleep(5)
        except Exception as e:
            print(f" [!] Critical error: {e}")
            break

if __name__ == '__main__':
    main()
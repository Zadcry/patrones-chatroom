import pika
import json
from app.core.config import settings

def publish_message(message_data: dict):
    """Publica un mensaje en la cola 'chat_messages'."""
    try:
        # Nota: En producción, mantendrías la conexión abierta en lugar de abrir/cerrar por mensaje
        params = pika.URLParameters(settings.BROKER_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        channel.queue_declare(queue='chat_messages', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='chat_messages',
            body=json.dumps(message_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hace el mensaje persistente
            ))
        connection.close()
    except Exception as e:
        print(f"Error publishing to broker: {e}")
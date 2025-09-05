import pika
import json
import threading
from config import Config
import time

class RabbitMQHandler:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        
        try:
            url = "amqps://zyxugwqh:5ZOoSHJxcUJBg-zaeZ6HfXgA4zuPjHQA@fuji-01.lmq.cloudamqp.com/zyxugwqh"
            print("Connecting with URL:", url)

            parameters = pika.URLParameters(url)
            print(parameters)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare queues
            self.channel.queue_declare(queue='stt_processing', durable=True)
            self.channel.queue_declare(queue='feedback_analysis', durable=True)

            print("RabbitMQ connection established")
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            raise

    
    def publish_message(self, queue_name, message):
        """Publish message to queue"""
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()
            
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            print(f"Message published to {queue_name}")
            
        except Exception as e:
            print(f"Failed to publish message: {e}")
            # Try to reconnect and retry
            try:
                self.connect()
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                    )
                )
            except Exception as retry_error:
                print(f"Retry failed: {retry_error}")
    
    def close_connection(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print("RabbitMQ connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")

# Global instance
rabbitmq_handler = RabbitMQHandler()
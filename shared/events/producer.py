import aio_pika
from typing import Optional
from .schemas.events import BaseEvent
from pydantic_settings import BaseSettings

class RabbitMQSettings(BaseSettings):
    rabbitmq_url: str

    class Config:
        env_file="/app/.env"
        extra="ignore"


settings = RabbitMQSettings()
print(f"RabbitMQ URL: {settings.rabbitmq_url }")

class EventProducer:
    def __init__(self):
        self.rabbitmq_url =settings.rabbitmq_url 
        self.connection=None
        self.channel=None

    async def connect(self):
        self.connection=await aio_pika.connect_robust(self.rabbitmq_url )
        self.channel=await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        print(f"Подключён к {self.rabbitmq_url }")

    async def publish(self, event: BaseEvent, exchange_name: str="events"):
        """Отправка события"""
        print(f"PRODUCER: Отправка {event.event_type.value} id={event.event_id}")
        if not self.channel:
            await self.connect()

        """Создание topic exchange"""
        exchange=await self.channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC)
        print(f"PRODUCER: Exchange '{exchange_name}' готов")
        """Отправка сообщения"""
        message=aio_pika.Message(
            body=event.model_dump_json().encode(),
            content_type="application/json"
        )

        routing_key = f"{event.event_type.value}.{event.source_service}"
        print(f"PRODUCER: Routing key '{routing_key}'")
        await exchange.publish(message, routing_key=routing_key)
        print(f"PRODUCER: СООБЩЕНИЕ ОТПРАВЛЕНО в '{routing_key}'!")

    async def close(self):
        """Закрытие соединения"""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()


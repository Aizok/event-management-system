import asyncio

import aio_pika
import json
from typing import Optional, Callable
from .schemas.events import BaseEvent
from pydantic_settings import BaseSettings

class RabbitMQSettings(BaseSettings):
    rabbitmq_url: str

    class Config:
        env_file="/app/.env"
        extra="ignore"


settings=RabbitMQSettings()
print(f"RabbitMQ URL: {settings.rabbitmq_url }")


class EventConsumer:
    def __init__(self):
        self.rabbitmq_url = settings.rabbitmq_url
        self.connection=None
        self.channel=None
        self.consume_task = None
        self.callback=None

    async def connect(self):
        self.connection=await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel=await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        print(f"Consumer подключён к {self.rabbitmq_url }")

    async def consume(
            self,
            exchange_name: str="events",
            queue_name: str="user_events",
            routing_keys: list=["TaskCreated.task-service"],
            callback: Callable[[BaseEvent], None]=None
    ):
        """Получение сообщения"""
        if not self.channel:
            await self.connect()

        """Создание topic exchange"""
        exchange=await self.channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC)

        """Создание очереди"""
        queue=await self.channel.declare_queue(queue_name, durable=True)

        """bind очереди к exchange с routing keys"""
        for routing_key in routing_keys:
            await queue.bind(exchange, routing_key)
            print(f"Consumer подписан на {routing_key}")


        # Callback функция
        async def on_message(message):
            async with message.process():
                try:
                    # Парсинг события
                    # JSON to dict
                    event_data=json.loads(message.body.decode())
                    # dict to BaseEvent
                    event=BaseEvent.model_validate(event_data)

                    print(f"Получено событие {event.event_type.value} (id={event.event_id})")
                    if self.callback:
                        await self.callback(event)

                except Exception as e:
                    print(f"Ошибка обработки события: {e}")

        """Начинаем потребление"""
        self.consume_task=asyncio.create_task(queue.consume(on_message))
        print(f"Consumer запущен на очереди: {queue_name}")
        return self.consume_task

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
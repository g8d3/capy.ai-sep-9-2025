from __future__ import annotations

import os
from rq import Worker, Queue, Connection
from redis import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
listen = ["backtests"]


if __name__ == "__main__":
    conn = Redis.from_url(REDIS_URL)
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()

import asyncio
from threading import Thread

__global_loop: asyncio.AbstractEventLoop | None = None

def run_async_task(task):
    """
    Run a asyncio awaitable task
    task: awaitable task
    """
    global __global_loop
    if __global_loop is None:
        __global_loop = asyncio.new_event_loop() 
        Thread(target=__global_loop.run_forever).start()
    return asyncio.run_coroutine_threadsafe(task, __global_loop).result()

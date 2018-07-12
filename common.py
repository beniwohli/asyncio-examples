import asyncio

import elasticapm


async def tracked_sleep(sleep_time, counter):
    async with elasticapm.async_capture_span('sleep_%d_%.3f' % (counter, sleep_time)):
        await asyncio.sleep(sleep_time)
    elasticapm.tag(**{'sleep_%d' % counter: sleep_time})
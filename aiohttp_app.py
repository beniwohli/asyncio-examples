import asyncio
import random
import logging

from aiohttp import web

from common import tracked_sleep

import elasticapm

routes = web.RouteTableDef()

logging.basicConfig(level=logging.DEBUG)

apm_client = elasticapm.Client(service_name='async-greeter')
elasticapm.instrument()



@web.middleware
async def transaction(request, handler):
    info = request.match_info.get_info()
    apm_client.begin_transaction('request')
    resp = await handler(request)
    apm_client.end_transaction(info.get('formatter', info.get('path')), resp.status)
    return resp


@routes.get('/{name}')
async def hello_name(request):
    coros = [tracked_sleep(random.random() / 10, i) for i in range(random.randint(1, 10))]
    async with elasticapm.capture_span('overall'):
        await asyncio.wait(coros)
    return web.Response(text="Hello, {0}".format(request.match_info['name']))


@routes.get('/')
async def hello(request):
    return web.Response(text="Hello, world")


def init(argv):
    app = web.Application(middlewares=[transaction])
    # app = web.Application()
    app.add_routes(routes)
    return app
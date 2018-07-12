import os
import asyncio
import logging
import random

from aiohttp.client import ClientSession
from sanic import Sanic
from sanic import response

import elasticapm

from common import tracked_sleep

logging.basicConfig(level=logging.DEBUG)

app = Sanic(__name__)

apm_client = elasticapm.Client(service_name='sanic-greeter')
elasticapm.instrument()


@app.middleware('request')
async def start_transaction(request):
    apm_client.begin_transaction('request')


@app.middleware('response')
async def end_transaction(request, response):
    apm_client.end_transaction(request.uri_template, response.status)


async def get_ip():
    async with ClientSession() as session:
        async with session.get('https://get.geojs.io/v1/ip.json') as response:
            result = await response.json()
            return result['ip']


async def get_long_lat(ip):
    async with ClientSession() as session:
        async with session.get('https://get.geojs.io/v1/ip/geo/{}.json'.format(ip)) as response:
            result = await response.json()
            return result['latitude'], result['longitude']


async def get_weather(lat, lon):
    weather_api_key = os.environ['WEATHER_API_KEY']
    url = 'https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}'.format(lat, lon, weather_api_key)
    print(url)
    async with ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
            return result


@app.route('/weather')
async def weather(request):
    async with elasticapm.async_capture_span('overall'):
        ip = await get_ip()
        lat, lon = await get_long_lat(ip)
        weather = await get_weather(lat, lon)

    return response.json({
        'ip': ip,
        'geo': {
            'latitude': lat,
            'longitude': lon,
        },
        'weather': weather
    })


@app.route('/<name:[A-z]+>')
async def hello(request, name):
    coros = [tracked_sleep(random.random() / 10, i) for i in range(random.randint(1, 10))]
    async with elasticapm.async_capture_span('overall'):
        await asyncio.gather(coros)
    return response.text('Hello')


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8088)
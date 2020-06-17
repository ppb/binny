import gqlmod
gqlmod.enable_gql_import()  # noqa

import asyncio
import datetime
import logging
import os

from async_cron.job import CronJob
from async_cron.schedule import Scheduler
from quart import Quart
import quart_github_webhook

from .astro import get_nearest_solar_event
from .globals import ghapp
from .greeting import do_greeting

log = logging.getLogger(__name__)
rootlog = logging.getLogger()


app = Quart(__name__)
app.config.from_mapping(os.environ)
scheduler = Scheduler()


webhook = quart_github_webhook.Webhook(
    app,
    endpoint='/webhook/github',
    secret=app.config['WEBHOOK_SECRET'],
)


@app.route('/status')
async def status():
    """
    Basic status call
    """
    gh_ok = True
    try:
        await ghapp.get_this_app()
    except Exception:
        log.exception("Error checking github")
        gh_ok = False

    return (f"""Service: ok
GitHub: {'ok' if gh_ok else 'err'}
""", 200 if gh_ok else 500)


@webhook.hook('pull_request')
async def greeting_pull_request(payload):
    """
    https://developer.github.com/v3/activity/events/types/#pullrequestevent
    """
    async with ghapp.for_installation(payload['installation']['id']):
        if payload['action'] == 'opened':
            await do_greeting(**payload)


async def check_release():
    """
    Checks if today is a release-related day, and performs appropriate actions
    """
    today = datetime.date.today()
    # Using "nearest" to make sure we get today's
    release = get_nearest_solar_event()
    freeze = release - datetime.timedelta(days=4 * 7)  # 4 weeks before release
    # ^^ is marginal, but should work: 1mo freeze < 1.5mo past/future switchover

    if today == release:
        # TODO: Notify about release day
        ...
    elif today == freeze:
        # TODO: Notify about freeze day
        ...


async def capture_exceptions(func):
    try:
        await func()
    except Exception:
        rootlog.exception("Exception in background task")


@app.before_serving
async def schedule():
    log.info("Initializing schedule")
    scheduler.add_job(
        CronJob(name='check_release', tolerance=12 * 60 * 60)  # tolerance=12hrs (in seconds)
        .every().day
        .go(capture_exceptions, check_release),
    )

    asyncio.create_task(scheduler.start())


async def entrypoint(scope, receive, send):
    if scope["type"] == "http" and scope["scheme"] == "http":
        # Let's assume we're behind a proxy, adjust based on additional headers
        for k, v in scope['headers']:
            if k.lower() == b'x-forwarded-proto':
                scope['scheme'] = v.decode('ascii')
            elif k.lower() == b'x-forwarded-for':
                scope['client'] = (v.decode('ascii'), 0)

    return await app(scope, receive, send)

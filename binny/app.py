import gqlmod
gqlmod.enable_gql_import()  # noqa

import logging
import os

from quart import Quart
import quart_github_webhook

from .globals import ghapp
from .greeting import do_greeting

log = logging.getLogger(__name__)


app = Quart(__name__)
app.config.from_mapping(os.environ)


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
    repo = payload['repository']
    async with ghapp.for_installation(payload['installation']['id']):
        # Limit this to the test repo for now.
        if repo['full_name'] != 'ppb/binny-test-repo':
            return
        if payload['action'] == 'opened':
            await do_greeting(**payload)


async def entrypoint(scope, receive, send):
    if scope["type"] == "http" and scope["scheme"] == "http":
        # Let's assume we're behind a proxy, adjust based on additional headers
        for k, v in scope['headers']:
            if k.lower() == b'x-forwarded-proto':
                scope['scheme'] = v.decode('ascii')
            elif k.lower() == b'x-forwarded-for':
                scope['client'] = (v.decode('ascii'), 0)

    return await app(scope, receive, send)

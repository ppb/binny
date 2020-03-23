from .queries import get_all_prs


MESSAGE = """
Thank you for contributing to PursuedPyBear! Don't forget to add yourself `CONTRIBUTORS.md`.
"""


async def iter_prs(repo):
    resp = await get_all_prs(repo=repo)
    assert not resp.errors, resp.errors
    yield from resp.data['node']['pullRequests']['nodes']

    while resp.data['node']['pullRequests']['pageInfo']['hasNextPage']:
        resp = await get_all_prs(
            repo=repo,
            after=resp.data['node']['pullRequests']['pageInfo']['endCursor'],
        )
        assert not resp.errors, resp.errors
        yield from resp.data['node']['pullRequests']['nodes']


async def count_prs_for_user(repo, login):
    prs = [
        pr
        async for pr in iter_prs(repo)
        if pr['author']['login'] == login
    ]

    count = len(prs)
    is_bot = any(
        pr['author']['__typename'] == 'Bot'
        for pr in prs
    )  # These should be all true or all false
    return count, is_bot


async def do_greeting(pull_request, repository, sender, **_):
    """
    Args from https://developer.github.com/v3/activity/events/types/#pullrequestevent
    """
    prcount, is_bot = await count_prs_for_user(repository['node_id'], sender['login'])

    if is_bot:
        # Don't do anything if the sender is a bot
        return

    if prcount > 1:
        # They've had two or more PRs, don't greet
        return

    # Ok, this is a greetable PR, send the greeting
    ...

import gqlmod
gqlmod.enable_gql_import()  # noqa

import pathlib
import subprocess

from .status import deploy_status


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def update_git(ref, commit, branch_name):
    subprocess.run(
        ['git', 'fetch', 'origin', ref],
        cwd=PROJECT_ROOT, check=True,
    )

    # TODO: Make sure FETCH_HEAD matches commit

    subprocess.run(
        ['git', 'checkout', '-b', branch_name, 'FETCH_HEAD'],
        cwd=PROJECT_ROOT, check=True,
    )


def deploy(deployment_id):
    with deploy_status(deployment_id) as deployment:
        # 1. Update code via git
        update_git(
            ref=f"{deployment['ref']['prefix']}{deployment['ref']['name']}",
            commit=deployment['commit']['oid'],
            branch_name=deployment['ref']['name'],
        )

        # 2. Update dependencies via poetry
        subprocess.run(
            ['poetry', 'install'],
            cwd=PROJECT_ROOT, check=True,
        )

        # 3. Restart service
        subprocess.run(
            ['systemctl', '--user', 'restart', 'binny'],
            cwd=PROJECT_ROOT, check=True,
        )

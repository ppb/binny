"""
Self-update
"""
import gqlmod
gqlmod.enable_gql_import()  # noqa

import sys

from binny.deploy import deploy
deploy(sys.argv[1])

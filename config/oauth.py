"""Authentication configuration
"""
import os

from .utils import read_boolean

# Should only be True when testing
LOGIN_DISABLED = read_boolean('LOGIN_DISABLED', default=False)

OPENID_PROVIDERS = [
    {'name': 'GitHub',
     'url': 'https://github.com/login/oauth/authorize'}
]

# Defines API endpoints for OAuth providers. If their API changes these
# will need to be updated.
OAUTH_CONFIG = {
    'github':
        {'authorize_url': 'https://github.com/login/oauth/authorize',
         'base_url': 'https://github.com/login/',
         'token_url': 'https://github.com/login/oauth/access_token',
         'user_api': 'https://api.github.com/user'},
    'gitlab':
        {'authorize_url': 'http://sdrshgitlabv.camhres.ca/oauth/authorize',
         'base_url': 'http://sdrshgitlabv.camhres.ca',
         'token_url': 'http://sdrshgitlabv.camhres.ca/oauth/token',
         'user_api': 'http://sdrshgitlabv.camhres.ca/api/v3/user'
         }
}

# OAuth provider ID and 'secret' needed to authenticate users with the service
# provider. These values are given when first configuring OAuth for the app.
OAUTH_CREDENTIALS = {
    'github': {'id': os.environ.get('OAUTH_CLIENT_GITHUB'),
               'secret': os.environ.get('OAUTH_SECRET_GITHUB')
               },
    'gitlab': {'id': os.environ.get('OAUTH_CLIENT_GITLAB'),
               'secret': os.environ.get('OAUTH_SECRET_GITLAB')
               }
}

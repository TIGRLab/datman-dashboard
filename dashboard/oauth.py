from config import OAUTH_CREDENTIALS
from rauth import OAuth1Service, OAuth2Service
from flask import url_for, request, redirect, session
import string
import random

import json, urllib2


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = OAUTH_CREDENTIALS[provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class GithubSignIn(OAuthSignIn):
    str_rnd = None
    def __init__(self):
        super(GithubSignIn, self).__init__('github')

        self.service = OAuth2Service(
            name='github',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://github.com/login/oauth/authorize',
            base_url='https://github.com/login/',
            access_token_url='https://github.com/login/oauth/access_token'
        )

    def random_string(self, size=10, chars=string.ascii_uppercase +
                                           string.ascii_lowercase +
                                           string.digits):
        """Generates a random string"""
        rnd = ''.join(random.SystemRandom().choice(chars) for _ in range(size))
        self.str_rnd = rnd

    def authorize(self):
        self.random_string()
        return redirect(self.service.get_authorize_url(
            scope='user public_repo',
            state=self.str_rnd)
            )

    def callback(self):
        if 'code' not in request.args:
            return None, None
        if not request.args.get('state') == self.str_rnd:
            return None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()
                  })
        #me = oauth_session.get('').json()
        access_token = oauth_session.access_token
        user = oauth_session.get('https://api.github.com/user').json()
        return(access_token, user)

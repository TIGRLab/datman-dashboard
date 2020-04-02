"""This allows users to be validated using the OAuth protocol

See https://blog.miguelgrinberg.com/post/oauth-authentication-with-flask for
an overview.
"""
import json
import string
import random

from rauth import OAuth2Service
from flask import url_for, request, redirect, session, current_app


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('auth.oauth_callback', provider=self.provider_name,
                       _external=True)

    def random_string(self, size=10, chars=(string.ascii_uppercase +
                                            string.ascii_lowercase +
                                            string.digits)):
        """Generates a random string"""
        rnd = ''.join(random.SystemRandom().choice(chars) for _ in range(size))
        return rnd

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class GithubSignIn(OAuthSignIn):

    def __init__(self):
        super(GithubSignIn, self).__init__('github')

        self.conf = current_app.config['OAUTH_CONFIG']['github']
        self.service = OAuth2Service(
            name='github',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url=self.conf['authorize_url'],
            base_url=self.conf['base_url'],
            access_token_url=self.conf['token_url']
        )

    def authorize(self):
        session['str_rnd'] = self.random_string()
        if current_app.config['GITHUB_PUBLIC']:
            app_scope = 'user public_repo'
        else:
            app_scope = 'user repo'
        return redirect(self.service.get_authorize_url(
            scope=app_scope,
            state=session['str_rnd']))

    def callback(self):
        if 'code' not in request.args or 'state' not in request.args:
            return None, None

        returned_state = request.args['state']

        if returned_state != session['str_rnd']:
            return None, None

        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()
                  })

        access_token = oauth_session.access_token
        user = oauth_session.get(self.conf['user_api']).json()

        return access_token, user


class GitlabSignIn(OAuthSignIn):
    str_rnd = None

    def __init__(self):
        super(GitlabSignIn, self).__init__('gitlab')

        self.conf = current_app.config['OAUTH_CONFIG']['gitlab']
        self.service = OAuth2Service(
            name='gitlab',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url=self.conf['authorize_url'],
            base_url=self.conf['base_url'],
            access_token_url=self.conf['token_url']
        )

    def authorize(self):
        self.random_string()
        return redirect(self.service.get_authorize_url(
            state=self.str_rnd,
            redirect_uri=url_for('auth.oauth_callback',
                                 provider='gitlab',
                                 _external=True),
            response_type='code'))

    def callback(self):
        if 'code' not in request.args:
            return None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()
                  },
            decoder=json.loads)
        access_token = oauth_session.access_token
        api_url = self.conf['user_api']
        user = oauth_session.get(api_url).json()
        return access_token, user

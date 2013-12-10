import json
import os

from flask import Flask, flash, request, redirect, render_template, session, url_for

from rauth.service import OAuth2Service


# Flask config
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = True
WAVE_CLIENT_ID = os.getenv('WAVE_CLIENT_ID')
WAVE_CLIENT_SECRET = os.getenv('WAVE_CLIENT_SECRET')

# Flask setup
app = Flask(__name__)
app.config.from_object(__name__)

# rauth OAuth 2.0 service wrapper
wave_api_url = 'https://api.waveapps.com/'
wave_authorize_url = '{}oauth2/authorize/'.format(wave_api_url)
wave_token_url = '{}oauth2/token/'.format(wave_api_url)

wave = OAuth2Service(name='wave',
                     authorize_url=wave_authorize_url,
                     access_token_url=wave_token_url,
                     client_id=app.config['WAVE_CLIENT_ID'],
                     client_secret=app.config['WAVE_CLIENT_SECRET'],
                     base_url=wave_api_url)


# views
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/about')
def about():
    if session.has_key('token'):
        auth = wave.get_session(token = session['token'])
        resp = auth.get('user')
        if resp.status_code == 200:
            user = resp.json()

        resp = auth.get('businesses')
        if resp.status_code == 200:
            businesses = resp.json()

        return render_template('about.html', user=user, businesses=businesses)
    else:
        return redirect(url_for('login'))

@app.route('/wave/login')
def login():
    redirect_uri = url_for('authorized', _external=True)
    params = {
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'user.read business.read account.read invoice.read'
    }
    return redirect(wave.get_authorize_url(**params))

@app.route('/wave/authorized')
def authorized():
    # check to make sure the user authorized the request
    if not 'code' in request.args:
        flash('You did not authorize the request')
        return redirect(url_for('index'))

    # make a request for the access token credentials using code
    redirect_uri = url_for('authorized', _external=True)
    data = dict(
        code=request.args['code'],
        redirect_uri=redirect_uri,
        grant_type='authorization_code'
    )

    auth = wave.get_auth_session(data=data, decoder=json.loads)
    session['token'] = auth.access_token
    return redirect(url_for('about'))


if __name__ == '__main__':
    app.run()

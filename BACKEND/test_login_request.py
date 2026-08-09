import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

URL = 'http://127.0.0.1:8000/api/auth/login/'
BODY = json.dumps({'username': 'demo_admin', 'password': 'DemoAdmin123!'}).encode('utf-8')
HEADERS = {'Content-Type': 'application/json'}

for name, headers in [
    ('no-auth', HEADERS),
    ('invalid-auth', {**HEADERS, 'Authorization': 'Bearer invalidtoken'}),
]:
    print('---', name, '---')
    req = Request(URL, data=BODY, headers=headers, method='POST')
    try:
        resp = urlopen(req)
        print('status', resp.status)
        print(resp.read().decode('utf-8'))
    except HTTPError as err:
        print('status', err.code)
        print(err.read().decode('utf-8'))
    except Exception as exc:
        print('exception', type(exc).__name__, exc)

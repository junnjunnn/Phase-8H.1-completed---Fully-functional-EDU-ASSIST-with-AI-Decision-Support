import json
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8000/api'
ENDPOINTS = [
    ('POST','/auth/login/'),
    ('GET','/auth/me/'),
    ('GET','/students/'),
    ('GET','/enrollments/'),
    ('GET','/academic-years/'),
    ('GET','/grade-levels/'),
    ('GET','/sections/'),
    ('GET','/subjects/'),
    ('GET','/teacher-assignments/'),
    ('GET','/academic-records/'),
    ('GET','/attendance-records/'),
    ('GET','/behavioral-assessments/'),
    ('GET','/risk-predictions/'),
    ('GET','/prediction-factors/'),
    ('GET','/interventions/'),
    ('GET','/reports/center/'),
    ('GET','/reports/export/'),
    ('GET','/audit-logs/'),
]

headers = {'Content-Type': 'application/json'}

def do_login():
    data = json.dumps({'username': 'demo_admin', 'password': 'DemoAdmin123!'}).encode()
    req = urllib.request.Request(BASE + '/auth/login/', data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode('utf-8')
        print('LOGIN', resp.status)
        return json.loads(body).get('access')


def check_endpoints(token):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    for method, path in ENDPOINTS[1:]:
        url = BASE + path
        req = urllib.request.Request(url, data=None if method == 'GET' else b'', headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode('utf-8')
                js = 'json' if (body and (body.strip().startswith('{') or body.strip().startswith('['))) else 'not-json'
                print(path, resp.status, js, len(body))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            print(path, 'HTTP', e.code, body[:500])
        except Exception as e:
            print(path, 'ERR', type(e).__name__, e)


if __name__ == '__main__':
    try:
        token = do_login()
        if not token:
            print('No token returned from login')
        else:
            check_endpoints(token)
    except Exception as exc:
        print('FAILED', exc)

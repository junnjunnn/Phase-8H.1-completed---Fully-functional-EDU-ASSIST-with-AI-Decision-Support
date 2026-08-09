import site, os
paths = site.getsitepackages()
print('site-packages candidates:')
for p in paths:
    print('-', p, 'exists=', os.path.exists(p))
    try:
        files = os.listdir(p)
    except Exception as e:
        print('  list error', e)
        continue
    matches = [f for f in files if 'setuptools' in f or 'pkg_resources' in f or f.startswith('pkg_resources')]
    print('  matches count:', len(matches))
    for m in matches[:100]:
        print('   -', m)
    print('  first 50 entries:')
    for f in files[:50]:
        print('   -', f)

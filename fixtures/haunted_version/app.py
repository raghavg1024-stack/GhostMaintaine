import tomllib

assert tomllib.loads('enabled = true')['enabled'] is True
print('VERSION_SMOKE_OK: 1 assertion passed')

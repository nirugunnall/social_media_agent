import tomllib, openai, traceback
s = open(r'.\.streamlit\secrets.toml','rb').read()
data = tomllib.loads(s.decode())
key = data.get('OPENAI_API_KEY','').strip()
openai.api_key = key
try:
    models = openai.Model.list()
    print('OPENAI_OK: reachable, models count:', len(models.data))
except Exception as e:
    print('OPENAI_ERROR:', repr(e))
    traceback.print_exc()

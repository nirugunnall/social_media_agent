from openai import OpenAI
import tomllib, traceback
s = open(r'.\.streamlit\secrets.toml','rb').read()
data = tomllib.loads(s.decode())
key = data.get('OPENAI_API_KEY','').strip()
client = OpenAI(api_key=key)
try:
    resp = client.chat.completions.create(model='gpt-4o-mini', messages=[{'role':'user','content':'test'}], max_tokens=5)
    print('OPENAI_OK: success')
except Exception as e:
    print('OPENAI_ERROR:', repr(e))
    traceback.print_exc()

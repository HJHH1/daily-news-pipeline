import os
from openai import OpenAI

def deepseek_chat(config, user_message: str) -> str:
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        api_key = config['deepseek']['api_key']
    client = OpenAI(api_key=api_key, base_url=config['deepseek']['base_url'])
    response = client.chat.completions.create(
        model=config['deepseek']['model'],
        messages=[{"role": "user", "content": user_message}],
        temperature=config['deepseek']['temperature'],
        max_tokens=8192
    )
    return response.choices[0].message.content

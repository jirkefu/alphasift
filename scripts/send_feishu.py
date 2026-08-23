import hmac
import hashlib
import base64
import json
import time
import os
import subprocess

webhook_url = os.environ['WEBHOOK_URL']
secret = os.environ.get('WEBHOOK_SECRET')
timestamp = int(time.time())

# 读取输出内容（限制长度）
try:
    with open('out.txt', 'r') as f:
        content = f.read()[:3000]
except FileNotFoundError:
    content = "未找到选股结果文件"

payload = {
    'msg_type': 'text',
    'content': {
        'text': f'📊 选股策略 (resonance_20260823) 结果：\n{content}'
    }
}

# 如果配置了签名，则添加 timestamp 和 sign
if secret:
    sign_str = f'{timestamp}\n{secret}'
    sign = base64.b64encode(hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    payload['timestamp'] = timestamp
    payload['sign'] = sign

cmd = ['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(payload), webhook_url]
subprocess.run(cmd, check=True)

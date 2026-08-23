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

try:
    with open('out.txt', 'r') as f:
        data = json.load(f)
except Exception as e:
    content = f"读取选股结果失败: {e}"
    payload = {'msg_type': 'text', 'content': {'text': content}}
    subprocess.run(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(payload), webhook_url])
    exit(1)

picks = data.get('picks', [])
if not picks:
    content = "📊 稳健收益策略完成，但未选出符合条件的股票。"
else:
    lines = [
        f"📊 稳健收益策略 (stable_income) 结果",
        f"📅 {time.strftime('%Y-%m-%d %H:%M')}",
        f"📈 共扫描 {data.get('snapshot_count', 0)} 只股票，精选 {len(picks)} 只",
        "",
        "| 排名 | 代码 | 名称 | 得分 | 涨跌幅% | PE | PB | 换手率% |",
        "|------|------|------|------|---------|----|----|---------|"
    ]
    for p in picks[:3]:
        lines.append(
            f"| {p.get('rank', '-')} | {p.get('code', '-')} | {p.get('name', '-')} | "
            f"{p.get('final_score', 0):.1f} | {p.get('change_pct', 0):.1f} | "
            f"{p.get('pe_ratio', '-')} | {p.get('pb_ratio', '-')} | {p.get('turnover_rate', '-')} |"
        )
    content = "\n".join(lines)

payload = {'msg_type': 'text', 'content': {'text': content}}

if secret:
    sign_str = f'{timestamp}\n{secret}'
    sign = base64.b64encode(hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    payload['timestamp'] = timestamp
    payload['sign'] = sign

subprocess.run(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(payload), webhook_url], check=True)

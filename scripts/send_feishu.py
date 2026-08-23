import hmac
import hashlib
import base64
import json
import time
import os
import subprocess

# ====== 短线参数配置 ======
ATR_STOP_MULTIPLIER = 1.5   # 止损 ATR 倍数
ATR_PROFIT_MULTIPLIER = 2.0 # 止盈 ATR 倍数
HOLD_DAYS = 3               # 固定持股天数
# =========================

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
    content = "📊 稳健收益策略未选出符合条件的股票。"
else:
    # 构建表格（区间格式）
    lines = [
        f"📊 稳健收益策略 (stable_income) 短线信号",
        f"📅 {time.strftime('%Y-%m-%d %H:%M')}",
        f"📈 共扫描 {data.get('snapshot_count', 0)} 只，精选 {len(picks)} 只",
        "",
        "| 排名 | 代码 | 名称 | 得分 | 当前价 | 买入区间 | 止损区间 | 止盈区间 | 盈亏比 | 持股天数 |",
        "|------|------|------|------|--------|----------|----------|----------|--------|----------|"
    ]

    for p in picks[:3]:
        price = p.get('price', 0)
        atr = p.get('atr_20_pct', price * 0.015)  # 如果无ATR，默认1.5%

        # 如果atr是百分比，转为价格
        if atr is None or atr == 0:
            atr = price * 0.015
        elif atr < 1:
            atr = price * atr  # 假设是百分比

        # 计算基础值
        stop_price = price - ATR_STOP_MULTIPLIER * atr
        profit_price = price + ATR_PROFIT_MULTIPLIER * atr

        # 生成区间（上下浮动0.5%）
        buy_low = round(price * 0.995, 2)
        buy_high = round(price * 1.005, 2)
        stop_low = round(stop_price * 0.995, 2)
        stop_high = round(stop_price * 1.005, 2)
        profit_low = round(profit_price * 0.995, 2)
        profit_high = round(profit_price * 1.005, 2)

        # 计算盈亏比
        risk = price - stop_price
        reward = profit_price - price
        ratio = round(reward / risk, 2) if risk > 0 else 0

        lines.append(
            f"| {p.get('rank', '-')} | {p.get('code', '-')} | {p.get('name', '-')} | "
            f"{p.get('final_score', 0):.1f} | {price:.2f} | "
            f"{buy_low:.2f}~{buy_high:.2f} | {stop_low:.2f}~{stop_high:.2f} | "
            f"{profit_low:.2f}~{profit_high:.2f} | {ratio:.2f} | {HOLD_DAYS} |"
        )

    lines.append("")
    lines.append("💡 操作建议：从以上3只中随机选1只，在买入区间内挂单买入，止损设在止损区间，止盈设在止盈区间，持股3天后无论盈亏均卖出。")
    content = "\n".join(lines)

payload = {'msg_type': 'text', 'content': {'text': content}}

if secret:
    sign_str = f'{timestamp}\n{secret}'
    sign = base64.b64encode(hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    payload['timestamp'] = timestamp
    payload['sign'] = sign

subprocess.run(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(payload), webhook_url], check=True)

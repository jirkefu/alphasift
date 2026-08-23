import hmac
import hashlib
import base64
import json
import time
import os
import subprocess
from datetime import datetime
from manage_positions import load_positions, save_positions, update_positions

# ====== 短线参数配置 ======
ATR_STOP_MULTIPLIER = 1.5
ATR_PROFIT_MULTIPLIER = 2.0
HOLD_DAYS = 3
# =========================

webhook_url = os.environ['WEBHOOK_URL']
secret = os.environ.get('WEBHOOK_SECRET')
timestamp = int(time.time())

# 读取选股结果
try:
    with open('out.txt', 'r') as f:
        data = json.load(f)
except Exception as e:
    content = f"读取选股结果失败: {e}"
    payload = {'msg_type': 'text', 'content': {'text': content}}
    subprocess.run(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(payload), webhook_url])
    exit(1)

picks = data.get('picks', [])

# === 1. 更新持仓 ===
positions = update_positions(picks)

# === 2. 添加新推荐到持仓（假设都买入） ===
today = datetime.now().strftime('%Y-%m-%d')
for p in picks[:3]:
    price = p.get('price', 0)
    atr = p.get('atr_20_pct', price * 0.015)
    if atr is None or atr == 0:
        atr = price * 0.015
    elif atr < 1:
        atr = price * atr
    
    stop_price = price - ATR_STOP_MULTIPLIER * atr
    profit_price = price + ATR_PROFIT_MULTIPLIER * atr
    
    # 检查是否已持有
    existing = [pos for pos in positions if pos['code'] == p['code']]
    if not existing:
        positions.append({
            'code': p['code'],
            'name': p['name'],
            'buy_price': price,
            'buy_date': today,
            'hold_days': HOLD_DAYS,
            'target_pct': round((profit_price - price) / price * 100, 1),
            'stop_pct': round((stop_price - price) / price * 100, 1),
            'current_price': price,
            'change_pct': 0,
            'days_held': 0,
            'status': 'hold',
            'reason': '新开仓'
        })

save_positions(positions)

# === 3. 构建飞书消息 ===
lines = []
lines.append("📊 稳健收益策略 - 持仓追踪 & 新推荐")
lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 3.1 持仓追踪
sell_count = sum(1 for p in positions if p['status'] == 'sell')
hold_count = sum(1 for p in positions if p['status'] == 'hold')
lines.append(f"📈 持仓: {len(positions)} 只 (持有 {hold_count} / 卖出 {sell_count})")
lines.append("")

if positions:
    lines.append("📌 【持仓追踪】")
    lines.append("| 代码 | 名称 | 买入价 | 当前价 | 盈亏% | 天数 | 建议 |")
    lines.append("|------|------|--------|--------|-------|------|------|")
    for pos in positions:
        emoji = "🔴" if pos['status'] == 'sell' else "🟡"
        lines.append(
            f"| {pos['code']} | {pos['name']} | {pos['buy_price']:.2f} | "
            f"{pos['current_price']:.2f} | {pos['change_pct']:.1f}% | "
            f"{pos['days_held']} | {emoji} {pos['reason']} |"
        )
    lines.append("")

# 3.2 新推荐
if picks:
    lines.append("📌 【新推荐（今日买入）】")
    lines.append("| 排名 | 代码 | 名称 | 当前价 | 买入区间 | 止损区间 | 止盈区间 |")
    lines.append("|------|------|------|--------|----------|----------|----------|")
    for p in picks[:3]:
        price = p.get('price', 0)
        atr = p.get('atr_20_pct', price * 0.015)
        if atr is None or atr == 0:
            atr = price * 0.015
        elif atr < 1:
            atr = price * atr
        
        stop_price = price - ATR_STOP_MULTIPLIER * atr
        profit_price = price + ATR_PROFIT_MULTIPLIER * atr
        
        buy_low, buy_high = round(price * 0.995, 2), round(price * 1.005, 2)
        stop_low, stop_high = round(stop_price * 0.995, 2), round(stop_price * 1.005, 2)
        profit_low, profit_high = round(profit_price * 0.995, 2), round(profit_price * 1.005, 2)
        
        lines.append(
            f"| {p.get('rank', '-')} | {p['code']} | {p['name']} | {price:.2f} | "
            f"{buy_low:.2f}~{buy_high:.2f} | {stop_low:.2f}~{stop_high:.2f} | "
            f"{profit_low:.2f}~{profit_high:.2f} |"
        )
    lines.append("")

# 3.3 操作建议
lines.append("💡 操作建议：")
lines.append("1. 持仓中标记🔴的股票应立即卖出")
lines.append("2. 标记🟡的股票继续持有，等待下一次信号")
lines.append("3. 从新推荐中选1只买入")

content = "\n".join(lines)

# === 4. 发送到飞书 ===
payload = {'msg_type': 'text', 'content': {'text': content}}
if secret:
    sign_str = f'{timestamp}\n{secret}'
    sign = base64.b64encode(hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    payload['timestamp'] = timestamp
    payload['sign'] = sign

subprocess.run(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(payload), webhook_url], check=True)

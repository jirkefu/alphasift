import json
import os
import time
from datetime import datetime, timedelta

POSITIONS_FILE = "positions.json"

def load_positions():
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_positions(positions):
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f, indent=2)

def update_positions(picks):
    """更新持仓：计算盈亏，判断卖出/持有"""
    positions = load_positions()
    today = datetime.now()
    
    # 构建当前价格映射
    price_map = {p['code']: p['price'] for p in picks}
    
    # 更新已有持仓
    for pos in positions:
        code = pos['code']
        if code in price_map:
            pos['current_price'] = price_map[code]
            pos['change_pct'] = (price_map[code] - pos['buy_price']) / pos['buy_price'] * 100
            pos['days_held'] = (today - datetime.strptime(pos['buy_date'], '%Y-%m-%d')).days
            
            # 判断是否卖出
            if pos['change_pct'] >= pos['target_pct']:
                pos['status'] = 'sell'      # 触达止盈
                pos['reason'] = f"触达止盈 +{pos['target_pct']}%"
            elif pos['change_pct'] <= pos['stop_pct']:
                pos['status'] = 'sell'      # 触达止损
                pos['reason'] = f"触达止损 {pos['stop_pct']}%"
            elif pos['days_held'] >= pos['hold_days']:
                pos['status'] = 'sell'      # 持股到期
                pos['reason'] = f"持股{pos['hold_days']}天到期"
            else:
                pos['status'] = 'hold'
                pos['reason'] = f"持有中 ({pos['days_held']}/{pos['hold_days']}天)"
    
    return positions

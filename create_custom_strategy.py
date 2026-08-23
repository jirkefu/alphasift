#!/usr/bin/env python3
"""
交互式创建 AlphaSift 自定义多因子策略
用法: python3 create_custom_strategy.py
"""

import os
import yaml
import subprocess
from datetime import datetime

def get_float_input(prompt, default=None):
    """获取浮点数输入"""
    while True:
        val = input(prompt)
        if not val.strip() and default is not None:
            return default
        try:
            return float(val)
        except ValueError:
            print("请输入有效数字")

def main():
    print("\n" + "="*60)
    print("  🧠 AlphaSift 自定义多因子策略生成器")
    print("="*60)
    print("\n输入各因子的权重（总和建议 = 1.0）")
    print("权重越高，该因子对最终得分的影响越大\n")

    factors = {
        "value": {"label": "📊 估值 (PE/PB)", "default": 0.10},
        "momentum": {"label": "📈 动量 (MACD/趋势)", "default": 0.25},
        "reversal": {"label": "🔄 反转 (RSI/超买超卖)", "default": 0.20},
        "activity": {"label": "💹 量价 (量比/换手率)", "default": 0.25},
        "liquidity": {"label": "💰 流动性 (成交额)", "default": 0.10},
        "stability": {"label": "🛡️ 稳定性 (波动率)", "default": 0.10},
    }

    weights = {}
    print("--- 请依次输入各因子权重 ---")
    for key, info in factors.items():
        val = get_float_input(f"  {info['label']} 权重 (默认 {info['default']}): ", info['default'])
        weights[key] = val

    strategy_name = input(f"\n📝 策略名称 (默认 resonance_{datetime.now().strftime('%Y%m%d')}): ")
    if not strategy_name.strip():
        strategy_name = f"resonance_{datetime.now().strftime('%Y%m%d')}"

    desc = input("📝 策略描述 (可选): ") or f"自定义多因子共振策略，权重: {weights}"

    # 构建 YAML 结构（不包含 hard_filters，避免字段名不兼容）
    strategy_config = {
        "style": {
            "name": strategy_name,
            "category": "multi_factor",
            "description": desc,
        },
        "screening": {
            "factor_weights": weights,
            "scoring_profile": {
                "reversal_ideal_change_pct": -2.0,
                "activity_ideal_volume_ratio": 1.2,
                "activity_ideal_turnover_rate": 2.0,
            },
            # 注意：hard_filters 被注释掉，避免加载失败
            # 如有需要，请参考现有策略 yaml 的格式手动添加
        }
    }

    yaml_path = f"strategies/{strategy_name}.yaml"
    os.makedirs("strategies", exist_ok=True)

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(strategy_config, f, allow_unicode=True, sort_keys=False, indent=2)

    print(f"\n✅ 策略已保存至: {yaml_path}")

    run_now = input("\n🚀 是否立即运行该策略？(y/n): ").strip().lower()
    if run_now == 'y':
        max_out = input("  输出前多少只股票？(默认 20): ") or "20"
        use_llm = input("  是否启用 AI 排序？(y/n，默认 n): ").strip().lower()
        cmd = f"alphasift screen {strategy_name} --max-output {max_out} --save-run"
        if use_llm != 'y':
            cmd += " --no-llm"
        print(f"\n▶️ 执行: {cmd}\n")
        subprocess.run(cmd, shell=True)

    print(f"\n💡 提示: 如需调整权重或添加过滤条件，直接编辑 {yaml_path} 文件")

if __name__ == "__main__":
    main()

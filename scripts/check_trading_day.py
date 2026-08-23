import datetime
import akshare as ak

today = datetime.datetime.now().strftime('%Y%m%d')
trade_days = ak.tool_trade_date_hist_sina()
is_trading = today in trade_days['trade_date'].astype(str).values
print(str(is_trading).lower())

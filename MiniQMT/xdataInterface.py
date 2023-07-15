import pandas as pd
from xtquant import xtdata
import os
import time


stock_list = ['000063.SZ', '300014.SZ','601988.SH', '603338.SH', '688160.SH', '002920.SZ' ]

def on_data(datas):
    print('call back 1 stock &&&&&&&')
    for stock_code in datas:
        	print(stock_code, datas[stock_code])
    print('call back 1 stock end *******')

def on_data_whole_quote(datas):
    print('call back whole quote++++++++++++++++++')
    for stock_code in datas:
        	print(stock_code, datas[stock_code])
    print('call back whole quote end ---------------------')

xtdata.subscribe_quote('000063.SZ', period='1m', start_time='', end_time='', count=0, callback=on_data)

xtdata.subscribe_whole_quote(stock_list, callback=on_data_whole_quote)


data = xtdata.get_market_data(field_list=['time', 'open', 'high', 'low', 'close', 'volume'],
                              stock_list=['000063.SZ', '300014.SZ'], period='1d', count=10)

df = pd.DataFrame(data['open'])

print(data['close'])

print(data['close'].T['300014.SZ'])

for i in range(100):
    time.sleep(30)
    print(i)



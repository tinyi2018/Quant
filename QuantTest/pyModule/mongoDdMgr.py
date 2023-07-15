#import Ipynb_importer
#import DbOpModule
import pymysql
import tushare as ts
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
import talib as ta
import sys
import datetime
import json
import ast
import pymongo
import importlib
from pandas.io.json import json_normalize
sys.path.append(r"D:\Jupyter_Pj\pyModule")
import mongodbOp
importlib.reload(mongodbOp)

class mongoDbMgr():
    db_name = "stock"
    daily_col_name = "stock_daily"
    stock_basic_col_name = "stock_basic_info"
    stock_divid_factors_col_name = "stock_divid_factors"
    stock_db_info_name = "stock_db_info"

    daily_start_date = "20120801"
    daily_end_date   = "20220811"


    def __init__ (self):
        pass


    def mongoDbMgr(self):

        
        pass

def save_stock_daily_to_db(self, stockbasic):
	
    pro = ts.pro_api('af5f423bb57f376e71c2903058362f8e3e053fe30f486463f9bdac8e')

	df_temp = pro.daily(ts_code="000001.SZ", start_date = "20220811", end_date = "20220811")
	df_temp.rename(columns = {"ts_code":"stock_code"},inplace=True)
	df_temp.drop(df_temp.index, inplace=True)
	i =0 
	for i in stockbasic.index:

		start_time_ = self.daily_start_date
		if(stockbasic.loc[i,"list_date"] > start_time_):

			start_time_ = stockbasic.loc[i,"list_date"]

		df =pro.daily(ts_code=stockbasic.loc[i,"ts_code"], start_date = start_time_, end_date = self.daily_end_date)
			#db_op.insert_stock_daily_many(col_name, df)
		print ("db_op: insert_stock_daily_many get daily form tushare website， index : = %d, stock_code:= %s, len = %d" %(i,stockbasic.loc[i,"ts_code"],len(df)))
		
		df.rename(columns = {"ts_code":"stock_code"},inplace=True)

		df_temp = pd.concat([df_temp, df], axis=0, ignore_index=True)

		if( len(df_temp)>= 10000):
			db_op.insert_stock_daily_many(daily_col_name, df_temp)
			print ("db_op: insert_stock_daily_many completed!! index to: = %d, stock_code:= %s, len = %d , size = %d " %(i,stockbasic.loc[i,"ts_code"],len(df_temp), sys.getsizeof(df_temp)))
			df_temp.drop(df_temp.index, inplace=True)
			
		#if( i >=2655):
		#	break	

	if( len(df_temp)>= 1):
		db_op.insert_stock_daily_many(daily_col_name, df_temp)
		print ("db_op: insert_stock_daily_many completed!!  out side !!! index to: = %d, stock_code:= %s, len = %d , size = %d " %(i,stockbasic.loc[i,"ts_code"],len(df_temp), sys.getsizeof(df_temp)))
		df_temp.drop(df_temp.index, inplace=True)
        

def insert_stock_daily_oneDay(data_):
    df = pro.daily(trade_date=data_)
    db_op.insert_stock_daily_many(daily_col_name, df)

def update_stock_daily_auto():
    now = time.strftime("%Y%m%d")
    start_date = time.strftime("%Y%m%d",time.localtime(time.time() - 100*60*60*24))  #  100 天前的日期
    df = pro.trade_cal(exchange='', start_date = start_date, end_date = now)
    df = df[df["is_open"] ==1]
    df = df.sort_values(by=["cal_date"], ascending=[False])
    df = df.reset_index(drop=True)

    db_val = db_op.find_any(stock_db_info_name, {"_id":"0001"})
    last_update = db_val.stock_daily_update_time.values[0]

    last_update_index = df[df["cal_date"] == last_update].index
    df = df[0:last_update_index[0]]

    for dat in df["cal_date"].values:
        df_ts = pro.daily(trade_date=data_)
        db_op.insert_stock_daily_many(daily_col_name, df_ts)
        print ("完全更新 %d 的数据"%(dat) )

    # 更新数据的时间保存到数据库
    info_dict = {"_id":"0001", "stock_daily_update_time":time.strftime("%Y%m%d")}
    db_op.update_record_to_db(stock_db_info_name,info_dict )    



def update_diff_stock_daily():
    sb = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,list_date')
    db_val = db_op.find_any(daily_col_name, {"trade_date" :"20220812"})
    temp01 = sb["ts_code"].values
    temp02 = set(temp01) -set(db_val)

    sb_val = pd.DataFrame(data = None, columns= sb.columns)
    for sc in temp02:
        df = sb[sb["ts_code"] == sc]
        sb_val = pd.concat([sb_val, df], axis=0, ignore_index=True)

    save_stock_daily_to_db(sb_val)
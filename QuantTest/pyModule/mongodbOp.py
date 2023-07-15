import numpy as np
import pandas as pd
import time
import sys
import datetime
import json
import pymongo
import math
from copy import deepcopy
from pandas.io.json import json_normalize


class MongoDbOp():
    host = "localhost"
    port = 27017
    db_name = None

    op_db = None
    op_col = None

    def __init__(self, host_ = "localhost", port_ = 27017):
        self.host = host_
        self.port = port_

    def connect_To_MongoDb(self, host_ = "localhost", port_ = 27017, db_name = "test_db"):
        self.db_name = db_name
        self.host = host_
        self.port = port_

        client = pymongo.MongoClient(self.host, self.port)
        self.op_db = client[self.db_name]


    def insert_stock_daily_many(self, col_name, df ):
        # 把 “ts_code "字段替换为 ”stock_code"
        for colume in df.columns:
            if (colume == 'ts_code'):
                df.rename(columns = {"ts_code":"stock_code"},inplace=True)

        self.op_col = self.op_db[col_name]
        for i in df.index:
            df.loc[i,'_id'] = f"{df.loc[i,'stock_code']}-{df.loc[i,'trade_date']}"   # 增加 '_id' 字段， 为ts_code-trade_date, 如 “000001.SZ-20220801"
 
        data = json.loads(df.T.to_json()).values()
        try:
            res = self.op_col.insert_many(data)
        except  Exception as e:
            res = e
            print ("insert_stock_daily_many  Error: " +str(e) )
        
        return res
        

    def insert_stock_daily_many_2(self, col_name, df, step=1000):
        
        # 把 “ts_code "字段替换为 ”stock_code"
        for colume in df.columns:
            if (colume == 'ts_code'):
                df.rename(columns = {"ts_code":"stock_code"},inplace=True)


        self.op_col = self.op_db[col_name]

        for i in range(math.ceil(df.shape[0] / step)):
            data = df.iloc[step * i:step * (i + 1)].to_dict(orient="record")
            self.op_col.insert_many(data)


    def update_stock_daily_many(self,col_name, df):
        # 把 “ts_code "字段替换为 ”stock_code"
        for colume in df.columns:
            if (colume == 'ts_code'):
                df.rename(columns = {"ts_code":"stock_code"},inplace=True)

        self.op_col = self.op_db[col_name]

         # 增加 '_id' 字段， 为stock_code-trade_date, 如 “000001.SZ-20220801"
        for i in df.index:
            df.loc[i,'_id'] = f"{df.loc[i,'stock_code']}-{df.loc[i,'trade_date']}"  

        data = json.loads(df.to_json(orient="index",force_ascii=False)).values()
        for row in data:
            self.op_col.update_one({"_id": f"{row['stock_code']}-{row['trade_date']}"},{"$set":row}, upsert=True)
            #self.col_op.update_one({"ts_code":row['ts_code'], "trade_date":row["trade_date"]},{"$set":row}, upsert=True)
        
    def update_stock_basic_info_many(self,col_name, df):
        # 把 “ts_code "字段替换为 ”stock_code"
        for colume in df.columns:
            if (colume == 'ts_code'):
                df.rename(columns = {"ts_code":"stock_code"},inplace=True)

        self.op_col = self.op_db[col_name]

        data = json.loads(df.to_json(orient="index",force_ascii=False)).values()
        for row in data:
            self.op_col.update_one({"_id": row['stock_code']},{"$set":row}, upsert=True)
            #self.op_col.update_one({"_id": f"{row['ts_code']}-{row['trade_date']}"},{"$set":row}, upsert=True)
            #self.col_op.update_one({"ts_code":row['ts_code'], "trade_date":row["trade_date"]},{"$set":row}, upsert=True)
        
    def update_stock_divid_factors(self,col_name, disc_):

        self.op_col = self.op_db[col_name]
        disc = deepcopy(disc_)

        self.op_col.update_one({'_id': disc["_id"]},{"$set":disc}, upsert=True)


    def update_stock_divid_factors_many(self,col_name, disc_list):

        self.op_col = self.op_db[col_name]

        self.op_col.insert_many(disc_list)


    def update_record_to_db(self,col_name, dict_ ):

        self.op_col = self.op_db[col_name]
        self.op_col.update_one({'_id': dict_["_id"]},{"$set":dict_}, upsert=True)


    def insert_stock_1mK_line_many(self, col_name, df ):
        # 把 “ts_code "字段替换为 ”stock_code"
        for colume in df.columns:
            if (colume == 'ts_code'):
                df.rename(columns = {"ts_code":"stock_code"},inplace=True)

        self.op_col = self.op_db[col_name]
        for i in df.index:
            df.loc[i,'_id'] = f"{df.loc[i,'stock_code']}-{df.loc[i,'trade_time']}"   # 增加 '_id' 字段， 为ts_code-trade_date, 如 “000001.SZ-20220801"
 
        data = json.loads(df.T.to_json()).values()
        try:
            res = self.op_col.insert_many(data)
        except  Exception as e:
            res = e
            print ("insert_stock_daily_many  Error: " +str(e) )
        
        return res





    def find_code(self,col_name, code):

        self.op_col = self.op_db[col_name]
        ret = list(self.op_col.find({"stock_code":code}))
        
        if(len(ret) == 0):
            return None
        else:
            df = json_normalize(ret)
            df = df.drop(columns=["_id"])
            return df   
        
    def find_any(self, col_name, qurey):
        self.op_col = self.op_db[col_name]
        ret = list(self.op_col.find(qurey))
        
        if(len(ret) == 0):
            return None
        else:
            df = json_normalize(ret)
            #df = df.drop(columns=["_id"])
            return df      

    def find_test(self, col_name, qurey):
        self.op_col = self.op_db[col_name]
        ret = list(self.op_col.find({'stock_code':'002920.SZ','trade_date':{'$lt':'20220731'}}))
        
        if(len(ret) == 0):
            return None
        else:
            df = json_normalize(ret)
            return df  


    def find_distinct(self, col_name ,fields,query):
        self.op_col = self.op_db[col_name]
        ret = self.op_col.distinct(fields,query)
        return ret

    def find_some(self, col_name, qurey,ascending = True, num = 10):
        self.op_col = self.op_db[col_name]

        if (ascending ):
            ret = list(self.op_col.find(qurey).limit(num))
        else:
            ret = list(self.op_col.find(qurey).sort('_id', -1).limit(num))

        if(len(ret) == 0):
            return None
        else:
            df = json_normalize(ret)
            #df = df.drop(columns=["_id"])
            return df    

    def remove_doc_form_col(self, col_name, qurey):
        self.op_col = self.op_db[col_name]
        self.op_col.delete_one(qurey)


    def del_all_data_in_collection(self,col_name, qurey = {}):
        self.op_col = self.op_db[col_name]
        self.op_col.delete_many(qurey)


    def del_collection(self,col_name):
        return self.op_col[col_name].drop()
        

    def del_database(self):
        return self.op_db.dropDatabase()
        






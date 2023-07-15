from xtquant import xtdata, xttrader, xtconstant
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from sanic import Sanic, Blueprint, response
import aiohttp, random

api = Blueprint('xtquant', url_prefix='/xtquant/trade')


@api.listener('before_server_start')
async def before_server_start(app, loop):
    '''全局共享session'''
    global session, trader
    jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(cookie_jar=jar, connector=aiohttp.TCPConnector(ssl=False))
    trader = Trader()


@api.listener('after_server_stop')
async def after_server_stop(app, loop):
    '''关闭session'''
    await session.close()


order_status = {
    xtconstant.ORDER_UNREPORTED: '未报',
    xtconstant.ORDER_WAIT_REPORTING: '待报',
    xtconstant.ORDER_REPORTED: '已报',
    xtconstant.ORDER_REPORTED_CANCEL: '已报待撤',
    xtconstant.ORDER_PARTSUCC_CANCEL: '部成待撤',
    xtconstant.ORDER_PART_CANCEL: '部撤',
    xtconstant.ORDER_CANCELED: '已撤',
    xtconstant.ORDER_PART_SUCC: '部成',
    xtconstant.ORDER_SUCCEEDED: '已成',
    xtconstant.ORDER_JUNK: '废单',
    xtconstant.ORDER_UNKNOWN: '未知'
}

if __name__ == '__main__':
    app = Sanic(name='xtquant')
    app.config.RESPONSE_TIMEOUT = 600000
    app.config.REQUEST_TIMEOUT = 600000
    app.config.KEEP_ALIVE_TIMEOUT = 600
    app.blueprint(api)
    app.run(host='0.0.0.0', port=7800, workers=1, auto_reload=True, debug=False)



'''定义交易账户全局信息类
这里使用单例模式，确保Trader中的RPC实例和账户信息唯一：
'''
class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class Trader(Singleton):
    xt_trader = None
    account = None

    def set_trader(self, qmt_dir, session_id):
        self.xt_trader = XtQuantTrader(qmt_dir, session_id)
        # 启动交易线程
        self.xt_trader.start()
        # 建立交易连接，返回0表示连接成功
        connect_result = self.xt_trader.connect()
        return connect_result

    def set_account(self, account_id, account_type):
        self.account = StockAccount(account_id, account_type=account_type)
        return self.account

    @property
    def get_account(self):
        return self.account

    @property
    def get_trader(self):
        return self.xt_trader

'''账号登录
随机设置一个session_id值，并传入极简客户端用户目录和账号ID、类型，连接客户端：
'''


@api.route('/login', methods=['GET'])
async def login(request):
    '''
    账号登录
    '''
    session_id = int(request.args.get("session_id", random.randint(20000, 60000)))
    qmt_dir = request.args.get("qmt_dir", 'D:\\ProgramFile\\国金证券QMT交易端\\userdata_mini')
    account_id = request.args.get("account_id", '')
    account_type = request.args.get("account_type", 'STOCK')  # 账号类型，可选STOCK、CREDIT

    connect_result = trader.set_trader(qmt_dir, session_id)
    trader.set_account(account_id, account_type=account_type)

    print("交易连接成功！") if connect_result == 0 else print("交易连接失败！")
    return response.json({"status": connect_result})

'''查询功能封装
查询资产、当前持仓、当日成交、当日委托等：
'''


@api.route('/query/assets', methods=['GET'])
async def query_assets(request):
    '''
    查询总资产
    '''
    asset = trader.xt_trader.query_stock_asset(trader.account)
    return response.json({"总资产": asset.total_asset, "现金": asset.cash, "持仓市值": asset.market_value,
                          "冻结金额": asset.frozen_cash})


@api.route('/query/holding', methods=['GET'])
async def query_holding(request):
    '''
    查询当前持仓
    '''
    holding = []
    for p in trader.xt_trader.query_stock_positions(trader.account):
        holding.append([{'股票代码': p.stock_code, '持仓': p.volume, '可用持仓': p.can_use_volume, '成本': p.open_price,
                         '持仓市值': p.market_value}])
    return response.json(holding, ensure_ascii=False)


@api.route('/query/trade', methods=['GET'])
async def query_trade(request):
    '''
    查询当日成交
    '''
    trades = trader.xt_trader.query_stock_trades(trader.account)

    result = []
    for trade in trades:
        result.append({'股票代码': trade.stock_code, '委托类型': trade.order_type, '成交数量': trade.traded_volume,
                       '成交均价': trade.traded_price, '成交金额': trade.traded_amount, '成交时间': trade.traded_time,
                       "成交编号": trade.traded_id, "柜台合同编号": trade.order_sysid})
    return response.json(result, ensure_ascii=False)


@api.route('/query/order', methods=['GET'])
async def query_order(request):
    '''
    查询当日委托
    '''
    order_id = request.args.get('order_id', '')
    if order_id == '':
        orders = trader.xt_trader.query_stock_orders(trader.account)
    else:
        orders = trader.xt_trader.query_stock_order(trader.account, int(order_id))
        # 订单不存在，下单失败
        if orders is None:
            return response.json([], ensure_ascii=False)
        orders = [orders]
    result = []
    for order in orders:
        result.append({'股票代码': order.stock_code, '委托数量': order.order_volume, '成交数量': order.traded_volume,
                       '委托价格': order.price, '委托类型': order.order_type,
                       '委托状态': order_status.get(order.order_status), "订单编号": order.order_id,
                       "柜台合同编号": order.order_sysid, "报单时间": order.order_time})
    return response.json(result, ensure_ascii=False)

'''交易功能封装
包含下单和撤单两类，下单成功会返回一个大于0的订单号，撤单只需传入这个订单号即可，撤单成功返回0。

注意：有时会存在下单失败的情况，因此最好下单后使用查询当日委托接口查询订单是否真的传送到客户端，如果不存在则重新下单
'''


@api.route('/place_order', methods=['GET'])
async def trade_place_order(request):
    '''
    下单
    '''
    stock_code = request.args.get('stock_code', '510300.SH')
    direction = xtconstant.STOCK_BUY if request.args.get('direction', 'buy') == 'buy' else xtconstant.STOCK_SELL
    volumn = int(request.args.get('volumn', '100'))
    price = float(request.args.get('price', '4.4'))
    order_id = trader.xt_trader.order_stock(trader.account, stock_code, direction, volumn, xtconstant.FIX_PRICE, price,
                                            'strategy_name', 'remark')
    return response.json({'order_id': order_id}, ensure_ascii=False)


@api.route('/cancel_order', methods=['GET'])
async def trade_cancel_order(request):
    '''
    撤单
    '''
    order_id = int(request.args.get('order_id', '0'))
    cancel_order_result = trader.xt_trader.cancel_order_stock(trader.account, order_id)
    return response.json({'cancel_order_result': cancel_order_result}, ensure_ascii=False)


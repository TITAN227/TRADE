import ccxt
import pprint
import time
import datetime
import pandas as pd
import larry 
import math


with open("api.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

binance = ccxt.binance(config={
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
    'defaultType': 'future' 
    }
})


symbol = "BTC/USDT"
long_target, short_target = larry.cal_target(binance, symbol)
balance = binance.fetch_balance()
usdt = balance['free']['USDT']
op_mode = False
position = {
    "type": None,
    "amount": 0
    }
    
def cal_amount(usdt_balance, cur_price):
    portion = 0.3
    usdt_trade = usdt_balance * portion
    amount = math.floor((usdt_trade * 1000000)/cur_price) / 1000000
    return amount


def enter_position(exchange, symbol, cur_price, long_target, short_target, amount, position):
    if cur_price > long_target:
        position['type'] = 'long'
        position['amount'] = amount
        exchange.create_market_buy_order(symbol=symbol, amount=amount)  
    elif cur_price < short_target:
        position['type'] = 'short'
        position['amount'] = amount
        exchange.create_market_sell_order(symbol=symbol, amount=amount)


def exit_position(exchange, symbol, position):
    amount = position['amount']
    if position['type'] == 'long':
        exchange.create_market_sell_order(symbol=symbol, amount=amount)
        position['type'] = None
    elif position['type'] == 'short':
        exchange.create_market_buy_order(symbol=symbol, amount=amount)
        position['type'] = None
        
while True:
    now = datetime.datetime.now()
    t = now.hour
    h, x = divmod(4,t)

    if x == 3 and now.minute == 55 and (0 <= now.second < 10):
        if op_mode and position['type'] is not None:
            exit_position(binance, symbol, position)
            op_mode = False

    if x == 0 and now.minute == 0 and (0 <= now.second < 10):
        long_target, short_target = larry.cal_target(binance, symbol)
        balance = binance.fetch_balance()
        usdt = balance['free']['USDT']
        op_mode = True
        time.sleep(5)

    ticker = binance.fetch_ticker(symbol)
    cur_price = ticker['last']
    amount = cal_amount(usdt, cur_price)

    if op_mode and position['type'] is None:
        enter_position(binance, symbol, cur_price, long_target, short_target, amount, position)

    if position['type'] == 'long':
        if cur_price < (long_target*0.99):
            exit_position(binance, symbol, position)
    
    if position['type'] == 'short':
        if cur_price > (short_target*1.01):
            exit_position(binance, symbol, position)

    time.sleep(1)
    

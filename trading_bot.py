from os import close
from binance.client import Client
from kucoin.client import Client as kuClient
import json
import pandas as pd
import ta
from ta.volatility import BollingerBands
from datetime import datetime
import time
import csv
from datetime import datetime

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

json_path = "/home/pi/Desktop/python/crypto/config.json"
json_path_kucoin = "/home/pi/Desktop/python/crypto/kucoin_keys.json"

with open(json_path, "r") as f:
    config = json.load(f)

with open(json_path_kucoin, "r") as f:
    config_k = json.load(f)

client = Client(config["api_key"], config["secret_key"])
client_k = kuClient(config_k["api_key"], config_k["api_secret"], config_k["api_passphrase"])

def getMinData (symbol, interval, lookback):
    #returns OHLCV
    frame = pd.DataFrame(client.get_historical_klines(symbol = symbol, interval = interval, start_str= lookback))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame['Time'] = pd.to_datetime(frame['Time'], unit = 'ms')
    frame[['Open', 'High', 'Low', 'Close', 'Volume']] = frame[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    return frame

def applyTechnicals(df):
    df['RSI'] = ta.momentum.rsi(close = df["Close"], window = 14)
    #df["MA200"] = df["Close"].rolling(200).mean()

    indicator_bb = BollingerBands(close = df["Close"], window = 20, window_dev = 2)
    df["bb_bbm"] = indicator_bb.bollinger_mavg()
    df["bb_high_band"] = indicator_bb.bollinger_hband()
    df["bb_low_band"] = indicator_bb.bollinger_lband()

#csv_log = '/home/pi/Desktop/python/crypto/logs/logs.csv'
csv_action = '/home/pi/Desktop/python/crypto/logs/action.csv'

def writeToCSV(csv_path, data):
    with open(csv_path, 'a+', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)

def Signal(pair):

    #checking if there's unfilled order

    if (len(client_k.get_orders(status="active")["items"]) == 0):
 
        action_df = pd.read_csv(csv_action)
        last_action = action_df.iloc[-1]
    
        buyPrice = last_action["Close"] if last_action["Type"] == False else 0
        
        action = []
        lowerB = 30
        higherB = 70

        df = getMinData(pair, '15m', '3 days ago UTC')
        applyTechnicals(df)

        current_row = df.iloc[-1]
        rsi = current_row["RSI"]
        close = current_row["Close"]

        balance_usdt = float(getBalance("USDT"))
        balance_crypto = float(getBalance("XLM"))
    
        buy = True if balance_usdt / close > balance_crypto else False

        if (buy and rsi <= lowerB):

            size = balance_usdt / close * 0.99
            
            try:
                print("Trying to buy: {}".format(size))
                client_k.create_limit_order(symbol='XLM-USDT', side='buy', size=round(size, 2), price=close)

                balance_usdt = getBalance("USDT")
                balance_crypto = getBalance("XLM")

                #Log action; Date,Pair,Type,Close,RSI,Invest,Crypto,Size,Profit,ProfitPCT
                action.append(current_row["Time"])
                action.append(pair)
                action.append(False)
                action.append(close)
                action.append(rsi)
                action.append(size)
                action.append(0)
                action.append(0)
            
                writeToCSV(csv_action, action)
                
                print(now)
                print("Bought| price: {}; size : {}".format(close, size))
            except Exception as e:
                print("Kucoin error while buying has occured", str(e))

        #looking for selling opportunity
        elif (buy == False and rsi >= higherB and buyPrice < close):
            
            size = balance_crypto * 0.99

            try:
                print("Trying to sell: {}".format(size))
                client_k.create_limit_order(symbol='XLM-USDT', side='sell', size=size, price=close)
                
                balance_usdt = getBalance("USDT")
                balance_crypto = getBalance("XLM")

                profit_perc = close / buyPrice - 1
                profit = close - buyPrice

                #Log action; Date,Pair,Type,Close,RSI,Invest,Crypto,Size,Profit,ProfitPCT
                action.append(current_row["Time"])
                action.append(pair)
                action.append(True)
                action.append(close)
                action.append(rsi)
                action.append(size)
                action.append(profit)
                action.append(profit_perc)
                writeToCSV(csv_action, action)
                
                print(now)
                print("Sold| price: {} ; size : {}".format(close, size))
            except Exception as e:
                print("Kucoin error while selling has occured", str(e))

        else:
            print(now)
            if buy:
                print("Looking for buying position.")
                print("It hasn't reached the limit. current price: {}; RSI: {}".format(close, rsi))

            else:
                print("Looking for selling position.")
                print("It hasn't reached the limit. current price: {}; min price: {}; RSI: {}".format(close, buyPrice, rsi))
            
            

    else:
        print(now)
        print("There's an unfilled order!")
    print("-----------")

def getBalance(crypto):
    accounts = pd.DataFrame(client_k.get_accounts())
   
    p1 = accounts.loc[(accounts["type"] == 'trade') & (accounts["currency"] == crypto)]["available"]
    
        
    return "{:.2f}".format(float(p1))



Signal("XLMUSDT")


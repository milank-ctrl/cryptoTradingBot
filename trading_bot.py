from os import close
from binance.client import Client
import json
import pandas as pd
import ta
from datetime import datetime
import time

json_path = "/home/pi/Desktop/python/crypto/config.json"

with open(json_path, "r") as f:
    config = json.load(f)

client = Client(config["api_key"], config["secret_key"])

def getMinData (symbol, interval, lookback):
    #returns OHLCV
    frame = pd.DataFrame(client.get_historical_klines(symbol = symbol, interval = interval, start_str= lookback))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time') 
    frame.index = pd.to_datetime(frame.index, unit = 'ms')
    #frame['Time'] = pd.to_datetime(frame['Time'], unit = 'ms')
    frame = frame.astype(float)
    return frame

def applyTechnicals(df):
    df['RSI'] = ta.momentum.rsi(close = df["Close"], window = 14)
    #df['macd'] = ta.trend.macd_diff(df["Close"])
    #df['%K'] = ta.momentum.stoch(df["High"],df["Low"], df["Close"], window = 14, smooth_window = 3)

#df = getMinData("ETHUSDT", '15m', '12 months ago UTC')
#applyTechnicals(df)
#df.to_csv("eth_test_data.csv")

def Signal(lowerB, higherB):

    global buy
    global invest
    global buyPrice 
    global eth

    df = getMinData("ETHUSDT", '1m', '100 minutes ago UTC')
    applyTechnicals(df)
    current_row = df.iloc[-1]

    print("Current price: {}, RSI: {}".format(current_row["Close"], current_row["RSI"]))
 
    if (buy and current_row["RSI"] <= lowerB):
        trx = {}
        buy = False
        eth = invest / current_row["Close"]
        buyPrice = current_row["Close"]
        trx["Type"] = "Buy"
        #trx["Date"] = str(current_row["Time"])
        trx["Close"] = current_row["Close"]
        log.append(trx)

        print("Bought| price: {}".format(current_row["Close"]))

    #looking for selling opportunity
    elif (buy == False and current_row["RSI"] >= higherB and buyPrice < current_row["Close"]):
        buy = True
        invest = current_row["Close"] * eth
        trx = {}
        trx["Type"] = "Sell"
        #trx["Date"] = str(current_row["Time"])
        trx["Close"] = current_row["Close"]
        log.append(trx)
        print("Sold| price: {} ; profit : {}".format(current_row["Close"], invest))

    #return current_row["Close"], current_row["RSI"]

buy = True
invest = 100
eth = 0
buyPrice = 0
log = []

while True:
    Signal(lowerB=65, higherB=67)
    time.sleep(5)






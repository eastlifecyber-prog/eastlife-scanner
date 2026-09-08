# app.py - PRO Scanner for Render
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","GBPJPY=X","EURJPY=X","BTC-USD","GC=F","EURGBP=X"]

def scan_pair(symbol, timeframe):
    interval_map = {"5m":"5m","15m":"15m","1h":"60m","4h":"4h","1d":"1d"}
    range_map = {"5m":"1d","15m":"5d","1h":"1mo","4h":"3mo","1d":"1y"}
    
    tf = interval_map.get(timeframe, "15m")
    rg = range_map.get(timeframe, "5d")
    
    try:
        df = yf.download(symbol, period=rg, interval=tf, progress=False)
        if len(df) < 200: return None
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['EMA200'] = df['Close'].ewm(span=200).mean()
        
        last = df.iloc[-1]
        close = float(last['Close'])
        ema50 = float(last['EMA50'])
        ema200 = float(last['EMA200'])
        
        # AI Score - how far from EMA
        distance = abs(close - ema50) / close * 1000
        
        if close > ema50 > ema200:
            return {"pair":symbol.replace("=X",""), "price":round(close,4), "trend":"BUY TREND", "score":min(95, 70+distance*2), "color":"green", "tf":timeframe}
        elif close < ema50 < ema200:
            return {"pair":symbol.replace("=X",""), "price":round(close,4), "trend":"SELL TREND", "score":min(95, 70+distance*2), "color":"red", "tf":timeframe}
        else:
            return {"pair":symbol.replace("=X",""), "price":round(close,4), "trend":"RANGING", "score":30, "color":"gray", "tf":timeframe}
    except:
        return None

@app.route('/scan')
def scan():
    tf = request.args.get('tf', '1h') # default 1H now
    results = []
    for p in PAIRS:
        r = scan_pair(p, tf)
        if r: results.append(r)
    # Sort by score - best trend first (AI ranking)
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return jsonify(results)

@app.route('/')
def home():
    return "EastLife Scanner API LIVE - use /scan?tf=1h"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

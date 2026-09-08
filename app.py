from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","GBPJPY=X","EURJPY=X","EURGBP=X","USDCHF=X","NZDUSD=X","BTC-USD","ETH-USD","GC=F","SI=F","NQ=F"]

def scan_pair(symbol, tf):
    try:
        interval = {"5m":"5m","15m":"15m","1h":"60m","4h":"60m","1d":"1d"}.get(tf,"60m")
        period = {"5m":"5d","15m":"5d","1h":"1mo","4h":"3mo","1d":"1y"}.get(tf,"1mo")
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if len(df) < 50: return None

        close = df['Close']
        if isinstance(close, pd.DataFrame): close = close.iloc[:,0]
        high = df['High'].iloc[:,0] if isinstance(df['High'], pd.DataFrame) else df['High']
        low = df['Low'].iloc[:,0] if isinstance(df['Low'], pd.DataFrame) else df['Low']

        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean()
        ema200 = close.ewm(span=200).mean()

        # ATR for TP/SL
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        c = float(close.iloc[-1])
        e20 = float(ema20.iloc[-1]); e50 = float(ema50.iloc[-1]); e200 = float(ema200.iloc[-1])
        atr_v = float(atr.iloc[-1])
        # Fix small ATR
        if atr_v < c*0.0005: atr_v = c*0.001

        # Logic
        score=40; trend="RANGING"; color="gray"; direction=""

        if c > e20 > e50 and e50 > e200: trend="STRONG BUY"; score=95; color="green"; direction="BUY"
        elif c > e20 and e20 > e50: trend="BUY TREND"; score=80; color="green"; direction="BUY"
        elif c > e50: trend="WEAK BUY"; score=60; color="green"; direction="BUY"
        elif c < e20 < e50 and e50 < e200: trend="STRONG SELL"; score=95; color="red"; direction="SELL"
        elif c < e20 and e20 < e50: trend="SELL TREND"; score=80; color="red"; direction="SELL"
        elif c < e50: trend="WEAK SELL"; score=60; color="red"; direction="SELL"

        if direction == "":
            return {"pair":symbol.replace("=X","").replace("-USD",""), "price":round(c,5), "trend":trend, "score":score, "color":color, "tf":tf, "entry":round(c,5), "sl":0, "tp1":0, "tp2":0, "dir":direction}

        # Calculate TP/SL based on ATR (real trading logic)
        if direction == "BUY":
            entry = c
            sl = entry - (atr_v * 1.5)
            tp1 = entry + (atr_v * 1.5)
            tp2 = entry + (atr_v * 3)
        else:
            entry = c
            sl = entry + (atr_v * 1.5)
            tp1 = entry - (atr_v * 1.5)
            tp2 = entry - (atr_v * 3)

        return {
            "pair": symbol.replace("=X","").replace("-USD",""), 
            "price": round(c,5), 
            "trend": trend, "score": score, "color": color, "tf": tf,
            "entry": round(entry,5), "sl": round(sl,5), "tp1": round(tp1,5), "tp2": round(tp2,5),
            "dir": direction
        }
    except Exception as e:
        print(e)
        return None

@app.route('/scan')
def scan():
    tf = request.args.get('tf','1h')
    results = []
    for p in PAIRS:
        r = scan_pair(p, tf)
        if r: results.append(r)
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return jsonify(results)

@app.route('/')
def home(): return "EastLife PRO V4 - TP/SL"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

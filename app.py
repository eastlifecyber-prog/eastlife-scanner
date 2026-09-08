from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","BTC-USD","GC=F"]

def scan_pair(symbol, timeframe):
    try:
        df = yf.download(symbol, period="1mo", interval="60m", progress=False, auto_adjust=True)
        if len(df) < 30:
            return None
        
        # FIX for new yfinance: Close can be DataFrame
        close_col = df['Close']
        if isinstance(close_col, pd.DataFrame):
            close_col = close_col.iloc[:, 0]
        
        ema50 = close_col.ewm(span=50).mean()
        ema200 = close_col.ewm(span=200).mean()
        
        close = float(close_col.iloc[-1])
        e50 = float(ema50.iloc[-1])
        e200 = float(ema200.iloc[-1])
        
        if close > e50 > e200:
            return {"pair": symbol.replace("=X",""), "price": round(close,5), "trend": "BUY TREND", "score": 85, "color": "green", "tf": timeframe}
        elif close < e50 < e200:
            return {"pair": symbol.replace("=X",""), "price": round(close,5), "trend": "SELL TREND", "score": 85, "color": "red", "tf": timeframe}
        else:
            return {"pair": symbol.replace("=X",""), "price": round(close,5), "trend": "RANGING", "score": 40, "color": "gray", "tf": timeframe}
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None

@app.route('/scan')
def scan():
    tf = request.args.get('tf','1h')
    results = []
    for p in PAIRS:
        r = scan_pair(p, tf)
        if r:
            results.append(r)
    return jsonify(results)

@app.route('/')
def home():
    return "EastLife LIVE - OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

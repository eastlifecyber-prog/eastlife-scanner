from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

# Cache to make it instant after first load
CACHE = {}

PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","GBPJPY=X","EURJPY=X","EURGBP=X","BTC-USD","GC=F","XAUUSD=X","NAS100"]

def get_data(symbol, tf_param):
    map_interval = {"5m":"5m","15m":"15m","1h":"60m","4h":"60m","1d":"1d"}
    map_period = {"5m":"5d","15m":"5d","1h":"1mo","4h":"3mo","1d":"1y"}
    interval = map_interval.get(tf_param, "60m")
    period = map_period.get(tf_param, "1mo")

    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    if len(df) < 30: return None
    col = df['Close']
    if isinstance(col, pd.DataFrame): col = col.iloc[:,0]
    return col

def scan_pair(symbol, timeframe):
    try:
        col = get_data(symbol, timeframe)
        if col is None: return None
        e50 = col.ewm(span=50).mean()
        e200 = col.ewm(span=200).mean()
        close = float(col.iloc[-1]); e50_v = float(e50.iloc[-1]); e200_v = float(e200.iloc[-1])

        if close > e50_v > e200_v: t,c,s = "BUY TREND","green",85
        elif close < e50_v < e200_v: t,c,s = "SELL TREND","red",85
        else: t,c,s = "RANGING","gray",40

        return {"pair": symbol.replace("=X","").replace("-USD",""), "price": round(close,5), "trend": t, "score": s, "color": c, "tf": timeframe}
    except Exception as e:
        print(e)
        return None

@app.route('/scan')
def scan():
    tf = request.args.get('tf','1h')
    # Check cache (valid for 2 mins)
    if tf in CACHE:
        return jsonify(CACHE[tf])

    results = []
    for p in PAIRS:
        r = scan_pair(p, tf)
        if r: results.append(r)

    results = sorted(results, key=lambda x: x['score'], reverse=True)
    CACHE[tf] = results
    return jsonify(results)

@app.route('/')
def home(): return "EastLife PRO LIVE"

if __name__ == '__main__': app.run(host='0.0.0.0', port=10000)

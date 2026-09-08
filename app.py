from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__)
CORS(app)

PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","GBPJPY=X","EURJPY=X","BTC-USD","GC=F","EURGBP=X"]

def scan_pair(symbol, timeframe):
    interval_map = {"5m":"5m","15m":"15m","1h":"60m","4h":"60m","1d":"1d"}
    range_map = {"5m":"5d","15m":"5d","1h":"1mo","4h":"3mo","1d":"1y"}
    
    tf = interval_map.get(timeframe, "15m")
    rg = range_map.get(timeframe, "5d")
    
    try:
        df = yf.download(symbol, period=rg, interval=tf, progress=False, auto_adjust=True)
        if len(df) < 50: return None
        
        # Fix for yfinance new format
        if 'Close' in df.columns:
            close_series = df['Close']
        else:
            close_series = df.iloc[:,0]
            
        df['EMA50'] = close_series.ewm(span=50).mean()
        df['EMA200'] = close_series.ewm(span=200).mean()
        
        last = df.iloc[-1]
        close = float(close_series.iloc[-1])
        ema50 = float(df['EMA50'].iloc[-1])
        ema200 = float(df['EMA200'].iloc[-1])
        
        if close > ema50 > ema200:
            return {"pair":symbol.replace("=X","").replace("-USD","/USD"), "price":round(close,5), "trend":"BUY TREND", "score":85, "color":"green", "tf":timeframe}
        elif close < ema50 < ema200:
            return {"pair":symbol.replace("=X","").replace("-USD","/USD"), "price":round(close,5), "trend":"SELL TREND", "score":85, "color":"red", "tf":timeframe}
        else:
            return {"pair":symbol.replace("=X","").replace("-USD","/USD"), "price":round(close,5), "trend":"RANGING", "score":40, "color":"gray", "tf":timeframe}
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None

@app.route('/scan')
def scan():
    tf = request.args.get('tf', '1h')
    results = []
    for p in PAIRS:
        r = scan_pair(p, tf)
        if r: results.append(r)
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return jsonify(results)

@app.route('/')
def home():
    return "EastLife Scanner API LIVE"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__)
CORS(app)

PAIRS = ["EURUSD=X","GBPUSD=X","BTC-USD","XAUUSD=X","USDJPY=X"] # 5 only for speed

def scan_pair(symbol, timeframe):
    try:
        # Use 60m for all to be fast
        df = yf.download(symbol, period="5d", interval="60m", progress=False)
        if len(df) < 30:
            return None
        close = float(df['Close'].iloc[-1])
        ema50 = float(df['Close'].ewm(span=50).mean().iloc[-1])
        ema200 = float(df['Close'].ewm(span=200).mean().iloc[-1])
        
        trend = "RANGING"
        color = "gray"
        score = 45
        if close > ema50 > ema200:
            trend = "BUY TREND"
            color = "green"
            score = 85
        elif close < ema50 < ema200:
            trend = "SELL TREND"
            color = "red"
            score = 85
            
        return {"pair": symbol.replace("=X","").replace("-USD",""), "price": round(close,4), "trend": trend, "score": score, "color": color, "tf": timeframe}
    except:
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
    return "EastLife LIVE"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

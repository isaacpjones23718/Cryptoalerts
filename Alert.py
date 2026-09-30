Here's the script. Long-press it and copy the whole thing.

```python
import os, json, requests, pandas as pd

TOKEN   = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]
STATE   = "state.json"

COINS = {
    "FET-USD":  {"support": 0.200, "resistance": 0.280},
    "BTC-USD":  {"support": 90000, "resistance": 120000},
    "SOL-USD":  {"support": 120,   "resistance": 200},
    "SUI-USD":  {"support": 2.00,  "resistance": 3.50},
    "HBAR-USD": {"support": 0.150, "resistance": 0.250},
    "NEAR-USD": {"support": 2.00,  "resistance": 4.00},
}

RSI_OVERSOLD, RSI_OVERBOUGHT = 30, 70

def candles(product, granularity=300):
    url = f"https://api.exchange.coinbase.com/products/{product}/candles"
    r = requests.get(url, params={"granularity": granularity}, timeout=10)
    r.raise_for_status()
    df = pd.DataFrame(r.json(), columns=["time","low","high","open","close","volume"])
    return df.sort_values("time").reset_index(drop=True)

def rsi(s, period=14):
    d = s.diff()
    gain = d.clip(lower=0).rolling(period).mean()
    loss = -d.clip(upper=0).rolling(period).mean()
    return 100 - (100 / (1 + gain / loss))

def send(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  json={"chat_id": CHAT_ID, "text": msg}, timeout=10)

prev = json.load(open(STATE)) if os.path.exists(STATE) else {}
now = {}

for product, levels in COINS.items():
    try:
        df = candles(product)
        df["rsi14"] = rsi(df["close"])
        price = float(df.iloc[-1].close)
        r14   = float(df.iloc[-1].rsi14)
    except Exception as e:
        print(f"{product}: {e}")
        continue

    hits = []
    if price <= levels["support"]:
        hits.append(f"{product} at support: ${price:,.4f}")
    if price >= levels["resistance"]:
        hits.append(f"{product} at resistance: ${price:,.4f}")
    if r14 <= RSI_OVERSOLD:
        hits.append(f"{product} oversold: RSI {r14:.1f} at ${price:,.4f}")
    if r14 >= RSI_OVERBOUGHT:
        hits.append(f"{product} overbought: RSI {r14:.1f} at ${price:,.4f}")

    for h in hits:
        key = h.split(":")[0]
        now[key] = True
        if prev.get(key):
            send(h)

json.dump(now, open(STATE, "w"))
```

Two notes. Those support and resistance numbers are placeholders — you'll want to set your own levels for each coin. And nothing fires the first time a level trips; it waits for a second consecutive check, so you don't get alerted by a single wick.

Copied it?

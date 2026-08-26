import os, time, threading, sqlite3, math
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
app=FastAPI(title="Market Intelligence - Angel One")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

latest={}
prev={}
status={"connected":False,"message":"Not connected"}
smart=None
sws=None

# Add Angel One instrument tokens here or load them from Angel One's published scrip master.
# Example format: {"RELIANCE":"2885","TCS":"11536"}
TOKENS={}
EXCHANGE_TYPE=1  # NSE_CM

def activity(symbol, price, volume=None):
    p0=prev.get(symbol, price)
    move=(price/p0-1)*100 if p0 else 0
    # This is a starter heuristic. Production score must be calibrated from historical data.
    rv=latest.get(symbol,{}).get("rvol",1.0)
    score=min(99,max(0,round(abs(move)*20+max(0,rv-1)*10)))
    return move,score

def on_data(wsapp, message):
    try:
        # SmartWebSocketV2 delivers binary packets; official SDK exposes parsed callback
        # depending on SDK version. If dict is received, use it directly.
        if isinstance(message,dict):
            data=message
        else:
            return
        token=str(data.get("token",""))
        symbol=next((s for s,t in TOKENS.items() if str(t)==token),token)
        price=float(data.get("last_traded_price",data.get("ltp",0)) or 0)
        if price:
            price=price/100 if price>100000 else price
            old=latest.get(symbol,{})
            prev[symbol]=old.get("price",price)
            latest[symbol]={**old,"symbol":symbol,"price":price,
                            "volume":data.get("volume_trade_for_the_day",data.get("volume",0)),
                            "ts":datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        status["message"]=f"tick parse error: {e}"

def on_open(wsapp):
    status.update(connected=True,message="Angel One WebSocket connected")
    if TOKENS:
        token_list=[{"exchangeType":EXCHANGE_TYPE,"tokens":[str(v) for v in TOKENS.values()]}]
        try:
            # mode 1 = LTP in SmartWebSocketV2
            sws.subscribe("market-intelligence",1,token_list)
        except Exception as e:
            status["message"]=f"subscribe error: {e}"

def on_error(wsapp,error):
    status.update(connected=False,message=str(error))

def on_close(wsapp):
    status.update(connected=False,message="Angel One WebSocket closed")

def start_socket():
    global smart,sws
    try:
        from SmartApi import SmartConnect
        import pyotp
        client=os.getenv("ANGEL_CLIENT_CODE")
        key=os.getenv("ANGEL_API_KEY")
        pwd=os.getenv("ANGEL_PASSWORD_OR_PIN")
        totp_secret=os.getenv("ANGEL_TOTP_SECRET")
        if not all([client,key,pwd,totp_secret]):
            status["message"]="Credentials missing in .env"
            return
        smart=SmartConnect(api_key=key)
        session=smart.generateSession(client,pwd,pyotp.TOTP(totp_secret).now())
        feed=smart.getfeedToken()
        jwt=session["data"]["jwtToken"]
        from SmartApi.smartWebSocketV2 import SmartWebSocketV2
        sws=SmartWebSocketV2(jwt, key, client, feed)
        sws.on_data=on_data
        sws.on_open=on_open
        sws.on_error=on_error
        sws.on_close=on_close
        sws.connect()
    except Exception as e:
        status.update(connected=False,message=f"Connection failed: {e}")

@app.on_event("startup")
def startup():
    threading.Thread(target=start_socket,daemon=True).start()

@app.get("/health")
def health(): return {"ok":True,**status}

@app.get("/scanner")
def scanner():
    rows=[]
    for symbol,x in latest.items():
        move,score=activity(symbol,x["price"],x.get("volume"))
        rows.append({**x,"change_from_last_tick":round(move,3),
                     "activity_score":score,
                     "state":"PRE-EVENT" if score>=70 else ("WATCH" if score>=45 else "NORMAL")})
    return {"timestamp":datetime.now(timezone.utc).isoformat(),"connection":status,"data":rows}

@app.get("/config")
def config():
    return {"symbols":list(TOKENS.keys()),"configured":bool(TOKENS),
            "note":"Set TOKENS in main.py or load an instrument-token map."}

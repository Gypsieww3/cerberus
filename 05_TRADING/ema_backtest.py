"""Offline long/flat toy EMA strategy, orders never sent to brokers."""
import math
def _prices(sequence):
    values=list(sequence)
    if len(values)<3 or len(values)>1000000 or any(isinstance(v,bool) or not isinstance(v,(int,float))
       or not math.isfinite(v) or v<=0 for v in values):
        raise ValueError("Need at least three finite positive prices")
    return [float(v) for v in values]
def ema(values,period):
    values=_prices(values)
    if type(period) is not int or period<2: raise ValueError("Invalid period")
    alpha=2/(period+1)
    output=[values[0]]
    for price in values[1:]: output.append(alpha*price+(1-alpha)*output[-1])
    return output
def backtest(closes,fast=5,slow=20,starting_cash=1000,fee_per_order=0.0,slippage_fraction=0.0):
    values=_prices(closes)
    if type(fast) is not int or type(slow) is not int or not 2<=fast<slow<len(values):
        raise ValueError("Must have 2<=fast<slow<total observations")
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x)
           for x in (starting_cash,fee_per_order,slippage_fraction)):
        raise ValueError("Invalid fees or cash")
    if starting_cash<=0 or fee_per_order<0 or not 0<=slippage_fraction<0.25:
        raise ValueError("Invalid trading cost configuration")
    short,long=ema(values,fast),ema(values,slow)
    cash,shares,trades=float(starting_cash),0,[]
    for i in range(slow-1,len(values)-1):
        before=short[i-1]-long[i-1]
        after=short[i]-long[i]
        # Signal on observation i: deterministic approximate fill on next observed close.
        if before<=0<after and shares==0:
            fill=values[i+1]*(1+slippage_fraction)
            qty=max(0,math.floor((cash-fee_per_order)/fill))
            if qty:
                cash-=qty*fill+fee_per_order
                shares=qty
                trades.append(dict(side="BUY",signal_index=i,fill_index=i+1,qty=qty))
        elif before>=0>after and shares:
            fill=values[i+1]*(1-slippage_fraction)
            cash+=shares*fill-fee_per_order
            trades.append(dict(side="SELL",signal_index=i,fill_index=i+1,qty=shares))
            shares=0
    equity=cash+shares*values[-1]
    return dict(initial_equity=float(starting_cash),final_equity=round(equity,6),
                return_pct=round(100*(equity/starting_cash-1),6),trades=trades,
                open_shares=shares,mode="OFFLINE_PAPER_ONLY",
                caveat="Next observed close fill is a proxy, not a tradable price")

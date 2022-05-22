import matplotlib.pyplot as plt
from causis_api.const import get_version
from causis_api.const import login
login.username = "yuhao.zheng"
login.password = "Aiamaman369@"
login.version = get_version()

# 1. package
import os
import numpy as np
import pandas as pd
import datetime

# 2. parameter
half_life = 20  # set half-life period as the window for moving average
sigma_times = 0.75  # up and down boundaries are mean +/- sigma_times * std
BB_times = 0.75  # up and down Bollinger Bands are MA +/- BB_times * roling_std

# 3. environment variable
path = r"D:\work\CTA\data\day_20220319"
productCode = ["R.CN.SHF.rb.0004", "R.CN.DCE.i.0004", "R.CN.CZC.SM.0004"]
index = {"R.CN.SHF.rb.0004": "rb", "R.CN.DCE.i.0004": "i", "R.CN.CZC.SM.0004": "SM"}
trade_fee = {"rb": 0.0001, "i": 0.0001, "SM": 3}
multiplier = {"rb": 10, "i": 100, "SM": 5}
weight = {"rb": 1, "i": -0.75038229, "SM": -0.12836106}
anchor = "rb"
history = "2017-01-01"
begin = "2017-03-19"
end = "2021-03-19"
outsample = "2022-03-18"
allocation = 1000000
volume = 100
trade_unit = {}
for i in weight:
    trade_unit[i] = round(volume*weight[i]*multiplier[anchor]/multiplier[i])

# 4. get data
def get_data(path, productCode, begin, end, columns=None):
    productCode = productCode if type(productCode) == list else [productCode]
    index = ["CLOCK", "SYMBOL"]
    columns = [] if columns is None else (index + columns if type(columns) == list else index + [columns])
    df = pd.DataFrame()
    for i in productCode:
        temp = pd.read_csv(os.path.join(path, i+".csv"))
        columns = temp.columns if len(columns) == 0 else columns
        temp = temp[(temp["CLOCK"] >= begin) & (temp["CLOCK"] <= end)][columns]
        df = pd.concat([df, temp])
    df.sort_values(by=index, inplace=True)
    df.set_index(index, inplace=True)
    return df

# 5. get signal
def get_signal(data, half_life, sigma_times, BB_times, begin, end, figure=False):
    global index, weight
    pdf = data[["CLOSE", "ADJ"]].copy()
    pdf["adj_close"] = pdf["CLOSE"]*pdf["ADJ"]
    pdf = pdf.unstack()["adj_close"].rename(columns=index)
    W = np.array([weight[i] for i in pdf.columns])
    pdf["MR"] = pdf.values.dot(W)  # mean reverting series
    mean, std = pdf["MR"].mean(), pdf["MR"].std()  # mean and sigma
    pdf["mean"], pdf["up"], pdf["down"] = mean, mean + sigma_times * std, mean - sigma_times * std
    pdf["BBMean"] = pdf["MR"].rolling(round(half_life)).mean()  # Bollinger Band
    pdf["BBstd"] = BB_times * pdf["MR"].rolling(round(half_life)).std()
    pdf["BBUp"] = pdf["BBMean"] + pdf["BBstd"]
    pdf["BBDown"] = pdf["BBMean"] - pdf["BBstd"]
    pdf.drop(list(index.values())+["BBstd"], axis=1, inplace=True)
    pdf = pdf[(pdf.index>=begin)&(pdf.index<=end)]

    # generate signal
    signal_list = [0]
    n = len(pdf)
    position = 0  # position state
    position_list = [position]
    up_flag, dw_flag = False, False  # beyond boundaries?
    for i in range(1, n, 1):
        signal = 0
        if position == 1:  # long position
            # sell when up cross mean
            cond_1 = (pdf["MR"].iloc[i-1]<pdf["mean"].iloc[i-1]) and (pdf["MR"].iloc[i]>=pdf["mean"].iloc[i])
            if cond_1:
                signal = -1
                position = 0
        elif position == -1:  # short position
            # cover when down cross mean
            cond_1 = (pdf["MR"].iloc[i-1]>=pdf["mean"].iloc[i-1]) and (pdf["MR"].iloc[i]<pdf["mean"].iloc[i])
            if cond_1:
                signal = 1
                position = 0
        if position == 0:  # empty position, ready to trade!
            if up_flag:
                # 1. down cross Bollinger Down Band
                cond_1 = (pdf["MR"].iloc[i-1]>=pdf["BBDown"].iloc[i-1]) and (pdf["MR"].iloc[i]<pdf["BBDown"].iloc[i])
                # 2. down cross Mean Revert Up Band
                cond_2 = (pdf["MR"].iloc[i-1]>=pdf["up"].iloc[i-1]) and (pdf["MR"].iloc[i]<pdf["up"].iloc[i])
                if cond_1 or cond_2:
                    signal = -1 if signal == 0 else -2  # cover first and then open a new position
                    position = -1
            elif dw_flag:  # there is no way for up_flag and dw_flag to be True at the same time
                # 1. up cross Bollinger Up Band
                cond_1 = (pdf["MR"].iloc[i-1]<pdf["BBUp"].iloc[i-1]) and (pdf["MR"].iloc[i]>=pdf["BBUp"].iloc[i])
                # 2. up cross Mean Revert Up Band
                cond_2 = (pdf["MR"].iloc[i-1]<pdf["down"].iloc[i-1]) and (pdf["MR"].iloc[i]>=pdf["down"].iloc[i])
                if cond_1 or cond_2:
                    signal = 1 if signal == 0 else 2
                    position = 1
        if (pdf["MR"].iloc[i-1]<pdf["up"].iloc[i-1]) and (pdf["MR"].iloc[i]>=pdf["up"].iloc[i]):
            up_flag = True
        elif (pdf["MR"].iloc[i-1]>=pdf["up"].iloc[i-1]) and (pdf["MR"].iloc[i]<pdf["up"].iloc[i]):
            up_flag = False
        if (pdf["MR"].iloc[i-1]>=pdf["down"].iloc[i-1]) and (pdf["MR"].iloc[i]<pdf["down"].iloc[i]):
            dw_flag = True
        elif (pdf["MR"].iloc[i-1]<pdf["down"].iloc[i-1]) and (pdf["MR"].iloc[i]>=pdf["down"].iloc[i]):
            dw_flag = False
        signal_list.append(signal)
        position_list.append(position)
    pdf["signal"] = signal_list
    pdf["signal"] = pdf["signal"].shift(1).fillna(0)  # trade in next day
    pdf["position"] = position_list
    pdf["position"] = pdf["position"].shift(1).fillna(0)  # trade in next day
    if pdf["signal"].iloc[-1] != 0:
        pdf["signal"].iloc[-1] = -1*position  # cover in the end

    # visualization
    if figure:
        visual_sig = pdf[["MR", "mean", "up", "down", "signal", "position"]].copy()
        visual_sig["buy"] = visual_sig[visual_sig["signal"] > 0]["MR"]
        visual_sig["sell"] = visual_sig[visual_sig["signal"] < 0]["MR"]
        plt.figure(figsize=(12, 4))
        plt.bar(visual_sig.index, visual_sig["position"], alpha=0.5, color="black", label="position")
        plt.xticks([visual_sig.index[i] for i in range(0, len(visual_sig), 200)])
        plt.legend(loc="upper right")
        ax = plt.twinx()
        ax.plot(visual_sig.index, visual_sig["MR"], label="Spread")
        ax.plot(visual_sig.index, visual_sig["mean"], label="mean")
        ax.plot(visual_sig.index, visual_sig["up"], label="up")
        ax.plot(visual_sig.index, visual_sig["down"], label="down")
        ax.plot(visual_sig.index, visual_sig["buy"], "ro", label="long")
        ax.plot(visual_sig.index, visual_sig["sell"], "go", label="short")
        plt.xticks([visual_sig.index[i] for i in range(0, len(visual_sig), 200)])
        plt.legend(loc="upper left")
        plt.title("Signal & Position")
        plt.show()

    return pdf[["signal"]]

# 6~8. back-test to get trading order/position/pnl
def back_test(quote, category, multiplier, trade_unit, trade_fee):
    df = quote.copy()
    multi, unit, fee = multiplier[category], trade_unit[category], trade_fee[category]
    flag = np.sign(df["signal"].iloc[0])
    pnl, cost = [0], [0 if flag == 0 else 1]
    date = [] if flag == 0 else [df.index[0]]
    order = [] if flag == 0 else [flag*unit]
    price = [] if flag == 0 else [df[category].iloc[0]]
    position = [0 if flag == 0 else flag*unit]
    n = len(df)
    for i in range(1, n, 1):
        profit, pay = 0, 0
        profit = df[category].iloc[i]-df[category].iloc[i-1]
        pnl.append(flag*profit)
        if df["signal"].iloc[i] != 0:  # trading
            if flag == 0:  # open position
                pay = 1
                flag = np.sign(df["signal"].iloc[i])
                date.append(df.index[i])
                order.append(flag*unit)
                price.append(df[category].iloc[i])
            else:  # cover position
                if flag != np.sign(df["signal"].iloc[i]):  # skip same signal
                    if abs(df["signal"].iloc[i]) == 1:
                        pay = 0
                        flag = 0
                    else:  # cover and open
                        pay = 1
                        flag = np.sign(df["signal"].iloc[i])
                    date.append(df.index[i])
                    order.append(-1*order[-1]+flag*unit)
                    price.append(df[category].iloc[i])
        cost.append(pay)
        position.append(flag*unit)
    if position[-1]!=0:  # cover position
        cost[-1] = 0
        date.append(df.index[-1])
        order.append(-1*order[-1])
        price.append(df[category].iloc[-1])
        position[-1] = 0
    df["pnl"], df["cost"] = pnl, cost
    df["pnl"] = df["pnl"]*unit
    df["cost"] = df["cost"]*unit*fee*(1 if fee >= 1 else multi*df[category])  # %fee/unit or fee/trade
    df["qty"] = position
    trading_order = pd.DataFrame({"time": date, "qty": order, "price": price})
    position_order = df[["qty"]].copy().reset_index().rename(columns={"CLOCK": "time"})
    return trading_order, position_order, df["pnl"]-df["cost"]

def get_backtest(signal):
    global data, index, multiplier, weight, anchor, volume, trade_unit, trade_fee, allocation
    quote = data[["OPEN", "CLOSE"]].copy()
    quote["VWAP"] = (quote["OPEN"]+quote["CLOSE"])/2
    quote = quote.unstack()["VWAP"].rename(columns=index)
    quote = pd.concat([quote, signal], axis=1, join="inner")

    trading_order, trading_position = pd.DataFrame(), pd.DataFrame()
    pnl_list = []
    n = len(index)
    for i in range(n):
        code = list(index.keys())[i]
        pnl_list.append("pnl_%s" % index[code])
        temp_order, temp_position, quote["pnl_%s" % index[code]] = back_test(quote, index[code], multiplier, trade_unit, trade_fee)
        temp_order["productCode"] = code
        temp_order["filledPrice"] = temp_order["price"]
        temp_order = temp_order[["time", "productCode", "qty", "price", "filledPrice"]]
        trading_order = pd.concat([trading_order, temp_order])
        temp_position["productCode"] = code
        temp_position = temp_position[["time", "productCode", "qty"]]
        trading_position = pd.concat([trading_position, temp_position])

    trading_order.sort_values(by=["time", "productCode"], inplace=True)
    trading_position.sort_values(by=["time", "productCode"], inplace=True)
    quote["interPNL"] = quote[pnl_list].sum(axis=1)
    quote["balance"] = allocation+quote["interPNL"].cumsum()
    trading_pnl = quote[["interPNL", "balance"]].copy().reset_index().rename(columns={"CLOCK": "time"})
    return trading_order, trading_position, trading_pnl

# 9. Execute Strategy and Analyze
def get_analysis(trading_pnl, figure=False):
    global allocation
    stat = {}
    df = trading_pnl.copy()
    df["time"] = df["time"].apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"))
    df["cum"] = df["interPNL"].cumsum()
    stat["AnnRtn"] = (df["cum"].iloc[-1]/allocation)/(((df["time"].iloc[-1]-df["time"].iloc[0]).days+1)/365)
    stat["MDD"] = np.max(np.maximum.accumulate(df["cum"].values)-df["cum"].values)
    stat["Sharpe"] = np.sqrt(365)*df["interPNL"].mean()/df["interPNL"].std()
    stat["Calmar"] = stat["AnnRtn"]/stat["MDD"]

    n = len(df)
    period, win, loss = [], [], []
    start_date, profit = df["time"].iloc[0], df["interPNL"].iloc[0]
    for i in range(1, n, 1):
        if df["interPNL"].iloc[i]!=0 and df["interPNL"].iloc[i-1]==0:
            start_date = df["time"].iloc[i]
        elif df["interPNL"].iloc[i]==0 and df["interPNL"].iloc[i-1]!=0:
            period.append((df["time"].iloc[i]-start_date).days)
            if profit>0:
                win.append(profit)
            elif profit<0:
                loss.append(profit)
            profit = 0
        profit += df["interPNL"].iloc[i]
    if profit!=0:
        period.append((df["time"].iloc[-1]-start_date).days+1)
        if profit > 0:
            win.append(profit)
        elif profit < 0:
            loss.append(profit)

    stat["WinRate"] = len(win)/(len(win)+len(loss))
    stat["PnL Ratio"] = -np.mean(win)/(np.mean(loss))
    stat["AvgPeriod"] = np.mean(period)

    if figure:
        df[["time", "cum"]].set_index("time").plot(figsize=(12, 4), title="PNL", legend=False)
        plt.show()

    return stat

data = get_data(path, productCode, history, outsample)
signal = get_signal(data, half_life, sigma_times, BB_times, begin, end)
trading_order, trading_position, trading_pnl = get_backtest(signal)
stat = get_analysis(trading_pnl, True)

signal_o = get_signal(data, half_life, sigma_times, BB_times, end, outsample)
trading_order_o, trading_position_o, trading_pnl_o = get_backtest(signal_o)
stat_o = get_analysis(trading_pnl_o, True)

# 10. Parameter Sensitivity
sigma_list = np.linspace(0.25, 0.9, 27)
sharpe_list = []
for i in sigma_list:
    signal_temp = get_signal(data, half_life, i, BB_times, begin, end)
    temp_order, temp_position, temp_pnl = get_backtest(signal_temp)
    temp_stat = get_analysis(temp_pnl)
    sharpe_list.append(temp_stat["Sharpe"])
plt.figure(figsize=(12, 4))
plt.plot(sigma_list, sharpe_list)
plt.xticks(sigma_list, rotation=30)
plt.title("sharpe - sigma times")
plt.show()

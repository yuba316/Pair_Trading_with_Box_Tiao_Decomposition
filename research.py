'''
from causis_api.const import get_version
from causis_api.const import login
login.username = "yuhao.zheng"
login.password = "Aiamaman369@"
login.version = get_version()
'''
import os
import numpy as np
import pandas as pd
from scipy.stats import norm
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import seaborn as sns
import matplotlib.pyplot as plt
# import causis_api.data as caud

# 本地数据下载>Week1>商品期货数据>商品期货数据_日线_20220319.zip 解压路径
path = r"D:\work\CTA\data\day_20220319"
# back-test period and out-of-sample period
history, start_date, insample, end_date = "2016-03-19", "2017-03-19", "2021-03-19", "2022-03-18"  # 5 years
# categories need researching: steel & coal industry
steel = ["rb", "i", "hc", "SM"]
coal = ["j", "jm"]

# 1. data processing
# info = caud.all_instruments("R")
future_list = os.listdir(path)  # file name of all categories
future_dir = {}
n = len(future_list)
for i in range(n):
    name = future_list[i].split(".")[-3]
    if name not in steel+coal:  # only consider steel or coal industry
        continue
#     if info[info["Code"]==name]["BeginDate"].iloc[0] > history:  # at least traded more than one year
#         continue
    temp = pd.read_csv(os.path.join(path, future_list[i]))
    temp = temp[temp["VOLUME"] != 0].dropna().reset_index(drop=True)  # volume=0 means no trading at that date
    if temp["CLOCK"].iloc[0] > start_date or temp["CLOCK"].iloc[-1] < end_date:
        continue
    future_dir[name] = temp

# set the unique trading calendar
# trading_date = caud.get_trading_dates(start_date, end_date)
# trading_date = pd.DataFrame({"CLOCK": trading_date})
trading_date = future_dir["rb"][(future_dir["rb"]["CLOCK"]>=start_date)&(future_dir["rb"]["CLOCK"]<=end_date)][["CLOCK"]]
trading_date.sort_values(by="CLOCK", inplace=True)
def data_processing(temp, trading_date):
    # get adjusted price divided by mean to unitize data
    df = temp.copy()
    df["adj_close"] = df["CLOSE"]*df["ADJ"]
    df["uni_close"] = df["adj_close"]/df["adj_close"].mean()
    # make sure that data has covered all the trading days
    # there is no nan value in this case
    df = pd.merge(trading_date, df, how="left", on="CLOCK")
    df.set_index("CLOCK", inplace=True)
    return df
for i in future_dir.keys():
    temp = data_processing(future_dir[i], trading_date)
    future_dir[i] = temp

# 2. Visualize Correlation
trend = pd.concat([future_dir[i][(start_date<=future_dir[i].index)&(future_dir[i].index<=insample)]
                   [["uni_close"]].rename(columns={"uni_close": i}) for i in future_dir.keys()], axis=1)
trend.plot(figsize=(12, 4), title="Steel Industry Trend (unitize)")
plt.show()
corr = trend.corr()
sns.heatmap(corr, cmap="YlGnBu")
plt.title("Correlation Heat Map")
plt.show()

# 3. Integration Order Test
def Integration(X):
    count = 0
    while count <= 3:
        adf = adfuller(X)
        if adf[0] < adf[4]["5%"]:  # stationary
            return count
        count += 1
        X = np.diff(X)  # difference
    return count
Int_Order = {}
for i in trend.columns:
    Int_Order[i] = Integration(trend[i].values)  # all series meet 1-order Integration assumption
print(Int_Order)

# 4. EG Cointegration Test
def Half_Life(X):
    reg = sm.OLS(X[1:]-X[:-1], sm.add_constant(X[:-1]))
    res = reg.fit()
    half_life = -np.log(2)/res.params[1]
    return half_life

def Cointegration(Y, X, title):
    A = np.linalg.inv((X.T).dot(X)).dot(X.T).dot(Y)
    E = Y-X.dot(A)
    half_life = Half_Life(E)
    adf = adfuller(E)
    if adf[0] < adf[4]["5%"]:
        plt.figure(figsize=(12, 4))
        plt.plot(E)
        plt.title("{} | half-life: {} | adf: {} | 95%: {}".format(
            title, round(half_life), round(adf[0], 4), round(adf[4]["5%"], 4)))
        plt.show()
    return A, half_life, adf

# 5. Box-Tiao Canonical Decomposition
def Box_Tiao(X):
    X = X-X.mean(axis=0)  # demean to meet the assumption
    Y, X_lag = X[1:, :], X[:-1, :]  # OLS: X[t] ~ X[t-1] without constant item
    # Y = AX + e, A = [X^T * X]^-1 * X^T * Y
    A = np.linalg.inv((X_lag.T).dot(X_lag)).dot(X_lag.T).dot(Y)
    Y_hat = X.dot(A)  # X[t] Prediction: Y_hat = AX
    Cov = (X.T).dot(X)  # 1/(len(X)-1) would be offset in the following calculation
    eig_l, eig_v = np.linalg.eigh(np.linalg.inv(Cov))  # Covariance Matrix is real symmetric (positive semi-definite)
    Q = eig_v.dot(np.diag(np.sqrt(eig_l))).dot(eig_v.T)  # Q = Cov^(-1/2) = V*sqrt(L)*V^T (V*L*V^T = Cov^(-1))
    P = Q.dot((Y_hat.T).dot(Y_hat)).dot(Q)  # Predictability Matrix P = Q * ([XA]^T*[XA]) * Q
    eig_l, eig_v = np.linalg.eig(P)
    rank = np.argsort(eig_l)  # get the minimum eigenvalue
    eig_l, eig_v = eig_l[rank], eig_v[:, rank]
    return Q.dot(eig_v[:, 0])

def BT_weight(X, category):  # most mean-reverting portfolio
    index = list(X.columns).index(category)
    W = Box_Tiao(X.values)
    W /= W[index]
    return W

def stationary(X, title):  # half-life and stationary test
    half_life = Half_Life(X)
    adf = adfuller(X)
    if half_life <= 21 and adf[0] < adf[4]["5%"]:
        plt.figure(figsize=(12, 4))
        plt.plot(X)
        plt.title("{} | half-life: {} | adf: {} | 95%: {}".format(
            title, round(half_life), round(adf[0], 4), round(adf[4]["5%"], 4)))
        plt.show()
    return half_life, adf

# 6. Brute Force Search
X = pd.concat([future_dir[i][(start_date<=future_dir[i].index)&(future_dir[i].index<=insample)]
               [["adj_close"]].rename(columns={"adj_close": i}) for i in future_dir.keys()], axis=1)
"""
all = steel+coal
n = len(all)
cointegration_dir = {}
for i in range(n-1):  # cointegration search
    temp = [all[i]]
    for j in range(i+1, n):
        temp.append(all[j])
        name = "+".join(temp)
        A_temp, hf_temp, adf_temp = Cointegration(X[[temp[0]]].values, X[[temp[1]]].values, name)
        print("{} | half-life: {} | adf: {} | 95%: {}".format(name, round(hf_temp), round(adf_temp[0], 4), round(adf_temp[4]["5%"], 4)))
        if adf_temp[0] < adf_temp[4]["5%"]:  # stationary with 95% confidence level
            cointegration_dir[name] = (A_temp, hf_temp, adf_temp)
        temp.pop()
stationary_dir = {}
for i in range(n-2):  # box-tiao search
    temp = [all[i]]
    for j in range(i+1, n-1):
        temp.append(all[j])
        for k in range(j+1, n):
            temp.append(all[k])
            X_temp, index = X[temp], temp[0]
            W_temp = BT_weight(X_temp, index)
            name = "+".join(temp)
            hf_temp, adf_temp = stationary(X_temp.values.dot(W_temp), name)
            if hf_temp <= 21 and adf_temp[0] < adf_temp[4]["5%"]:  # stationary with 95% confidence level
                stationary_dir[name] = (hf_temp, adf_temp)
            temp.pop()
        temp.pop()
"""

# 7. Quarterly Rolling Mean Reverting
def rolling_MR(pdf, category, window=63):
    columns = list(pdf.columns)
    n = len(pdf)
    index = [pdf.index[i] for i in range(0, n, window)]
    rdf = pd.DataFrame({"CLOCK": index, "Window": index})
    pdf = pd.merge(pdf, rdf, how="left", on="CLOCK").fillna(method="ffill").set_index("CLOCK")
    wdf = pdf.groupby("Window").apply(lambda x: BT_weight(x, category)).rename("Weight").reset_index()
    wdf["Weight"] = wdf["Weight"].shift(1)
    pdf = pd.merge(pdf.reset_index(), wdf, how="left", on="Window").dropna().set_index("CLOCK")
    pdf["MR"] = np.concatenate(pdf.groupby("Window").apply(lambda x: x[columns].values.dot(x["Weight"].iloc[0])).values)
    return pdf

pair = ["rb", "i", "SM"]
pdf = X[pair].copy()
W_1 = BT_weight(pdf, pair[0])
pdf["MR"] = pdf[pair].values.dot(W_1)
hf_1, adf_1 = stationary(pdf["MR"].values, "Steel")

# 8. Boundary
def sigma_test(X, times, figure=False):
    mean, std = X.mean(), X.std()
    up, down = mean+times*std, mean-times*std
    n = len(X)
    theo = norm.cdf(up, mean, std)-norm.cdf(down, mean, std)
    real = sum(np.where((down <= X) & (X <= up), 1, 0))/n
    if figure:
        plt.figure(figsize=(12, 4))
        plt.plot(X)
        plt.plot([up]*n, color="green")
        plt.plot([down]*n, color="red")
        plt.title("sigma: %s | theory: %s | real: %s" % (str(times), str(round(theo, 4)), str(round(real, 4))))
        plt.show()
    return (theo, real)
"""
sigma_dir = {}
for i in np.linspace(0.25, 3, 12):  # boundary search
    sigma_dir[i] = sigma_test(pdf["MR"].values, i, True)
"""
sigma_1 = 0.75

# 9. Bollinger Band
mean, std = pdf["MR"].mean(), pdf["MR"].std()
pdf["mean"], pdf["up"], pdf["down"] = mean, mean+sigma_1*std, mean-sigma_1*std
pdf["BBMean"] = pdf["MR"].rolling(round(hf_1)).mean()
pdf["BBstd"] = sigma_1*pdf["MR"].rolling(round(hf_1)).std()
pdf["BBUp"] = pdf["BBMean"]+pdf["BBstd"]
pdf["BBDown"] = pdf["BBMean"]-pdf["BBstd"]
pdf.drop("BBstd", axis=1, inplace=True)

# 10. visualization
trend[["rb", "i", "SM"]].plot(figsize=(12, 4), title="rb+i+SM Trend (unitize)")
plt.show()  # trend
pdf[["MR"]].rename(columns={"MR": "Spread"}).plot(figsize=(12, 4), title="Mean-Reverting Series Signal")
plt.show()  # spread
pdf[["MR", "mean", "up", "down"]].rename(columns={"MR": "Spread"}).plot(figsize=(12, 4), title="Mean Reverting Band (0.75*sigma)")
plt.show()  # MR band
pdf[pdf.columns[3:]].rename(columns={"MR": "Spread"}).plot(figsize=(12, 4), title="Bollinger Band (Window = 20, 0.75*sigma)")
plt.show()  # BB band

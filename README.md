# Pair_Trading_with_Box_Tiao_Decomposition
Apply Box&amp;Tiao to generate stationary price spread series in steel industry commodity futures market for pair trading

### Abstract
In 1977, [Box and Tiao](https://pages.stern.nyu.edu/~dbackus/BCZ/HS/BoxTiao_canonical_Bio_77.pdf) provided a method of Canonical Decomposition, which can be used in assessing the predictability of Multidimensional Time Series. With Box-Tiao decomposition, we can get a vector of weights allows the linear combination of the input time series to have the worst forecasting capability. In this case, the output combination is close to a white noise series where we can apply pair-trading strategy due to its mean-reverting property.  
  
In this project, we are going to study the cointegration phenomena among 6 steel and coal assets in Chinese commodity futures market. Box-Tiao decomposition would be used to generate the stationary price spread series among those cointegrated assets for further pair-trading strategy developing.

### 1. Box & Tiao Canonical Decomposition
In the paper of Box and Tiao, the portfolio $\Pi_t$ is assumed to be satisfied with an VAR(1) model: $\Pi_t=\Pi_{t-1}A+Z$, where $\Pi_{t-1}A$ is an one-step forward prediction for $\Pi_t$ at time $t-1$. So, we have their volatility had the following relationship:
$$Var(\Pi_t)=\sigma_t^2\quad|\quad Var(\Pi_{t-1}A)=\sigma_{t-1}^2\quad|\quad Var(Z_t)=\Sigma$$
$$\sigma_t^2=\sigma_{t-1}^2+\Sigma$$
$$1=\frac{\sigma_{t-1}^2}{\sigma_{t}^2}+\frac{\Sigma}{\sigma_{t}^2}=v+\frac{\Sigma}{\sigma_{t}^2}$$
$v=\frac{\sigma_{t-1}^2}{\sigma_{t}^2}$ is used to describe the predictability of the Var(1) model. So, while minimizing $v$, the portfolio $\Pi_t$ would be close to a white noise series, which is the stationary price spread we want.  
  
In this project, we have the price of commodity futures as $S_t$, the weight of asset $x$, and the linear combination with the worst forecasting capability as $\Pi_t$ with the minimum $v=\frac{\sigma_{t-1}^2}{\sigma_{t}^2}$. So, we have the following formula:
$$\Pi_t=S_tx$$
$$S_tx=S_{t-1}Ax+Z_tx$$
$$v=\frac{x^TA^T\Gamma Ax}{x^T\Gamma x}$$
$$\Gamma=\frac{1}{m}S_t^TS_t\quad(S_t=Demean(S_t))$$
The process of minimizing $v$ is equal to have the solution for eigenvalue $\lambda$ satisfied with the following equation:
$$det(\lambda\Gamma-A^T\Gamma A)=0$$
So, we have $x=\Gamma^{-\frac{1}{2}}z$, where $z$ is the eigenvector with the minimum eigenvalue of the following matrix:
$$\Gamma^{-\frac{1}{2}}A^T\Gamma A\Gamma^{-\frac{1}{2}}$$
Since $A$ is the slope parameter of the Linear Regression for $S_t$ to $S_{t-1}$ and $\Gamma$ is the covariance matric of $S_t$, we have:
$$\Gamma^{-\frac{1}{2}}A^T\Gamma A\Gamma^{-\frac{1}{2}}$$
$$=(S_t^TS_t)^{-\frac{1}{2}}A^T(S_{t-1}^TS_{t-1})A(S_t^TS_t)^{-\frac{1}{2}}$$
$$=(S_t^TS_t)^{-\frac{1}{2}}(S_{t-1}A)^T(S_{t-1}A)(S_t^TS_t)^{-\frac{1}{2}}$$
$$=(S_t^TS_t)^{-\frac{1}{2}}(\hat{S_{t}^T}\hat{S_{t}})(S_t^TS_t)^{-\frac{1}{2}}$$

### 2. Pick up Trading Pairs
Box-Tiao decomposition helps us generate the stationary price spread series for a given set of commodity futures, so the question remains is to identify a set of commodity futures possibly have cointegration phenomena among them. It is obvious that those commodity categories who are in the same supply and demand chain would probably have a close trend, so we pick up 6 categories from the steel and coal industries: rebar(rb), iron ore(i), hot rolled coil(hc), manganese silicon(SM), coking coal(jm), coke(j).  
  
After applying Box-Tiao decomposition on every 3 pairs out of these 6 categories ($C_6^3=20$ pairs in total), we filter those pairs didn't pass the ADF stationary test or have a half-life longer than 21 trading days. Finally, we have the following 5 pairs suitable for pair trading:

No. | Code | Half-Life
--- | --- | ---
1 | rb+i+SM | 20
2 | rb+j+jm | 19
3 | i+SM+jm | 17
4 | i+j+jm | 20
5 | hc+j+jm | 21

For the first pair, all these 3 categories are from steel industry, so we pick up this pair for the further pair trading strategy developing.

![Trend](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/trend.png)

After applying Box-Tiao decomposition on the first pair, we have the weight vector for these 3 categories as follow:

Code | Weight | Contract Multiplier | Volume
--- | --- | --- | ---
rb | 1 | 10 | 100
i | -0.75038229 | 100 | 8
SM | -0.12836106 | 5 | 26

![Price Spred](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/spread.png)

### 3. Mean-Reverting Breakthrough Signal
After we generated the stationary price spread series, with its mean-reverting property, we can open a position when it is moving away from the mean value and cover the position at its returning. A simple method to catch these arbitrage chances is to build up a channel which is $n\sigma$ away from the mean value $\mu\pm n\times\sigma$, and then trade every time when the series breakthroughs the channel.  
For a white Gaussian noise, theoretically, the frequency of series moving within the channel should be equal to the following possibility:
$$\frac{\sum_i{I_i(\mu-n\sigma\leq P_t\leq \mu+n\sigma)}}{T}=\phi(\mu+n\sigma)-\phi(\mu-n\sigma)$$
We hope to have around half of the trading days in-sample within the channel, so we set $n=0.75$.

n Times | In-Sample Trading Frequency | Theoretical Frequency
--- | --- | ---
0.75 | 0.5467 | 0.561

However, with this simple method, we can only make money when the series passes the channel, whose final profit is close to $\frac{N_{pass}}{2}\times 0.75\sigma$. By introducing the Bollinger Band Breakthrough signal, it is possible to open a position earlier than the passing time, which would bring us more profit. For example, when the series is far above the upper band but it sends out a signal of breaking down through the lower Bollinger band as a sign that the series is in its process of reverting, opening a short position earlier can earn more profit. We use the half-life 20 and $0.75\sigma$ to build the Bollinger Band.

![mean±sigma](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/sigma.png)

### 4. Back-Test
item | details
--- | ---
Futures Category | rb, i, SM
Contract Type | continuous contract
Trading Frequency | daily
Trade Executing Time | next day
Price for Signal Construction | back-adjusted closing price
Trading Rules | When the series is above the upper band and a signal of down breaking through the lower Bollinger band or upper band, sell 100 contracts of rb, buy 8 contracts of i and 26 contracts of SM. When the series is under the lower band and a signal of up breaking through the upper Bollinger band or lower band, buy 100 contracts of rb, sell 8 contracts of i and 26 contracts of SM. When the series touches the mean value, cover all the positions.
Executing Price Simulation | average of open price and close price next day
Executing Cost | 0.03%/RMB for rb and i; 3.00RMB/contract for SM
Price for Profit Calculation | average of open price and close price

![signal](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/signal.png)

Back-Test | in-sample
--- | ---
Period | 03/19/2017 - 03/19/2021
Capital | 1000000.00RMB
Trading Volume | rb: 100, i: 8, SM: 26
Trading Fee | rb: 0.03%/RMB, i: 0.03%/RMB, SM: 3.00RM/contract

Statistics | Value
--- | ---
Annual Return | 7.5612%
Max Drawdown | 66616.00RMB
Sharpe Ratio | 1.8118
Calmar Ratio | 1.1350\*10^-6
Win Rate | 84.6154%
Profit-Loss Ratio | 2.2122
Average Position Holding Period | 59.3077 days

![in-sample P&L](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/in.png)

Back-Test | out-of-sample
--- | ---
Period | 03/19/2021 - 03/18/2022
Capital | 1000000.00RMB
Trading Volume | rb: 100, i: 8, SM: 26
Trading Fee | rb: 0.03%/RMB, i: 0.03%/RMB, SM: 3.00RM/contract

Statistics | Value
--- | ---
Annual Return | 1.3788%
Max Drawdown | 127679.00RMB
Sharpe Ratio | 0.1643
Calmar Ratio | 1.0799\*10^-7
Win Rate | 50.00%
Profit-Loss Ratio | 1.1247
Average Position Holding Period | 66.25 days

![out-of-sample P&L](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/out.png)

![Parameter Sensitive](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/parameter.png)

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
![Price Spred](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/spread.png)
![mean±sigma](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/sigma.png)
![signal](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/signal.png)
![in-sample P&L](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/in.png)
![Parameter Sensitive](https://github.com/yuba316/Pair_Trading_with_Box_Tiao_Decomposition/blob/main/figure/parameter.png)

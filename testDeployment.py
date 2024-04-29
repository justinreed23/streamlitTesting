import streamlit as st
import numpy as np
import pandas as pd
import datetime
import math
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(
    "Older, Smarter, Richer",
    "📈",
    initial_sidebar_state="expanded",
    layout="wide",
    menu_items={
        "Report a Bug" : 'https://github.com/justinreed23/Older-Smarter-Richer/issues',
        "About" : 'https://github.com/justinreed23/Older-Smarter-Richer/blob/main/README.md',
        "Get Help" : 'https://media.tenor.com/mZZoOtDcouoAAAAM/stop-it-get-some-help.gif'
    }
)


"""
# CAPM Portfolio Optimization with Risk Aversion Adjustment: Find Your Optimal Investment Portfolio for Retirement by filling Out Our Survey!
## Project Purpose:
In the modern investing landscape, the traditional approach of using a 60:40 stock-bond approach is prevalent. This strategy involves allocating 60% to stocks and 40% bonds at the beggining of one's life, then typically flips those weights after retirement. This aims to provide a simplified balance between growth potential from stocks and stability from bonds. Our goal was to come up with a more advanced model, which creates a survey for one to clarify their investing and retirement goals to find their optimal investing strategy without having to use unrefined methods or taking the time and effort to work with a professional advisor.  
We hypothesise that different income levels and risk profiles favor different strategies. We use an equation to determine the optimal portfolio selection after the subject has outlined his/her self-described parameters. In addition to finding the optimal investment portfolio, we will also display the cumulative returns over time that one may recieve using our optimized model. The data that we use to optimize a portfolio comes from 10 different ETFs we extracted from Yahoo Finance. We downloaded monthly returns for as long as they date back, then merge them by data into one wide dataset. Lastly, we randomly pulled rows to create a new 600 row dataframe (12 rows x 50 years) and converr that back to a tall dataframe.
This is the equation we use:
"""

st.latex(r'''
         U(C,B) = \displaystyle\sum_{t=\Delta}^{T_{max}} \frac{(C_{t}/\sqrt{H_{t}})^{1-\gamma}}{1-\gamma} + \theta{\frac{(B+k)^{1-\gamma}}{1-\gamma}}
         ''')


"""
1. We will be using the utility equation from [Anarkulova, Cederburg, O'Doherty](Related_reading/Beyond_Status_Quo.pdf) (2023) to determine optimal portfolio selection
2. Variable Definitions
   1. $C$ is defined as consumption in dollars during retirement
   2. $H$ is number of people in household during retirement
   3. $t$ is time since started saving (in months)
   4. $\gamma$ is risk aversion
      1. The medium value is $3.84$
      2. We will adjust this based on respondents self-described risk aversion
   5. $θ$ is inheritance utility intensity
      1. The medium value is $2360 multiplied by 12^{\gamma}$ to adjust for monthly returns
      2. We will adjust this based on respondents self-described inheritance goals
   6. $B$ is inheritance amount
   7. $k$ is the extent to which inheritance is viewed as a luxury good
      1. Normal is $490,000
   8. $\Delta$ is the time between retirement age and savings age in months
   9.  $T^{max}$ is date of death.
## Inspiration: 
Our work was inspired by "Beyond the Status Quo: A Critical Assessment of Lifecycle Investment Advice." In this paper, the authors discuss the limitations of the traditional 60:40 stock-bond approach and propose a new model that takes into account the individual's risk aversion and inheritance goals. However their study focuses on the average investor using a simulation of many possible American lifestyles. We wanted to take this a step further and create a model that is personalized to the individual investor.
## Caveats:
Our models for the ETFs are not particularly robust and can use better refinement for accurate, large scale modeling. We are essentially saying past predictions will provide accurate predictions for future results. Our data consists of monthly returns from these ETFs, which also do not date back past around 40 years. Our model does not account for irregularities in the economic landscape.
## About Us:
### Reghan Hesser
title: "Reghan Hesser" 
logo: "/images/headshot.jpg"
- Major: Finance 
- Year of Graduation: 2024
- Interests: Cooking, Skiing, Dancing 
### Justin Reed
- Major:
- Year of Graduation: 2024
- Interests: 
### Maria Maragkelli
- Major:
- Year of Graduation: 2024
- Interests: 

"""


#############################################
# start: sidebar
#############################################

with st.sidebar:

    '''
    ## Financial Assessment
    
    ### Please answer the following questions about your financial situation
    '''
    
    submitted_income = st.number_input("What is your annual income?(Max $10mil)", min_value=0,max_value=10000000, value=65000)
    income_growth = st.slider("What is your expected annual income growth rate in percentage?", min_value=1.0, max_value=10.0, value=3.0, step=0.1) / 100
    start_savings = st.number_input("At what age did you start saving?", min_value=18, max_value=50)
    retirement_start = st.number_input("At what age will you retire?", min_value=50, max_value=80)
    death_year = st.number_input("At what age do you expect you will pass away?", min_value=retirement_start, max_value=100)
    household_size = st.number_input("Number of people in household at time of retirement?", min_value=1, value=10)
    
    save_rate = st.slider("What percent of your income do you expect to save annually?", min_value=5.0, max_value=40.0, value=10.0, step=0.1) / 100
    consumption_rate= st.slider("What percent of your income do you plan to spend annually in retirement? General investment advice is 4%", min_value=1.0, max_value=20.0, value=4.0, step=0.1) / 100
    risk_aversion_options = ["Low", "Medium", "High"]
    selected_risk_aversion = st.selectbox("Select your risk aversion level:", risk_aversion_options)

# Assigning values based on user selection
    if selected_risk_aversion == "Low":
        risk_aversion = 3.74
    elif selected_risk_aversion == "Medium":
        risk_aversion = 3.84
    else:
        risk_aversion = 3.94 

    inher_util_options = ["None", "Low", "Medium", "High"]
    selected_inher_util = st.selectbox("Select your inheritance utility level:", inher_util_options)

# Assigning values based on user selection
    if selected_inher_util == "None":
        inher_util = 0
    elif selected_inher_util == "Low":
        inher_util = 0
    elif selected_risk_aversion == "Medium":
        inher_util = 2360
    else:
        inher_util = 2460


#############################################
# create returns df, normally this is an import
#############################################

monthly_income = submitted_income/12
monthly_growth = 1+ (income_growth/12)
month_start_savings = start_savings*12
month_retirement_start = retirement_start*12
death_month = death_year*12
# maybe I should let them option this
inflation = 0.02
inflation_rate = inflation/12
inher_luxury = 490000




rng = np.random.default_rng(123)

start_year = 1950
end_year = 2050
portfolios = ["First", "Second", "Third", "Fourth", "Fifth"]
portfolios_list = []
dates_list = []


for portfolio in portfolios:
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            date = datetime.date(year, month, 1)
            dates_list.append(date)
            portfolios_list.append(portfolio)

random_returns = rng.uniform(low=0, high=(0.10 / 12), size=len(dates_list))


returns = pd.DataFrame(
    {"Portfolio": portfolios_list, "date": dates_list, "ret": random_returns}
)


returns['income'] = 0.0


total_monthly_incomes = []

for t in returns.index[month_start_savings:month_retirement_start]:
    current_month = t-month_start_savings
    income_for_month = monthly_income*(monthly_growth**current_month)
    total_monthly_incomes.append(income_for_month)
    


# Apply mapping to DataFrame's index to create a month column that resets for each portfolio
returns['month'] = returns.groupby('Portfolio').cumcount()

# Map the total_monthly_incomes to each row based on the month
income_series = pd.Series(total_monthly_incomes, index=range(month_start_savings, month_retirement_start))
returns['income'] = returns['month'].map(income_series)
# set all nan values in income to 0.0
returns['income'] = returns['income'].fillna(0.0)


def utility_consumption(consumption, household_size, risk_aversion):
    factor_risk = 1 - risk_aversion
    consumption_util = (consumption / math.sqrt(household_size)) ** factor_risk
    adj_consumption_util = consumption_util / factor_risk
    return adj_consumption_util


def utility_inheritance(inher_util, inheritance_amount, inher_luxury, risk_aversion):
    adj_inher_util = inher_util*(12**risk_aversion)
    factor_risk = 1-risk_aversion
    equation = (((inheritance_amount/inher_luxury)**factor_risk) / factor_risk) * adj_inher_util
    return equation


returns['savings'] = 0.0
returns['utility'] = 0.0

final_utility = {}
consumption_dict = {}

for portfolio in returns['Portfolio'].unique():
    # Filter the DataFrame by portfolio
    portfolio_data = returns[returns['Portfolio'] == portfolio]
    
    # Initialize previous savings
    previous_savings = 0.0
    initial_consumption = 0.0
    current_consumption = 0.0
    current_utility = 0.0
    
    
    # Iterate through each row in the portfolio data
    for index, row in portfolio_data.iterrows():
        if row['month'] == month_retirement_start:
            initial_consumption = (previous_savings * consumption_rate)/12
            current_savings = (previous_savings - initial_consumption) * (1 + row['ret'])
            current_utility = utility_consumption(initial_consumption, household_size, risk_aversion)
            returns.at[index, 'savings'] = current_savings
            returns.at[index, 'utility'] = current_utility
            consumption_dict[portfolio] = initial_consumption
        if row['income'] == 0.0 and row['month'] > month_retirement_start and row['month'] < death_month:
            current_consumption = initial_consumption * ((1+inflation_rate)**(row['month']-month_retirement_start))
            if previous_savings <= current_consumption:
                current_consumption = previous_savings
                current_utility = -10000000000000.0
                current_savings = (previous_savings - current_consumption) * (1 + row['ret'])
                returns.at[index, 'utility'] = current_utility
                returns.at[index, 'savings'] = current_savings
            else:
                current_savings = (previous_savings - current_consumption) * (1 + row['ret'])
                current_utility = utility_consumption(current_consumption, household_size, risk_aversion)
                returns.at[index, 'utility'] = current_utility + returns.at[index-1, 'utility']
                returns.at[index, 'savings'] = current_savings
        elif row['month'] == death_month:
            returns.at[index, 'savings'] = previous_savings
            current_consumption = initial_consumption * ((1+inflation_rate)**(row['month']-month_retirement_start))
            current_utility = utility_consumption(current_consumption, household_size, risk_aversion) + utility_inheritance(inher_util, returns.at[index, 'savings'], inher_luxury, risk_aversion)
            returns.at[index, 'utility'] = current_utility + returns.at[index-1, 'utility']
            final_utility[portfolio] = returns.at[index, 'utility']
        elif row['month'] > death_month:
            returns.at[index, 'savings'] = previous_savings
        else:
            current_savings = save_rate * row['income'] + previous_savings * (1 + row['ret'])
            returns.at[index, 'savings'] = current_savings
        # Update previous savings
        previous_savings = current_savings


max_key = max(final_utility, key=final_utility.get)


#############################################
# start: plot
#############################################



returns = returns[(returns['month'] >= month_start_savings) & (returns['month'] <= death_month)]

fig = px.line(returns, x="date", y="savings", color="Portfolio", title="Savings Over Time", width=1000, height=600)

st.plotly_chart(fig, use_container_width=True)


fig2 = go.Figure()

for portfolio_name, portfolio_frame in returns.groupby("Portfolio"):
    if portfolio_name == max_key:
        fig2.add_trace(go.Scatter(x=portfolio_frame["month"], y=portfolio_frame["savings"], line_shape='spline', name=portfolio_name, line=dict(color='red'), hovertemplate="Month: %{x}<br>Savings: $%{y}"))
        fig2.add_annotation(
            x=portfolio_frame["month"].iloc[-1],
            y=portfolio_frame["savings"].iloc[-1],
            text=f"{portfolio_name} is the optimal portfolio<br>"
             f"Savings at Retirement Start: ${returns.loc[returns['month'] == month_retirement_start, 'savings'].iloc[0]:,.2f}<br>"
             f"Savings at Retirement End (Inheritance): ${portfolio_frame['savings'].iloc[-1]:,.2f}<br>"
             f"Initial Monthly Consumption: ${initial_consumption:,.2f}",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-60
        )
    else:
        fig2.add_trace(go.Scatter(x=portfolio_frame["month"], y=portfolio_frame["savings"], line_shape='spline', name=portfolio_name, line=dict(color='rgba(128, 128, 128, 0.5)'), hovertemplate="Month: %{x}<br>Savings: $%{y}"))

fig2.update_layout(
    xaxis_title="Month",
    yaxis_title="Savings",
    width=1000,
    height=600,
    template="plotly_white"
)
fig2.update_layout(
    title={
        'text': "Retirement Portfolios over time",
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    }
)

st.plotly_chart(fig2, use_container_width=True, theme="streamlit")

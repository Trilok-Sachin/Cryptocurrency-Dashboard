# import dash
import streamlit as st
import plotly.graph_objs as go
import plotly.subplots as sp
import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
# import ast


# Initialize the CCXT exchange object (use your desired exchange)
exchange = ccxt.binance()
cg = CoinGeckoAPI()


#Extract Data 
def extract_data(TIMEFRAME, START_DATE, SYMBOL, SMA1, SMA2):


    crypto_df = pd.DataFrame()

    # Fetch historical OHLCV data in chunks and append to crypto_df
    # Calculate the number of milliseconds in the timeframe
    if TIMEFRAME == '4h':
        timeframe_ms = 4 * 60 * 60 * 1000
    elif TIMEFRAME == '12h':
        timeframe_ms = 12 * 60 * 60 * 1000
    elif TIMEFRAME == '1d':
        timeframe_ms = 24 * 60 * 60 * 1000
    elif TIMEFRAME == '3d':
        timeframe_ms = 3 * 24 * 60 * 60 * 1000
    elif TIMEFRAME == '1w':
        timeframe_ms = 7 * 24 * 60 * 60 * 1000
    elif TIMEFRAME == '1M':
        timeframe_ms = 30 * 24 * 60 * 60 * 1000

    # Initialize an empty DataFrame to store the combined data
    crypto_df = pd.DataFrame()

    start_date = START_DATE
    # Fetch historical OHLCV data in chunks and append to crypto_df
    while True:
        # Fetch historical OHLCV data with a limit based on the timeframe
        ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, since=int(pd.Timestamp(start_date).timestamp() * 1000), limit=1000)

        # Convert OHLCV data to a DataFrame
        chunk_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Convert timestamps to datetime format
        chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'], unit='ms')

        # Append the chunk to crypto_df
        crypto_df = pd.concat([crypto_df, chunk_df], ignore_index=True)

        # Update the start_date for the next chunk
        start_date = crypto_df['timestamp'].iloc[-1] + pd.DateOffset(milliseconds=timeframe_ms)

        # If the data returned is less than the limit, it means we've fetched all available data
        if len(ohlcv) < 1000:
            break


    # Convert timestamps to datetime format
    crypto_df['timestamp'] = pd.to_datetime(crypto_df['timestamp'], unit='ms')


    # Calculate Simple Moving Averages (SMA)
    # Customize the window for the second SMA
    crypto_df['sma1'] = crypto_df['close'].rolling(window=SMA1).mean()
    crypto_df['sma2'] = crypto_df['close'].rolling(window=SMA2).mean()

    return crypto_df

    
def return_buy_and_sell_signals(crypto_df):

    
    # Initialize the 'Buy and Hold' and 'Sell and Observe' columns
    crypto_df['Buy Flag'] = 0

    # Flag the points where SMA1 crosses above SMA2 as 'Buy and Hold' (1)
    crypto_df.loc[crypto_df['sma1'] > crypto_df['sma2'], 'Buy Flag'] = 1

    crypto_df.sort_values('timestamp', inplace=True)

    crypto_df['Buy Flag Lagged'] = crypto_df['Buy Flag'].shift(1)

    buy_signals = crypto_df[(crypto_df['Buy Flag']==1)&(crypto_df['Buy Flag Lagged']==0)]
    sell_signals = crypto_df[(crypto_df['Buy Flag']==0)&(crypto_df['Buy Flag Lagged']==1)]

    return buy_signals, sell_signals


def plot_price_chart(crypto_df, SYMBOL, TIMEFRAME, SMA1, SMA2):


    
    #Extracting Buy and sell signals based on moving averages
    buy_signals_df, sell_signals_df = return_buy_and_sell_signals(crypto_df)

    # Create a subplot grid
    fig = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])

    # Add the candlestick chart to the upper subplot with name 'Price'
    candlestick = go.Candlestick(x=crypto_df['timestamp'],
                                open=crypto_df['open'],
                                high=crypto_df['high'],
                                low=crypto_df['low'],
                                close=crypto_df['close'],
                                name='Price')
    fig.append_trace(candlestick, row=1, col=1)

    # Add SMAs to the candlestick chart with custom line colors
    sma1_trace = go.Scatter(x=crypto_df['timestamp'], y=crypto_df['sma1'], mode='lines', name=f'SMA-{SMA1}', line=dict(color='yellow'))
    sma2_trace = go.Scatter(x=crypto_df['timestamp'], y=crypto_df['sma2'], mode='lines', name=f'SMA-{SMA2}', line=dict(color='pink'))
    fig.add_trace(sma1_trace, row=1, col=1)
    fig.add_trace(sma2_trace, row=1, col=1)

    # Define the buy and sell signals as datetime values
    buy_signals = buy_signals_df['timestamp']
    sell_signals = sell_signals_df['timestamp']

    # Create vertical lines at buy and sell signals
    for buy_signal in buy_signals:
        fig.add_shape(go.layout.Shape(
            type="line",
            x0=buy_signal,
            x1=buy_signal,
            y0=crypto_df['low'].min(),
            y1=crypto_df['high'].max(),
            line=dict(color="green", dash="dot")
        ))

    for sell_signal in sell_signals:
        fig.add_shape(go.layout.Shape(
            type="line",
            x0=sell_signal,
            x1=sell_signal,
            y0=crypto_df['low'].min(),
            y1=crypto_df['high'].max(),
            line=dict(color="red", dash="dot")
        ))


    # Set the layout for the cryptocurrency chart
    fig.update_layout(title=f'{SYMBOL} Candlestick Chart ({TIMEFRAME})',
                    xaxis_rangeslider_visible=True)

    # Create a volume chart as a subplot in the lower subplot with name 'Volume'
    volume = go.Bar(x=crypto_df['timestamp'], y=crypto_df['volume'], marker_color='blue', name='Volume')
    fig.append_trace(volume, row=2, col=1)

    # Update the subplot height
    fig.update_layout(yaxis2=dict(domain=[0.1, 0.3]))

    # Add legends
    fig.update_layout(legend=dict(orientation="h", x=0, y=1.05),
                      width=900, height=600)

    # Display the chart
    # fig.show()

    return buy_signals_df, sell_signals_df, fig


def return_agg_profit_pct(buy_signals_df, sell_signals_df):

    buy_signals_df_req = buy_signals_df[['timestamp', 'close']].copy()
    buy_signals_df_req['Action'] = 'BUY'
    sell_signals_df_req = sell_signals_df[['timestamp', 'close']].copy()
    sell_signals_df_req['Action'] = 'SELL'

    signal_df = pd.concat([buy_signals_df_req, sell_signals_df_req]).sort_values('timestamp')

    signal_df['Sell Date'] = signal_df['timestamp'].shift(-1)
    signal_df['Sell Price'] = signal_df['close'].shift(-1)


    signal_df_req = signal_df[signal_df['Action']=='BUY']
    signal_df_req.rename(columns={'close':'Buy Price'}, inplace=True)


    signal_df_req['Profit'] = signal_df_req['Sell Price'] - signal_df_req['Buy Price']
    signal_df_req['Profit_pct'] = (signal_df_req['Sell Price'] - signal_df_req['Buy Price'])/signal_df_req['Buy Price']

    print(f"Overall Profit Percentage:{signal_df_req['Profit_pct'].sum()*100:.2f}%")

    overall_profit_pct = signal_df_req['Profit_pct'].sum()*100

    return signal_df_req, overall_profit_pct

def return_trending_coin_info():

    trending_coin_data = pd.DataFrame()
    for coin_data in cg.get_search_trending()['coins']:

        melted_trending_coin_df = pd.DataFrame(coin_data['item']).reset_index()
        melted_trending_coin_df['price_change_pct_btc_24h'] = melted_trending_coin_df[melted_trending_coin_df['index']=='price_change_percentage_24h']['data'].values[0]['btc']
        melted_trending_coin_df['price_change_pct_usd_24h'] = melted_trending_coin_df[melted_trending_coin_df['index']=='price_change_percentage_24h']['data'].values[0]['usd']

        melted_trending_coin_df = melted_trending_coin_df[~(melted_trending_coin_df['index'].isin(['sparkline', 'price_change_percentage_24h']))]

        trending_coin_info = melted_trending_coin_df.pivot_table(index=['id', 'symbol', 
                                                                        'market_cap_rank', 'score', 
                                                                        'price_change_pct_btc_24h', 'price_change_pct_usd_24h'], columns='index', values='data', aggfunc='first').reset_index()
        trending_coin_info['score'] = trending_coin_info['score'] + 1

        # trending_coin_data = trending_coin_data.append(trending_coin_info)
        trending_coin_data = pd.concat([trending_coin_data, trending_coin_info], ignore_index=True)

    trending_coin_data.sort_values('score', inplace=True, ascending=True)
    # trending_coin_data['content'] = trending_coin_data['content'].astype(str)
    # top_coin_symbol = trending_coin_data['symbol'].iloc[0]
    # top_coin_name = trending_coin_data['id'].iloc[0]
    
    # top_coin_description_str = trending_coin_data['content'].iloc[0]

    # print(trending_coin_data)
    # if top_coin_description_str is not None:
    #     top_coin_description = ast.literal_eval(trending_coin_data['content'].iloc[0])['description']
    # else:
    #     top_coin_description = None
    # print(top_coin_name, top_coin_description)

    trending_coin_data.drop('content', axis=1, inplace=True)

    return trending_coin_data
    
    

# Streamlit UI
def main():


    market_data = pd.DataFrame(cg.get_coins_markets(vs_currency='usd'))[['symbol', 'name', 'current_price', 
                                                                         'market_cap', 'market_cap_rank',
                                                                         'fully_diluted_valuation', 
                                                                         'total_volume', 'high_24h', 'low_24h',
                                                                         'price_change_24h', 'price_change_percentage_24h',
                                                                         'market_cap_change_24h', 'market_cap_change_percentage_24h',
                                                                         'circulating_supply', 'total_supply', 'ath', 'ath_change_percentage',
                                                                         'ath_date', 'atl', 'atl_change_percentage', 'atl_date']].copy()

    st.title('Crypto Price Analysis Dashboard')
    
    st.sidebar.title('Parameters')

    # Add text input fields for parameters
    st.sidebar.subheader('Choose a pair Crypto Currencies')
    default_crypto1 = 'BTC'
    default_crypto2 = 'USDT'
    CRYPTO1 = st.sidebar.text_input('Cryptocurrency 1', value=default_crypto1)
    CRYPTO2 = st.sidebar.text_input('Cryptocurrency 2', value=default_crypto2)

    st.sidebar.subheader('Choose SMAs to test out Strategy')
    # Add sliders for additional parameters
    SMA1 = st.sidebar.slider('SMA 1', min_value=3, max_value=20, value=10)
    SMA2 = st.sidebar.slider('SMA2', min_value=8, max_value=30, value=16)

    SYMBOL = CRYPTO1 + '/' + CRYPTO2

    #Parameter for Timeframe
    st.sidebar.subheader('Select Timeframe')
    options = ['1d', '3d', '1w', '1M']
    TIMEFRAME = st.sidebar.selectbox('Timeframe', options, index=2)

    START_DATE = '2016-01-01'

    # SMA1 = 10  # Customize the window for the first SMA
    # SMA2 = 16

    # Process data based on parameters
    crypto_df = extract_data(TIMEFRAME, START_DATE, SYMBOL, SMA1, SMA2)

    # Plot
    st.subheader(f'Price Action for {SYMBOL} Pair')
    buy_signals_df, sell_signals_df, fig = plot_price_chart(crypto_df, SYMBOL, TIMEFRAME, SMA1, SMA2)
    st.plotly_chart(fig)

    #Extracting Crypto info from market data
    crypto_name =  market_data[market_data['symbol']==CRYPTO1.lower()]['name'].values[0]
    crypto_current_price =  market_data[market_data['symbol']==CRYPTO1.lower()]['current_price'].values[0]
    crypto_marketcap =  market_data[market_data['symbol']==CRYPTO1.lower()]['market_cap'].values[0]
    crypto_price_pct_change =  market_data[market_data['symbol']==CRYPTO1.lower()]['price_change_percentage_24h'].values[0]
    crypto_price_vol =  market_data[market_data['symbol']==CRYPTO1.lower()]['total_volume'].values[0]
    crypto_price_circulating_supply =  market_data[market_data['symbol']==CRYPTO1.lower()]['circulating_supply'].values[0]
    crypto_price_total_supply =  market_data[market_data['symbol']==CRYPTO1.lower()]['total_supply'].values[0]
    crypto_price_ath =  market_data[market_data['symbol']==CRYPTO1.lower()]['ath'].values[0]
    crypto_price_ath_change_pct =  market_data[market_data['symbol']==CRYPTO1.lower()]['ath_change_percentage'].values[0]
    st.subheader('Info')
    st.write(f"""
        - Cryptocurrency Name: {crypto_name}     
        - Current Price: $ {crypto_current_price:,}
        - Market Cap: $ {crypto_marketcap:,}
        - Last 24h Pct Change (USD): {crypto_price_pct_change:.2f}%
        - Volume: $ {crypto_price_vol:,}
        - Circulating Supply: {crypto_price_circulating_supply:,}
        - Total Supply: {crypto_price_total_supply:,}
        - All Time High: $ {crypto_price_ath:,}
        - All Time High Change Pct: {crypto_price_ath_change_pct:.2f}%
        """)



    # Table
    st.subheader('Profit Percentage Table')
    signal_df_req, overall_profit_pct  = return_agg_profit_pct(buy_signals_df, sell_signals_df)
    st.dataframe(signal_df_req)

    st.write(f'Overall Profit Percentage: {overall_profit_pct:.2f}%')

    

    trending_coin_data = return_trending_coin_info()


    st.markdown('---')
    st.title('Overall Market Condition')
    st.subheader('Top Cyptos Today')
    st.dataframe(market_data)
    
    st.write("")
    st.subheader('Trending Cyptos Today 📈')
    st.write(f"**Trending Crypto for the day: {trending_coin_data.id.iloc[0]}**")

    st.write(f"""
        - Ticker Symbol: {trending_coin_data.symbol.iloc[0]}
        - Market Cap: {trending_coin_data.market_cap.iloc[0]}
        - Last 24h Pct Change (USD): {trending_coin_data.price_change_pct_usd_24h.iloc[0]:.2f}%
        """)
    st.table(trending_coin_data)




if __name__ == '__main__':
    main()


    
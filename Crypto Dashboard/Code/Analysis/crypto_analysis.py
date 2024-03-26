import streamlit as st
import ccxt
import plotly.graph_objs as go
import datetime

# Initialize the Binance exchange (you can choose a different exchange)
exchange = ccxt.binance()

# Define chart types and labels
chart_types = {'line': 'Line Chart', 'candlestick': 'Candlestick Chart'}
default_chart_type = 'line'

# Define timeframes and labels
timeframes = {'1h': '1 Hour', '1d': '1 Day', '1w': '1 Week'}
default_timeframe = '1h'

# Streamlit app layout
st.set_page_config(layout="wide")  # Make the app layout wider
st.title('Cryptocurrency Price Dashboard')


# Select timeframe using a dropdown
selected_timeframe = st.sidebar.selectbox('Select Timeframe', list(timeframes.keys()), index=0)


chart_width = 900
chart_height = 600


# Create a sidebar to select a cryptocurrency
selected_crypto = st.sidebar.selectbox('Select Cryptocurrency', ['BTC', 'ETH', 'XRP', 'LTC', 'BCH', 'ADA', 'DOT', 'BNB', 'LINK', 'XLM', 'XMR', 'TRX', 'EOS', 'NEO', 'DASH', 'ETC', 'ZEC', 'XEM', 'DOGE', 'ATOM', 'XTZ', 'BAT', 'ZRX', 'ONT', 'ALGO', 'QTUM', 'ICX', 'ZIL', 'KNC', 'SNT'])

# Fetch historical OHLCV data for the selected cryptocurrency and timeframe
crypto_symbol = f'{selected_crypto}/USDT'
crypto_ohlcv = exchange.fetch_ohlcv(crypto_symbol, selected_timeframe)

# Extract timestamps and closing prices from the data for the selected cryptocurrency
crypto_timestamps = [data[0] for data in crypto_ohlcv]
crypto_closing_prices = [data[4] for data in crypto_ohlcv]

# Convert timestamps to datetime objects for the selected cryptocurrency
crypto_dates = [datetime.datetime.utcfromtimestamp(ts / 1000) for ts in crypto_timestamps]

crypto_trace = go.Scatter(x=crypto_dates, y=crypto_closing_prices,
                        mode='lines', name=f'{selected_crypto}/USDT')

crypto_layout = go.Layout(title=f'{selected_crypto} Price Time Series ({timeframes[selected_timeframe]})',
                           xaxis=dict(title='Time'),
                           yaxis=dict(title=f'Price ({selected_crypto})'),
                           showlegend=True,
                           width=chart_width,
                           height=chart_height)
crypto_fig = go.Figure(data=[crypto_trace], layout=crypto_layout)

# Display the Plotly figure for the selected cryptocurrency
st.plotly_chart(crypto_fig)

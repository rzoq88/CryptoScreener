import os, csv
import talib
import yfinance as yf
import pandas
from flask import Flask, escape, request, render_template
from patterns import candlestick_patterns
import streamlit as st
import requests
import os
import sys
import subprocess

# check if the library folder already exists, to avoid building everytime you load the pahe
if not os.path.isdir("/tmp/ta-lib"):

    # Download ta-lib to disk
    with open("/tmp/ta-lib-0.4.0-src.tar.gz", "wb") as file:
        response = requests.get(
            "http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz"
        )
        file.write(response.content)
    # get our current dir, to configure it back again. Just house keeping
    default_cwd = os.getcwd()
    os.chdir("/tmp")
    # untar
    os.system("tar -zxvf ta-lib-0.4.0-src.tar.gz")
    os.chdir("/tmp/ta-lib")
    os.system("ls -la /app/equity/")
    # build
    os.system("./configure --prefix=/home/appuser")
    os.system("make")
    # install
    os.system("make install")
    # back to the cwd
    os.chdir(default_cwd)
    sys.stdout.flush()

# add the library to our current environment
from ctypes import *

lib = CDLL("/home/appuser/lib/libta_lib.so.0.0.0")
# import library
try:
    import talib
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--global-option=build_ext", "--global-option=-L/home/appuser/lib/", "--global-option=-I/home/appuser/include/", "ta-lib"])
finally:
    import talib


    
app = Flask(__name__)

@app.route('/snapshot')
def snapshot():
    with open('datasets/symbols.csv') as f:
        for line in f:
            if "," not in line:
                continue
            symbol = line.split(",")[0]
            data = yf.download(symbol, start="2020-01-01", end="2020-08-01")
            data.to_csv('datasets/daily/{}.csv'.format(symbol))

    return {
        "code": "success"
    }

@app.route('/')
def index():
    pattern  = request.args.get('pattern', False)
    stocks = {}

    with open('datasets/symbols.csv') as f:
        for row in csv.reader(f):
            stocks[row[0]] = {'company': row[1]}

    if pattern:
        for filename in os.listdir('datasets/daily'):
            df = pandas.read_csv('datasets/daily/{}'.format(filename))
            pattern_function = getattr(talib, pattern)
            symbol = filename.split('.')[0]

            try:
                results = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = results.tail(1).values[0]

                if last > 0:
                    stocks[symbol][pattern] = 'bullish'
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                else:
                    stocks[symbol][pattern] = None
            except Exception as e:
                print('failed on filename: ', filename)

    return render_template('index.html', candlestick_patterns=candlestick_patterns, stocks=stocks, pattern=pattern)

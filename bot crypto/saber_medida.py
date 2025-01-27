import pandas as pd
import os 
import time 
from binance.client import Client
from binance.enums import *

#from dotenv import load_dotenv
#load_dotenv()

api_key = os.getenv("KEY_BINANCE")
secret_key = os.getenv("SECRET_BINANCE")

cliente_binance = Client(api_key, secret_key)

symbol_info = cliente_binance.get_symbol_info('BTCUSDT')
lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
min_qty = float(lot_size_filter['minQty'])
max_qty = float(lot_size_filter['maxQty'])
step_size = float(lot_size_filter['stepSize'])

print(lot_size_filter, min_qty, max_qty, step_size)


# Parâmetros do Ativo e Operações
codigo_operado = "BTCBRL"  # Ativo negociado
ativo_operado = "BTC"      # Ativo principal
periodo_candle = Client.KLINE_INTERVAL_1HOUR
quantidade = 0.00004       # Quantidade mínima a ser negociada
posicao_atual = False      # Controle da posição atual (se estamos comprados ou não)


# Parâmetros do Ativo e Operações
codigo_operado = "ETHBRL"  # Ativo negociado
ativo_operado = "ETH"      # Ativo principal
periodo_candle = Client.KLINE_INTERVAL_1HOUR
quantidade = 0.001        # Quantidade mínima a ser negociada
posicao_atual = False      # Controle da posição atual (se estamos comprados ou não)



# Parâmetros do Ativo e Operações
codigo_operado = "XRPBRL"  # Ativo negociado
ativo_operado = "XRP"      # Ativo principal
periodo_candle = Client.KLINE_INTERVAL_1HOUR
quantidade = 1       # Quantidade mínima a ser negociada
posicao_atual = False      # Controle da posição atual (se estamos comprados ou não)
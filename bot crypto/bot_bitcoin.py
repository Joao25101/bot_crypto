import pandas as pd
import os
import time
from binance.client import Client
from binance.enums import *

# Chaves de API
api_key = os.getenv("KEY_BINANCE")
secret_key = os.getenv("SECRET_BINANCE")

cliente_binance = Client(api_key, secret_key)

# Parâmetros do Ativo e Operações
codigo_operado = "BTCBRL"  # Ativo negociado
ativo_operado = "BTC"      # Ativo principal
periodo_candle = Client.KLINE_INTERVAL_1HOUR
quantidade_base = 0.0001  # Quantidade base mínima
posicao_atual = False      # Controle da posição atual (se estamos comprados ou não)

# Função para buscar dados de candles
def pegando_dados(codigo, intervalo):
    candles = cliente_binance.get_klines(symbol=codigo, interval=intervalo, limit=1000)
    precos = pd.DataFrame(candles)
    precos.columns = ["tempo_abertura", "abertura", "maxima", "minima", "fechamento", "volume", 
                      "tempo_fechamento", "moedas_negociadas", "numero_trades", 
                      "volume_ativo_base_compra", "volume_ativo_cotação", "-"]
    precos = precos[["fechamento", "maxima", "minima", "tempo_fechamento"]]
    precos["fechamento"] = pd.to_numeric(precos["fechamento"])
    precos["maxima"] = pd.to_numeric(precos["maxima"])
    precos["minima"] = pd.to_numeric(precos["minima"])
    precos["tempo_fechamento"] = pd.to_datetime(precos["tempo_fechamento"], unit="ms").dt.tz_localize("UTC")
    precos["tempo_fechamento"] = precos["tempo_fechamento"].dt.tz_convert("America/Sao_Paulo")
    return precos

# Função para calcular RSI
def calcular_rsi(dados, periodo=14):
    delta = dados['fechamento'].diff()
    ganho = delta.where(delta > 0, 0)
    perda = -delta.where(delta < 0, 0)
    
    media_ganho = ganho.rolling(window=periodo).mean()
    media_perda = perda.rolling(window=periodo).mean()
    
    rs = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))
    
    dados['rsi'] = rsi
    return dados

# Função para calcular MACD
def calcular_macd(dados, rapida=12, lenta=26, sinal=9):
    dados["ema_rapida"] = dados["fechamento"].ewm(span=rapida, adjust=False).mean()
    dados["ema_lenta"] = dados["fechamento"].ewm(span=lenta, adjust=False).mean()
    dados["macd"] = dados["ema_rapida"] - dados["ema_lenta"]
    dados["macd_sinal"] = dados["macd"].ewm(span=sinal, adjust=False).mean()
    return dados

# Função para calcular Bollinger Bands
def calcular_bollinger(dados, periodo=20, desvios=2):
    dados["media_bollinger"] = dados["fechamento"].rolling(window=periodo).mean()
    dados["bollinger_superior"] = dados["media_bollinger"] + (dados["fechamento"].rolling(window=periodo).std() * desvios)
    dados["bollinger_inferior"] = dados["media_bollinger"] - (dados["fechamento"].rolling(window=periodo).std() * desvios)
    return dados

# Estratégia de Trade
def estrategia_trade(dados, codigo_ativo, ativo_operado, quantidade_base, posicao):
    # Calcular indicadores
    dados = calcular_rsi(dados)
    dados = calcular_macd(dados)
    dados = calcular_bollinger(dados)
    
    # Últimos valores dos indicadores
    ultima_rsi = dados['rsi'].iloc[-1]
    ultimo_macd = dados["macd"].iloc[-1]
    ultimo_macd_sinal = dados["macd_sinal"].iloc[-1]
    ultimo_preco = dados["fechamento"].iloc[-1]
    bollinger_sup = dados["bollinger_superior"].iloc[-1]
    bollinger_inf = dados["bollinger_inferior"].iloc[-1]

    print(f"RSI: {ultima_rsi} | MACD: {ultimo_macd} | Preço Atual: {ultimo_preco}")

    # Obtendo saldo atual
    conta = cliente_binance.get_account()
    for ativo in conta["balances"]:
        if ativo["asset"] == ativo_operado:
            quantidade_atual = float(ativo["free"])
    
    # Condições de Compra
    if ultimo_preco < bollinger_inf and ultima_rsi < 30 and ultimo_macd > ultimo_macd_sinal:
        if not posicao:
            order = cliente_binance.create_order(
                symbol=codigo_ativo,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantidade_base
            )
            print("COMPROU O ATIVO")
            posicao = True

    # Condições de Venda
    elif ultimo_preco > bollinger_sup and ultima_rsi > 70 and ultimo_macd < ultimo_macd_sinal:
        if posicao:
            order = cliente_binance.create_order(
                symbol=codigo_ativo,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=round(quantidade_atual, 5)
            )
            print("VENDEU O ATIVO")
            posicao = False

    return posicao

# Loop principal para execução contínua
while True:
    try:
        # Buscar dados atualizados
        dados_atualizados = pegando_dados(codigo=codigo_operado, intervalo=periodo_candle)
        
        # Executar estratégia de trade
        posicao_atual = estrategia_trade(
            dados=dados_atualizados, 
            codigo_ativo=codigo_operado, 
            ativo_operado=ativo_operado, 
            quantidade_base=quantidade_base, 
            posicao=posicao_atual
        )
        
        # Aguardar 30 minutos antes do próximo ciclo
        time.sleep(30 * 60)
    
    except Exception as e:
        print(f"Erro no loop principal: {e}")
        time.sleep(60)  # Espera antes de tentar novamente em caso de erro

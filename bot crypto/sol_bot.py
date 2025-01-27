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
codigo_operado = "SOLBRL"
ativo_operado = "SOL"
periodo_candle = Client.KLINE_INTERVAL_1HOUR
quantidade = 0.050     # Quantidade mínima a ser negociada
posicao_atual = False      # Controle da posição atual (se estamos comprados ou não)

# Função para buscar dados de candles
def pegando_dados(codigo, intervalo):
    candles = cliente_binance.get_klines(symbol=codigo, interval=intervalo, limit=1000)
    precos = pd.DataFrame(candles)
    precos.columns = ["tempo_abertura", "abertura", "maxima", "minima", "fechamento", "volume", 
                      "tempo_fechamento", "moedas_negociadas", "numero_trades", 
                      "volume_ativo_base_compra", "volume_ativo_cotação", "-"]
    precos = precos[["fechamento", "tempo_fechamento"]]
    precos["fechamento"] = pd.to_numeric(precos["fechamento"])
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

# Estratégia de Trade
def estrategia_trade(dados, codigo_ativo, ativo_operado, quantidade, posicao):
    # Calcular indicadores
    dados = calcular_rsi(dados, periodo=14)
    dados["media_rapida"] = dados["fechamento"].rolling(window=7).mean()
    dados["media_devagar"] = dados["fechamento"].rolling(window=40).mean()
    
    ultima_rsi = dados['rsi'].iloc[-1]
    ultima_media_rapida = dados["media_rapida"].iloc[-1]
    ultima_media_devagar = dados["media_devagar"].iloc[-1]
    
    print(f"RSI: {ultima_rsi} | Média Rápida: {ultima_media_rapida} | Média Devagar: {ultima_media_devagar}")

    # Obtendo saldo atual
    conta = cliente_binance.get_account()
    for ativo in conta["balances"]:
        if ativo["asset"] == ativo_operado:
            quantidade_atual = float(ativo["free"])
    
    # Condições de Compra
    if ultima_media_rapida > ultima_media_devagar and ultima_rsi < 70:
        if not posicao:
            order = cliente_binance.create_order(
                symbol=codigo_ativo,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantidade
            )
            print("COMPROU O ATIVO")
            posicao = True

    # Condições de Venda
    elif ultima_media_rapida < ultima_media_devagar and ultima_rsi > 30:
        if posicao:
            order = cliente_binance.create_order(
                symbol=codigo_ativo,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=round(quantidade_atual, 5)  # Ajuste para evitar erros de precisão
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
            quantidade=quantidade, 
            posicao=posicao_atual
        )
        
        # Aguardar 30 minutos antes do próximo ciclo
        time.sleep(30 * 60)
    
    except Exception as e:
        print(f"Erro no loop principal: {e}")
        time.sleep(60)  # Espera antes de tentar novamente em caso de erro

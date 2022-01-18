from io import IncrementalNewlineDecoder
import threading
from typing import final
from requests import *
import json
from requests.exceptions import RetryError
from requests.models import Response
from time import sleep
from sys import argv
from worldproxy import Proxy
import sofasgram
import traceback
from datetime import datetime
import os.path
from os import mkdir
from queue import Queue
from pathlib import Path


print("Sofaspy v2.6.0 - Unstable [01/12/2021]")
print("==============================")
print("[*] Remoção do Sleep entre o inicio das Threads Principais.")
print("[*] Mensagem para checar se o tempo está certo.")
print("[*] Remoção da Queue de jogos armazenados.")
print("[*] Jogos agora são consultados dentro do loop for de liveGames.")
print("[*] Command Line removido/comentado.")
print("[*] Os campos de período não passam mais por tratativas, são analisados cruamente")
print("[*] Os campos de período agora são analisados pelo objeto status.description, não mais pelo campo 'lastPeriod'.")
print("[*] Pausa de 8s à cada 30 proxies para evitar sobrecarga de tarefas.")
print("[*] Mais um site adicionado à bibliotecas de busca de proxies (free-proxy.cz).")
print("==============================\n")
verbose = False
if "-v" in argv:
    print(f"[!] Verbose ligado.")
    verbose = True
# Game list
gamelistCompress = [] # Lista com todos os dados dos jogos ao vivo (chaveado por IDs)
# ETags
etag = {}

token = "2070425936:AAFwmuDYzB3TMZp56MnDdpndxNymPkhq158"
telebot = sofasgram.Bot(token)



# Headers para as requisições
headers = {
    "cache-control": "max-age=0",
    "sec-ch-ua": '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
    "sec-ch-ua-mobile": "?0",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    "sec-ch-ua-platform": "\"Windows\"",
    "accept": "*/*",
    "origin": "https://www.sofascore.com",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://www.sofascore.com/",
#    "accept-encoding": "gzip, deflate, br",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

def verb(message):
    if verbose:
        print(f"[!]{message}")

def fetchFail(resp: Response):
    """
    Checa se o site aceita requisições desse IP.
    """
    if 'error' in resp.text or 'data-translate="error"' in resp.text:

        return True
    else:
        return False


def setCurrentProxy(proxy: str):
    """
    Checa se o Proxy é estável.
    """
    proxy = {
        'http' : proxy,
        'https': proxy
    }
    try:
        resp = get('http://sofascore.com', headers=headers, proxies=proxy, timeout=8)

        if fetchFail(resp):
            return False

        else:
            threading.Thread(target=main, args=(proxy,)).start()
            return True
    except:
        return False



def getGameInfo(id: str, proxy: dict):
    """
    Retorna as Informações de um jogo específico pelo Id dele.\n
    Retorna False se fetchFail() for True.
    """
    if "single-game" in etag:
        headers["ETag"] = etag["single-game"]
    resp = get('http://api.sofascore.com/api/v1/event/' + id, headers=headers, proxies=proxy, timeout=8)

    if "ETag" in resp.headers:
        etag["single-game"] = resp.headers['ETag']

    if fetchFail(resp):
        return False

    try:
        return json.loads(resp.text)
    except:
        return False


def getGameOdds(id: str, proxy: dict):
    """
    Retorna as Odds do time da casa e do time de fora.\n
    Retorna False se fetchFail() for True.
    """
    if "winning-odds" in etag:
        headers["ETag"] = etag["winning-odds"]
    try:
        resp = get('http://api.sofascore.com/api/v1/event/{}/provider/1/winning-odds'.format(id), headers=headers, proxies=proxy, timeout=8)

        if "ETag" in resp.headers:
            etag["winning-odds"] = resp.headers['ETag']
        if fetchFail(resp):
            return False
        return json.loads(resp.text)
    except Exception as e:
        return False

def getBothTeamHistoric(customId: str, proxy: dict):
    if "teams-historic" in etag:
        headers["ETag"] = etag["teams-historic"]
    try:
        resp = get(f'http://api.sofascore.com/api/v1/event/{customId}/h2h/events', headers=headers, proxies=proxy, timeout=8)

        if "ETag" in resp.headers:
            etag["teams-historic"] = resp.headers['ETag']
        if fetchFail(resp):
            return False
        return json.loads(resp.text)
    except Exception as e:
        return False

def getGameFeatures(id: str, proxy: dict):
    """
    Retorna as Features do jogo.
    Retorna False se fetchFail() for True.
    """
    if "featured" in etag:
        headers["ETag"] = etag["featured"]
    try:
        resp = get('http://api.sofascore.com/api/v1/event/{}/odds/1/featured'.format(id), headers=headers, proxies=proxy, timeout=8)

        if "ETag" in resp.headers:
            etag["featured"] = resp.headers['ETag']
        if fetchFail(resp):
            return False
        return json.loads(resp.text)
    except:
        return False

def getGameAll(id: str, proxy: dict):

    if "all" in etag:
        headers["ETag"] = etag["all"]
    try:
        resp = get('http://api.sofascore.com/api/v1/event/{}/odds/1/all'.format(id), headers=headers, proxies=proxy, timeout=8)

        if "ETag" in resp.headers:
            etag["all"] = resp.headers['ETag']
        if fetchFail(resp):
            return False
        return json.loads(resp.text)
    except:
        return False


def getGameStatistics(id: str, proxy: dict):
    """
    Retorna as estatísticas do jogo.\n
    Retorna False se fetchFail() for True.
    """
    if "statistics" in etag:
        headers["ETag"] = etag["statistics"]
    try:
        resp = get(f'http://api.sofascore.com/api/v1/event/{id}/statistics', headers=headers, proxies=proxy, timeout=8)

        if "ETag" in resp.headers:
            etag["statistics"] = resp.headers['ETag']
        if fetchFail(resp):
            return False
        return json.loads(resp.text)
    except Exception as e:
        return False


def getGameh2h(id: str, proxy: dict):
    if "h2h" in etag:
        headers["ETag"] = etag["h2h"]
    try:
        resp = get(f'http://api.sofascore.com/api/v1/event/{id}/h2h', headers=headers, proxies=proxy, timeout=8)

        if "ETag" in resp.headers:
            etag["h2h"] = resp.headers['ETag']
        if fetchFail(resp):
            return False
        return json.loads(resp.text)
    except:
        return False


def getSingleGame(id: str, proxy: dict):
    try:
        resp = get(f'http://api.sofascore.com/api/v1/event/{id}', headers=headers, proxies=proxy, timeout=4)
        print(resp.content)
        if fetchFail(resp):
            return False
        return json.loads(resp.text)
    except:
        return False

def getLiveGames(proxy: dict):
    """
    Retorna uma lista de jogos ao vivo.\n
    Retorna False se fetchFail() for True.
    """
    try:
        resp = get('http://api.sofascore.com/api/v1/sport/football/events/live', headers=headers, proxies=proxy, timeout=8)
        if fetchFail(resp):
            return False
        activeGames = json.loads(resp.text)
        return activeGames
    except Exception as e:
        return False

def saveGame(game, type, value):
    data = json.load(open('jogos.json', 'r'))
    if game['id'] in [dfid['id'] for dfid in data]:
        for d in data:
            if game['id'] == d['id']:
                d[type] = value
    else:
        data.append({'id' : game['id'], type : value})
    json.dump(data, open('jogos.json', 'w'), indent=4)



# Jogos
lastUpdate = "Nenhum"
lastGameUpdate = []

# Variáveis das regras
# percentOddTarget = 20 # Porcentagem preferencial para Porcentagem da Odd
# timeOddTarget = 600 # Tempo de jogo para enviar Odd. Envia se for menor ou igual à esse valor.
# periodOddTarget = "1st half" # Período de jogo para enviar mensagem de Vitória

# percent05ht15TargetMinute = 5 # Até que tempo enviará 0,5ht e 1,5ht
# percent05ht15TargetPeriod = "1st half" # De qual período
# percent05htTarget = 10 # Porcentagem mínima para enviar 0,5ht
# percent15htTarget = 10 # Porcentagem mínima para enviar 1,5

# generalPressionMinute = 0 # Minuto para mensagem de Pressão. Envia se for maior ou igual à esse valor
# generalPressionPeriod = '1st half' # Período de jogo para enviar mensagem de Pressão
# pressionDefaultPercentTarget = 10 # Porcentagem para regra de pressão(posse de bola) de um dos dois times. Envia se for maior ou igual à esse valor
# pressionDefaultShotsTarget = 3 # Quantidade de finalizações para enviar a mensagem de pressão. Envia se for maior ou igual à esse valor

# pressionGoalShotsTarget = 5 # Quantidade que um dos dois times tem que finalizar em direção ao gol para enviar a mensagem. Envia se for maior ou igual à esse valor

# cornerPeriod = '1st half' # Período de jogo para enviar mensagem de Escanteio
# cornerMinute = 600 # Minuto para mensagem de escanteio. Envia se for menor ou igual à esse valor
# cornerKicksQuantity = 2 # Quantidade de escanteios para enviar a mensagem








percentOddTarget = 200 # Porcentagem preferencial para Porcentagem da Odd
timeOddTarget = 6 # Tempo de jogo para enviar Odd. Envia se for menor ou igual à esse valor.
periodOddTarget = "1st half" # Período de jogo para enviar mensagem de Vitória

percent05ht15TargetMinute = 5 # Até que tempo enviará 0,5ht e 1,5ht
percent05ht15TargetPeriod = "1st half" # De qual período
percent05htTarget = 70 # Porcentagem mínima para enviar 0,5ht
percent15htTarget = 70 # Porcentagem mínima para enviar 1,5

generalPressionMinute = 17 # Minuto para mensagem de Pressão. Envia se for maior ou igual à esse valor
generalPressionPeriod = '1st half' # Período de jogo para enviar mensagem de Pressão
pressionDefaultPercentTarget = 65 # Porcentagem para regra de pressão(posse de bola) de um dos dois times. Envia se for maior ou igual à esse valor
pressionDefaultShotsTarget = 2 # Quantidade de finalizações para enviar a mensagem de pressão. Envia se for maior ou igual à esse valor

pressionGoalShotsTarget = 3 # Quantidade que um dos dois times tem que finalizar em direção ao gol para enviar a mensagem. Envia se for maior ou igual à esse valor

cornerPeriod = '1st half' # Período de jogo para enviar mensagem de Escanteio
cornerMinute = 35 # Minuto para mensagem de escanteio. Envia se for menor ou igual à esse valor
cornerKicksQuantity = 4 # Quantidade




# Lista de IDs dos jogos que foram enviados baseados nas regras
oddListMessage = []
h2hListMessage = []
bothTeamListMessage = []
statisticsPressionListMessage = []
statisticsGoalListMessage = []
statisticsCornerListMessage = []

# Variáveis de relatórios
over05Ok = 0
over05Stored = 0
over15Ok = 0
over15Stored = 0
winningOk = 0
winningStored = 0
cornerStored = 0
cornerOk = 0
noAccessToData = 0

def consultSavedGame():
    print(f"Thread de Relatório iniciada... Aguardando horário (23:30)")
    inCycle = False
    while True:
        sleep(50)
        if f"{datetime.strftime(datetime.now(), '%H:%M')}" == "23:30" and not inCycle:
            inCycle = True
            print(f"[{datetime.strftime(datetime.now(), '%H:%M:%S')}] Gerando relatório relatório...")
            global over05Ok, over05Stored, over15Ok, over15Stored, winningOk, winningStored, noAccessToData, gameIdList, cornerStored
            def makeResquests(id, fieldsData, proxy):
                global over05Ok, over05Stored, over15Ok, over15Stored, winningOk, winningStored, noAccessToData, gameIdList, cornerStored
                if id in gameIdList:
                    result = getSingleGame(id, proxy)
                    if result:
                        result = result.get('event')
                        try:
                            if result.get('status', {'description' : None}).get('description') == "Ended" or result.get('status', {'type' : None}).get('type') == 'finished':

                                gameIdList = list(set(gameIdList) - set([id]))
                                homeGoals = result.get('homeScore', {'current' : None}).get('current')
                                awayGoals = result.get('awayScore', {'current' : None}).get('current')
                                if fieldsData.get('regra-odd'):
                                    ro = fieldsData.get('regra-odd')
                                    if homeGoals != None and awayGoals != None:
                                        if int(homeGoals) > int(awayGoals) and ro == 'homeFav':
                                            scannedGameDict[str(id)]['w'] = True
                                        if int(awayGoals) > int(homeGoals) and ro == 'awayFav':
                                            scannedGameDict[str(id)]['w'] = True
                                        else: pass
                                if fieldsData.get('05ht'):
                                    goalsHThome = result.get('homeScore', {'period1' : None}).get('period1')
                                    goalsHTaway = result.get('awayScore', {'period1' : None}).get('period1')
                                    if goalsHThome + goalsHTaway >= 1:
                                        scannedGameDict[str(id)]['0'] = True
                                    else: pass
                                if fieldsData.get('1,5AT'):
                                    if homeGoals + awayGoals >= 1.5:
                                        scannedGameDict[str(id)]['1'] = True
                                if fieldsData.get('cornerKicks'):
                                    try:
                                        getCorner = getGameStatistics(id, proxy)
                                        statistics1t = getCorner['statistics'][1]['groups'] #  Estatisticas do primeiro tempo
                                        cornerKicks = [n for n in statistics1t if n['groupName'] == "TVData"][0]['statisticsItems'][0]
                                        cornerKicksHome = int(cornerKicks['home'])
                                        cornerKicksAway = int(cornerKicks['away'])

                                        if cornerKicksAway + cornerKicksHome >= 5:
                                            scannedGameDict[str(id)]['ck'] = True
                                    except:
                                        cornerValidate.append(id)
                            else:
                                print(f"O jogo {result['homeTeam']['name']} x {result['awayTeam']['name']} ainda está rolando. Conferir se a informação procede.")
                                gameIdList = list(set(gameIdList) - set([id]))

                                scannedGameDict[result['id']]['running'] = True

                        except:
                            pass
                else: pass
            proxies = [{'http' : proxy, 'https': proxy} for proxy in Proxy().proxies]
            stored = json.load(open('jogos.json', 'r'))
            gameIdList = [game['id'] for game in stored]
            scannedGameDict = {}
            for gameid in gameIdList: scannedGameDict[str(gameid)] = { "w" : False, "0" : False, "1": False}
            progress = len(gameIdList)
            gameDictList = [game for game in stored]
            cornerValidate = []
            threadList = []
            for game in gameDictList:
                if len(gameIdList) == 0:
                    break

                keysnValues = {"regra-odd": False, '05ht': False, '1,5AT': False, "cornerKicks": False}
                if game.get('regra-odd'):
                    winningStored += 1
                    keysnValues['regra-odd'] = game.get('regra-odd')
                if game.get('05ht'):
                    over05Stored += 1
                    keysnValues['05ht'] = game.get('05ht')
                if game.get('1,5AT'):
                    over15Stored += 1
                    keysnValues['1,5AT'] = game.get('1,5AT')
                if game.get('cornerKicks'):
                    cornerStored += 1
                    keysnValues['cornerKicks'] = game.get('cornerKicks')

                for i, p in enumerate(proxies):
                    if game['id'] not in gameIdList:
                        break
                    if i%(len(gameDictList) * 3) == 0:
                        sleep(0.5)
                    else:

                        t1 = threading.Thread(target=makeResquests, args=(game['id'], keysnValues, p))
                        threadList.append(t1)
                        t1.start()
                        # t1.start()

            for thread in threadList:
                thread.join()
            print("Relatório Concluído. Enviando para Telegram...")
            date = datetime.strftime(datetime.now(), "%d/%m/%Y")
            over05Ok = 0
            over15Ok = 0
            winningOk = 0
            cornerOk = 0
            backupCorner = cornerStored
            wRunning = 0
            for k in scannedGameDict.values():
                if k.get('running'):
                    if k.get('w'):
                        winningStored -= 1
                        wRunning += 1
                    if k.get('0'): over05Stored -= 1
                    if k.get('1'): over15Stored -= 1
                    if k.get('ck'): cornerStored -= 1
                else:
                    if k.get('w'): winningOk += 1
                    if k.get('0'): over05Ok += 1
                    if k.get('1'): over15Ok += 1
                    if k.get('ck'): cornerOk += 1
            print(scannedGameDict)
            cornerValidate = list(set(cornerValidate))
            for chat in telebot.getChats():
                telebot.sendMessage(chat['id'],
                "TOTAIS\n"
                f"{date}\n{'-' * (len(str(date)) * 2) }\n"
                "VITORIA\n"
                f"ENVIADOS={winningStored}\n"
                f"BATERAM={winningOk}\n"
                f"EM JOGO={wRunning}\n"
                f"{'-' * (len(str(date)) * 2) }\n"
                "HT\n"
                f"ENVIADOS={over05Stored}\n"
                f"BATERAM={over05Ok}\n"
                f"{'-' * (len(str(date)) * 2) }\n"
                "1,5\n"
                f"ENVIADOS={over15Stored}\n"
                f"BATERAM={over15Ok}\n"
                f"{'-' * (len(str(date)) * 2) }\n"
                "ESCANTEIOS >= 4\n"
                f"ENVIADOS={cornerStored}\n"
                f"BATERAM={cornerOk}\n"
                f"VERIFICAR={', '.join(list(map(str, cornerValidate)))}\n"
                f"{'-' * (len(str(date)) * 2) }\n"
                )
            print("Salvando relatório...")
            if not os.path.isdir("relatorios"):
                mkdir("relatorios")

            with open(f'relatorios/RELATORIO - {datetime.strftime(datetime.now(), "%d-%m-%Y - %Hh-%Mm-%Ss")}.txt', 'w') as output:
                output.write("TOTAIS\n"
                f"{date}\n{'-' * (len(str(date)) * 2) }\n"
                "VITORIA\n"
                f"ENVIADOS={winningStored}\n"
                f"BATERAM={winningOk}\n"
                f"{'-' * (len(str(date)) * 2) }\n"
                "HT\n"
                f"ENVIADOS={over05Stored}\n"
                f"BATERAM={over05Ok}\n"
                f"{'-' * (len(str(date)) * 2) }\n"
                "1,5\n"
                f"ENVIADOS={over15Stored}\n"
                f"BATERAM={over15Ok}\n"
                f"{'-' * (len(str(date)) * 2) }\n"
                "ESCANTEIOS >= 4\n"
                f"ENVIADOS={cornerStored}\n"
                f"BATERAM={cornerOk}\n"
                f"{'-' * (len(str(date)) * 2) }\n"
                f"{scannedGameDict}"
                )
                print(f"Relatório salvo como: RELATORIO - {datetime.strftime(datetime.now(), '%d-%m-%Y - %Hh-%Mm-%S')}.txt")
                output.close()


            with open('jogos.json', 'w') as f:
                f.write('[]')
                f.close()
            inCycle = False
            sleep(5)

def messagesQueue():
    while True:
        sleep(2.5)
        if not messageQueue.empty():
            t = messageQueue.get()
            try:
                print(t)
                telebot.sendMessage(*t)
            except:
                messageQueue.queue.insert(0, t)
                print("[Telegram] Houve um problema de Conexão, e a mensagem não pode ser enviada. Tentando novamente em 10s")
                sleep(10)
                pass

ip = "45.33.103.249"
gameQueue = Queue()
def main(proxy: dict):
    global allgamesConsulted, gamelistCompress, lastUpdate, lastGameUpdate
    minute = 7 # Até quantos minutos de jogo devem ser enviadas as mensagens configuradas para início de jogo.
    verb("Executando função main...")
    if not allgamesConsulted:
        verb("Consultando lista de jogos ao vivo...")
        try:
            liveGames = getLiveGames(proxy)
            print(liveGames)
           # print(proxy)
        except:
            print(f"Error: {traceback.format_exc()}")

        liveGames = [{
            "id": data['id'],
            "tournament" : {
                "name" : data['tournament']['name']
            },
            "customId" : data['customId'],
            "message" : "",
            "homeTeam" : data['homeTeam'],
            "awayTeam" : data['awayTeam'],
            "homeScore" : data['homeScore'],
            "awayScore" : data['awayScore'],
            "startTimestamp" : data['startTimestamp'],
            # "realNamePeriod": data.get('status').get('description'),
            "lastPeriod" : data.get('status').get('description'),
            "currentPeriodStartTimestamp": data.get('time', {'currentPeriodStartTimestamp' : None}).get('currentPeriodStartTimestamp')
            } for data in liveGames['events']] if liveGames else None # Armazena todos os jogos
        if liveGames:
            allgamesConsulted = True
            lastUpdate = datetime.strftime(datetime.now(), "%H:%M:%S")
            gamelistCompress = liveGames.copy()
            lastGameUpdate = liveGames.copy()

            for lm in [var for var in globals() if var.endswith('ListMessage')]:
                varname = lm
                for n in eval(lm):
                    if n not in liveGames:
                        verb(f"O jogo cujo id é {n} não está mais rolando.")
                        verb(f"[ANTES][{varname}] = {lm}")
                        exec(f'{lm} = set({lm}) - set([{n}])')
                        verb(f"[DEPOIS][{varname}] = {lm}")
        else:
            return
            # list(map(lambda u: [u.remove(n) for n in u if n not in [u['id'] for u in liveGames]], [eval(var) for var in globals() if var.endswith('ListMessage')]))
            # list(map(lambda u: [u.remove(n) for n in set(u) - set([_g['id'] for _g in liveGames])], [eval(var) for var in globals() if var.endswith('ListMessage')])) # Remove os IDs armazenados nas listas de mensagens enviadas caso o jogo não exista mais,
                                       # para evitar que a lista fique pesada e trave o programa.
        try:
            for game in liveGames:
                #print(f"Consultando {game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']}")
                verb(f"[{game['id']}] Procurando regras de: {game['homeTeam']['name']} x {game['awayTeam']['name']}")

                #TODO
                # if game['lastPeriod'] == 'Halftime':
                #     verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Está em HT")
                #     game['lastPeriod'] = 'HT'
                # elif game['lastPeriod'] == '1st half':
                #     verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Está em 1T")
                #     game['lastPeriod'] = 'period1'
                # elif game['lastPeriod'] == '2nd half':
                #     verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Está em 2T")
                #     game['lastPeriod'] = 'period2'
                # else:
                #     verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Está inacessível")
                #     game['lastPeriod'] = 'Inacessível'
                #TODO

                dateTimeStartCurrentPeriod = int(game['currentPeriodStartTimestamp']) - (60*60*3)
                dateTimeNow = int(str(datetime.now().timestamp()).split(".")[0])

                dateMessageS = datetime.utcfromtimestamp(dateTimeStartCurrentPeriod).strftime('%d/%m/%Y - %H:%M')
                dateMessageMin =  datetime.utcfromtimestamp(dateTimeNow - dateTimeStartCurrentPeriod).strftime("%M")
                currentTimePeriod = '1T' if game.get('lastPeriod') == '1st half' else '2T' if game.get('lastPeriod') == '2nd half' else 'HT' if game.get('lastPeriod') == 'Halftime' else "Nenhum"
                dateMessageS = f"{datetime.strftime(datetime.now(), '%d/%m/%Y - %H:%M')}"
                print(f"{game['id']} | {game['lastPeriod']} | {currentTimePeriod}")

                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Está em {dateMessageMin} minutos.")
                game['timeInMinute'] = dateMessageMin
                if int(dateMessageMin) >= 46 and game['lastPeriod'] == "2nd half":
                    result = getSingleGame(game['id'], proxy)
                    if result:
                        result = result.get('event')
                        try:
                            if result.get('status', {'description' : None}).get('description') == "Ended" or result.get('status', {'type' : None}).get('type') == 'finished':
                                gamelistCompress.remove(game)
                                game['status'] = "Ended"
                        except:
                            pass
                            #print(f"Não foi possível excluir o jogo {game['homeTeam']['name']} x {game['awayTeam']['name']} da lista de jogos, pois ele não existe lá.")
                        finally:
                            print("Retornando 1")
                            return

                try:
                    messageBody = f"{game['tournament']['name']}\n"\
                        f"{game['homeTeam']['name']} {game['homeScore']['current']} x {game['awayScore']['current']} {game['awayTeam']['name']}\n"\
                        f"Time: {dateMessageS}\n"\
                        f"Live: {currentTimePeriod}:{dateMessageMin}min \n"\
                        f"Id: {game['id']}\n"
                    verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Todos os campos base da mensagem foram encontrados.")
                except:
                    print("Error: \n\n" + str(game))
                    print("Continuando...")
                    return

                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Pegando Features...")
                features = getGameFeatures(game['id'], proxy)
                #print("Features: " + str(features))
                if features:
                    game['featured'] = features['featured']
                    verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Features capturada.")
                else:
                    verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Features não encontrada. Tentando acessar Features pelo all...")
                    features = getGameAll(game['id'], proxy)
                    if features:
                        verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Features encontrada no all.")
                        features = {"default" : features['markets'][0]}
                        game['featured'] = features
                    else:
                        verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Sem features para esse jogo.")
                        game['featured'] = False

                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : {'Não se encaixa na regra winning-odds.' if not (game['id'] not in oddListMessage and int(dateMessageMin) <= timeOddTarget and currentTimePeriod == periodOddTarget) else 'Se encaixa em winning-odds'}")
                if game['id'] not in oddListMessage and int(dateMessageMin) <= timeOddTarget and game['lastPeriod'] == '1st half':
                    verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Pegando winning-odds...")
                    odds = getGameOdds(game['id'], proxy)
                    #print("Odds: " + str(odds))
                    if game['id'] not in oddListMessage:
                        if odds:
                            game['winning-odds'] = odds

                            verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Odds possivelmente disponíveis.")
                            hao = odds.get('home') or 0
                            aao = odds.get('away') or 0
                            if hao != 0 or aao != 0:
                                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Acessando Odds...")
                            if hao != 0:
                                hao = hao.get('actual') or 0
                                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Odds disponíveis para time da casa.")
                            if aao != 0:
                                aao = aao.get('actual') or 0
                                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Odds disponíveis para time de fora.")
                            greater = max(hao, aao)
                            if greater == 0:
                                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Odds Indisponíveis.")

                            greaterName = ('homeFav' if hao > aao else 'awayFav') if greater != 0 else None
                            if greaterName:
                                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Maior odd é para {greaterName}")
                            if hao != 0:
                                homeOddEx = round(100/odds['home']['expected'], 1)
                                homeOddExPer = f"{odds['home']['expected']:.2f}"
                                homeOddActPer = f"{odds['home']['actual']:.2f}"
                            else:
                                homeOddEx = "-.--"
                                homeOddExPer = "--"
                                homeOddActPer = "--"

                            if aao != 0:
                                awayOddEx = round(100/odds['away']['expected'], 1)
                                awayOddExPer = f"{odds['away']['expected']}"
                                awayOddActPer = f"{odds['away']['actual']}"
                            else:
                                awayOddEx = "-.--"
                                awayOddExPer = "--"
                                awayOddActPer = "--"



                            dateTimeStartCurrentPeriod = int(game['currentPeriodStartTimestamp'])
                            dateTimeNow = int(str(datetime.now().timestamp()).split(".")[0])


                            dateMessageS = datetime.utcfromtimestamp(dateTimeStartCurrentPeriod).strftime('%d/%m/%Y - %H:%M')
                            dateMessageMin =  datetime.utcfromtimestamp(dateTimeNow - dateTimeStartCurrentPeriod).strftime("%M")
                            try:
                                fid = game['featured']['default']['fid']
                                sourceId = game['featured']['default']['choices'][0]['sourceId']
                            except:
                                fid = False
                                sourceId = False
                            validBetRedirect = f"http://{ip}/?{fid}+{sourceId}" if sourceId != False else None
                            linkMessage = f"<a href=\"{validBetRedirect}\">Ver jogo no BET 365</a>" if sourceId != False else "Não há links Disponíveis."
                            verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : {'Não se encaixa na regra' if not (int(hao) >= percentOddTarget or int(aao) >= percentOddTarget) else 'Se encaixa na regra'}")

                            if (int(hao) >= percentOddTarget or int(aao) >= percentOddTarget):
                                verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Enviando mensagem e salvando em jogos.json...")
                                oddListMessage.append(game['id'])
                                saveGame(game, 'regra-odd', greaterName)
                                for chat in telebot.getChats():
                                    messageQueue.put((chat['id'],
                                    f"Probabilidade de ganhar >=  {greater}%\n" +
                                    messageBody +
                                    f"{game['homeTeam']['name']} odd {homeOddEx} X {homeOddExPer}% = {homeOddActPer}%\n"+
                                    f"{game['awayTeam']['name']} odd {awayOddEx} X {awayOddExPer}% = {awayOddActPer}%\n"+
                                    f"{linkMessage}"
                                    ), False)
                                    verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Mensagem enviada para o chat {chat['id']}")

                try:
                    homeOddEx = round(100/game['winning-odds']['home']['expected'], 1)
                    homeOddExPer = f"{game['winning-odds']['home']['expected']:.2f}"
                    homeOddActPer = f"{game['winning-odds']['home']['actual']:.2f}"
                except:
                    homeOddEx = 0
                    homeOddExPer = 0
                    homeOddActPer = 0

                try:
                    awayOddEx = round(100/game['winning-odds']['away']['expected'], 1)
                    awayOddExPer = f"{game['winning-odds']['away']['expected']:.2f}"
                    awayOddActPer = f"{game['winning-odds']['away']['actual']:.2f}"
                except:
                    awayOddEx = 0
                    awayOddExPer = 0
                    awayOddActPer = 0


                try:
                    fid = game['featured']['default']['fid']
                    sourceId = game['featured']['default']['choices'][0]['sourceId']
                except:
                    fid = False
                    sourceId = False

                validBetRedirect = f"https://{ip}/?{fid}+{sourceId}" if sourceId != False else None
                linkMessage = f"<a href=\"{validBetRedirect}\">Ver jogo no BET 365</a>" if sourceId != False else "Não há links Disponíveis."
                hasLinkMessage = True if linkMessage != "Não há links Disponíveis." else False



                if True: # TODO if hasLinkMessage
                    verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Checando Histórico dos times...")
                    bt = getBothTeamHistoric(game['customId'], proxy)
                    #print("bt: " + str(bt))
                    if not bt:
                        verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Não foi possível carregar histórico do time.")
                    if game['id'] not in bothTeamListMessage:
                        if bt:
                            verb(f"[{game['id']}] {game['homeTeam']['name']} x {game['awayTeam']['name']} : Histórico do time consultado. Checando campos dos jogos...")
                            gamesCount05ht = 0
                            gamesCount15 = 0
                            for match in bt['events']:
                                homeScore1Period = match.get("homeScore").get("period1") or 0
                                awayScore1Period = match.get("awayScore").get("period1") or 0


                                homeScoreAllPeriod = match.get("homeScore").get("current") or 0
                                awayScoreAllPeriod = match.get("awayScore").get("current") or 0

                                goalsht = homeScore1Period + awayScore1Period
                                goalsAllPeriod = homeScoreAllPeriod + awayScoreAllPeriod
                                if goalsht >= 1:
                                    gamesCount05ht += 1
                                if goalsAllPeriod > 1:
                                    gamesCount15 += 1



                            val05ht = f"{(gamesCount05ht/len(bt['events']) * 100):.2f}"
                            val15 = f"{(gamesCount15/len(bt['events']) * 100):.2f}"

                            alreadyInBTL = False
                            verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : {"Jogo não se encaixa nas regras de 0,5HT ou 1,5" if not (int(dateMessageMin) <= percent05ht15TargetMinute and game["lastPeriod"] == percent05ht15TargetPeriod and goalsht == 0) else "Jogo pode se encaixar nas regras de 0,5ht ou 1,5."}')
                            if int(dateMessageMin) <= percent05ht15TargetMinute and game['lastPeriod'] == percent05ht15TargetPeriod and goalsht == 0: #TODO trocar 600 por minute
                                if float(val05ht) >= percent05htTarget:
                                    verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Regra de 0,5ht é aplicada a esse jogo. Enviando mensagem...')

                                    message = (f"0,5 HT => {val05ht} %\n" +
                                        messageBody +
                                        f"{game['homeTeam']['name']} odd {homeOddEx} X {homeOddExPer}% = {homeOddActPer}%\n" +
                                        f"{game['awayTeam']['name']} odd {awayOddEx} X {awayOddExPer}% = {awayOddActPer}%\n" +
                                        f"{linkMessage}")

                                    bothTeamListMessage.append(game['id'])
                                    alreadyInBTL = True
                                    saveGame(game, '05ht', True)
                                    for chat in telebot.getChats():
                                        messageQueue.put((chat['id'], str(message)))
                                if float(val15) >= percent15htTarget:
                                    pass
                                    # verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Regra de 1,5 é aplicada a esse jogo. Enviando mensagem...')
                                    # message = (f"1,5 => {val15} %\n" +
                                    #     messageBody +
                                    #     f"{game['homeTeam']['name']} odd {homeOddEx} X {homeOddExPer}% = {homeOddActPer}%\n" +
                                    #     f"{game['awayTeam']['name']} odd {awayOddEx} X {awayOddExPer}% = {awayOddActPer}%\n" +
                                    #     f"{linkMessage}")

                                    # saveGame(game, '1,5AT', True)
                                    # if not alreadyInBTL:
                                    #     bothTeamListMessage.append(game['id'])
                                    # for chat in telebot.getChats():
                                    #     messageQueue.put((chat['id'], str(message)))

                    if game['id'] not in statisticsGoalListMessage or game['id'] not in statisticsPressionListMessage:
                        verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Pesquisando estatísticas...')
                        statistics = getGameStatistics(game['id'], proxy)
                        #print("statistics: " + str(statistics))
                        if not statistics:
                            verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Sem etatísticas para esse jogo.')
                        if statistics:
                            game['statistics'] = statistics
                
                            verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Checando campos de estatísticas...')
                            statisticsErrorPression = False
                            statisticsErrorCornerKicks = False
                            try:
                                statistics1t = statistics['statistics'][1]['groups'] #  Estatisticas do primeiro tempo
                                statistics = statistics['statistics'][0]['groups'] # Estatisticas de todos os períodos
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Campos de estatísticas para 1T e ALL validados!')
                            except:
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Sem campo de estatística para 1T ou ALL.')
                                statisticsErrorPression = True
                                pass
                            verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Checando campos para regra de pressão e gols...')
                            try:
                                ballPossession = [n for n in statistics if n['groupName'] == "Possession"][0]['statisticsItems'][0]
                                homeballPossession = int(ballPossession.get('home').split('%')[0])
                                awayballPossession = int(ballPossession.get('away').split('%')[0])
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Campos para pressão válidos!')
                            except:
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Sem campos para pressão.')
                                statisticsErrorPression = True
                                homeballPossession = "Sem dados."
                                awayballPossession = "Sem dados."
                                pass
                            try:
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Checando campos de chutes em direção ao gol...')
                                shotsOnTarget = [n for n in statistics if n['groupName'] == "Shots"][0]['statisticsItems'][1]
                                homeShotsOT = int(shotsOnTarget.get('home'))
                                awayShotsOT = int(shotsOnTarget.get('away'))
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Campos para chutes ao gol válidos!')
                            except:
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Sem campos para chutes ao gol.')
                                statisticsErrorPression = True
                                pass

                            try:
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Checando campos para escanteios...')
                                cornerKicks = [n for n in statistics1t if n['groupName'] == "TVData"][0]['statisticsItems'][0]
                                cornerKicksHome = int(cornerKicks['home'])
                                cornerKicksAway = int(cornerKicks['away'])
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Campos para escanteios válidos!')
                            except:
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Sem campos escanteios.')
                                statisticsErrorCornerKicks = True
                                pass


                            
                            # Se não houver erros na estatistica, se o jogo estiver 0x0, se estiver no primeiro tempo e o tempo de jogo(minuto) for maior ou igual a dateMessageMin
                            if not statisticsErrorPression and game['homeScore']['current'] == 0 and game['awayScore']['current'] == 0 :
                                # if (homeballPossession  targetPercentage or awayballPossession > targetPercentage) and (homeShotsOT >= 3 or awayShotsOT >= 3):
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Possível regra de pressão/gols!')
                                if max(homeballPossession, awayballPossession) > pressionDefaultPercentTarget and  max(homeShotsOT, awayShotsOT) >= pressionDefaultShotsTarget and game['id'] not in statisticsPressionListMessage and game['lastPeriod'] == generalPressionPeriod and int(dateMessageMin) >= generalPressionMinute:
                                    verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Regra de pressão aplicada! Enviando mensagem...')
                                    message = (f"ATENÇÃO/PRESSÃO => {pressionDefaultPercentTarget}\n" +
                                    messageBody +
                                    f"{game['homeTeam']['name']} odd {homeOddEx} X {homeOddExPer}% = {homeOddActPer}%\n" +
                                    f"{game['awayTeam']['name']} odd {awayOddEx} X {awayOddExPer}% = {awayOddActPer}%\n" +
                                    f"{linkMessage}")
                                    statisticsPressionListMessage.append(game['id'])
                                    for chat in telebot.getChats():
                                        messageQueue.put((chat['id'], str(message)))
                                        pass

                            if not statisticsErrorCornerKicks:
                                teamRule = ("homeTeam" if int(cornerKicksHome) > int(cornerKicksAway) else "awayTeam") if cornerKicksHome != cornerKicksAway else f"Ambos com {cornerKicksAway}"
                                teamRule = teamRule if "Ambos" in teamRule else game[teamRule]['name']
                                to20_2ndperiod = True if game['lastPeriod'] == "1st half" else True if game['lastPeriod'] == "period2" and int(dateMessageMin) <= 20 else False
                                if cornerKicksHome + cornerKicksAway >= 13 and game['id'] not in statisticsGoalListMessage and to20_2ndperiod:
                                    pass
                                    # TODO 
                                    # verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Regra de gols aplicada! Enviando mensagem...')
                                    # message = (f"TOTAL ESCANTEIOS\n" +
                                    # messageBody +
                                    # f"Time da regra: {teamRule}\n" + 
                                    # f"{game['homeTeam']['name']} Posse atual: {homeballPossession}%\n" +
                                    # f"{game['awayTeam']['name']} Posse atual: {awayballPossession}%\n" +
                                    # f"{linkMessage}")
                                    # statisticsGoalListMessage.append(game['id'])
                                    # for chat in telebot.getChats():
                                    #     messageQueue.put((chat['id'], str(message)))
                                    #     pass
                                


                            verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Possível regra de escanteio...')
                            if game['id'] not in statisticsCornerListMessage and not statisticsErrorCornerKicks and game['lastPeriod'] == cornerPeriod and int(dateMessageMin) <= cornerMinute and int(cornerKicksHome) + int(cornerKicksAway) >= cornerKicksQuantity:
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Regra de escanteio aplicada! Enviando mensagem...')
                                teamRule = ("homeTeam" if int(cornerKicksHome) > int(cornerKicksAway) else "awayTeam") if cornerKicksHome != cornerKicksAway else f"Ambos com {cornerKicksAway}"
                                teamRule = teamRule if "Ambos" in teamRule else game[teamRule]['name']
                                message = (f"ESCANTEIOS 1 TEMPO >= {cornerKicksQuantity}\n" +
                                messageBody +
                                f"Time da regra: {teamRule}\n" + 
                                f"{game['homeTeam']['name']} Posse atual: {homeballPossession}%\n" +
                                f"{game['awayTeam']['name']} Posse atual: {awayballPossession}%\n" +
                                f"{linkMessage}")
                                statisticsCornerListMessage.append(game['id'])
                                saveGame(game, 'cornerKicks', True)
                                for chat in telebot.getChats():
                                    messageQueue.put((chat['id'], str(message)))
                                    pass
                                pass
                            else:
                                verb(f'[{game["id"]}] {game["homeTeam"]["name"]} x {game["awayTeam"]["name"]} : Sem regras de escanteio para esse jogo.')


            verb(f'Fim da tarefa de busca para os jogos.')
            allgamesConsulted = True
            gamelistCompress = liveGames.copy()
            lastUpdate = datetime.strftime(datetime.now(), "%H:%M:%S")


        except:
            print(traceback.format_exc())
            pass
    else:
        return

def getNewTelegramClients():
    while True:
        try:
            telebot.getUpdates() # Lê as últimas mensagens recebidas | se /init for uma delas, inicia o bot para o usuário
        except:pass
        sleep(2.5) # Intervalo de tempo para ler as últimas mensagens

telegramThread = threading.Thread(target=getNewTelegramClients)
telegramThread.start()

allgamesConsulted = False
if not os.path.isfile('jogos.json'):
    verb("Lista de jogos não existe, criando jogos.json...")
    f = open('jogos.json', 'a+')
    f.write('[]')
    verb("Lista de jogos criada com sucesso.")
    f.close()
# def commandLine():
#     while True:
#         pass
#         x = input(">")
#         try:
#             if x == "gamelistCompress":
#                 exec(f"print(json.dumps({lastGameUpdate}, indent=4))")
#             elif x == "jogos":
#                 print(f"=== Ultima Atualização: {lastUpdate} ===")
#                 for game in lastGameUpdate:
#                     try:

#                         print(f"[{game['id']}][{game['timeInMinute']}:{game['realNamePeriod']}] {game['homeTeam']['name']} {game['homeScore']['current']} x {game['awayScore']['current']} {game['awayTeam']['name']} ")
#                     except:
#                         dateTimeStartCurrentPeriod = int(game['currentPeriodStartTimestamp']) - (60*60*3)
#                         dateTimeNow = int(str(datetime.now().timestamp()).split(".")[0])
#                         dateMessageMin =  datetime.utcfromtimestamp(dateTimeNow - dateTimeStartCurrentPeriod).strftime("%M")
#                         print(f"[{game['id']}][{dateMessageMin}:{game['realNamePeriod']}] {game['homeTeam']['name']} {game['homeScore']['current']} x {game['awayScore']['current']} {game['awayTeam']['name']} ")
#             elif x == "help":
#                 print("=== COMANDOS ===")
#                 print("jogos - Mostra a lista de jogos ao vivo com as informações da última captura.")
#                 print("nome_varivel - Mostra o valor de uma variável. Ex.: gamelistCompress, proxies etc.")
#                 print("================")
#             else:
#                 exec(f"print({x})")
#         except:
#             print("A ação não pode ser executada.")
#             pass
# relatoryThread = threading.Thread(target=consultSavedGame)
# relatoryThread.start()
messageQueue = Queue()
messagesQueueThread = threading.Thread(target=messagesQueue)
messagesQueueThread.start()
# commandLineThread = threading.Thread(target=commandLine)
# commandLineThread.start()
verb("Thread de fila de mensagens iniciada.")

proxyQueue = Queue()

while True:
    thread_list = []
    counter = 0
    if proxyQueue.empty():
        proxies = [{'http' : p, 'https' : p} for p in Proxy().proxies]
        for p in proxies:
            print(p)
            proxyQueue.put(p)
    while not proxyQueue.empty():
        counter += 1
        if counter % 30 == 0:
            print("Intervalo para aguardar respostas das outras requisições...")
            sleep(8)
        proxy = proxyQueue.get()
        if len(gamelistCompress) > 0 or allgamesConsulted:
            break
        # sleep(0.1)
        t1 = threading.Thread(target=main, args=(proxy,))
        print("Começando thread " + str(t1))
        t1.start()

    for n in [var for var in globals() if var.endswith("ListMessage")]:
        print(eval(n))
    verb("O loop será iniciado novamente em 60 segundos.")

    print("Parando...")
    sleep(60) # Intervalo para leitura de jogos
    print("Voltando...")
    gamelistCompress.clear()
    allgamesConsulted = False
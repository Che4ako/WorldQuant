import requests
import brotli
import base64
#from inspect import signature

import json
import time
import config
import logging


#Создание и настройка custom logger - https://dev-gang.ru/article/modul-logging-v-python-sugk5e4d8u/
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
f_handler = logging.FileHandler('bot_1.log')
f_handler.setLevel(logging.DEBUG)
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
f_handler.setFormatter(f_format)


#Корневой обработчик не увеличивает длину
print(len(logger.handlers))
if len(logger.handlers) == 0:
    logger.addHandler(f_handler)
elif len(logger.handlers) > 1:
    logger.handlers.clear()
    logger.addHandler(f_handler)
print(len(logger.handlers))
#logger.addHandler(f_handler)
#print(len(logger.handlers))
#logger.addHandler(f_handler)

#Настройка корневого логгера
'''logging.basicConfig(filename="bot.log", 
                    level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                   datefmt='%d-%b-%y %H:%M:%S')'''
#logger = logging.getLogger(__name__)
#logging.getLogger("requests").setLevel(logging.WARNING)

class alpha():
    def __init__(self, code, sim_settings):
        self.code = code
        self.sim_settings = sim_settings
        
    def get_code(self):
        return self.code
    
    def get_sim_settings(self):
        return self.sim_settings
    

class WebSim():
    def __init__(self, login, password, UID = None, WSSID = None):
        self.login = login
        self.password = password
        self.session = requests.Session()
        #self.session.auth = (self.login, self.password)
        
    def authorise(self):
        print("I'm here")
        logger.info("Authorization")
        
        login_x_password_encoded = base64.b64encode(bytes(self.login + ':' + self.password, 'utf-8')).decode('UTF-8')
        headers = {}
        headers['Authorization'] = 'Basic ' + login_x_password_encoded
        while True:
            r = self.session.post('https://api.worldquantvrc.com/authentication', headers=headers)
            logger.debug('Authorisation response: %s', r.text)
            try:
                res = r.json()
                if res['user'] is not None:
                    logger.info("Authorization was successful")
                    break
                else:
                    logger.critical("'Authorization response failed (wrong JSON). Reason: %s", r.json())
                    time.sleep(600)
                    continue
                break
            except:
                logger.error("Exception occurred", exc_info=True)
                logger.critical("'Authorization response failed. Reason: %s %s", r.status_code, r.reason, r.text)
                time.sleep(600)
                continue
    
    def get_stats(self, alpha_id):
        logger.debug("Try to get stats: alpha_id %s", alpha_id)
        total_attempts = 0
        while True:
            total_attempts += 1
            if total_attempts > 10:
                logger.critical("Try to get alpha stats failed. Reason: %s %s %s", r.status_code, r.reason, r.text, r.content)
                return
            try:
                r_get = self.session.get('https://api.worldquantvrc.com/alphas/'+alpha_id)
                stats_response_dict = r_get.json()
                if stats_response_dict.get('id') is None:
                    logger.info("Field id not found: %s %s", stats_response_dict, r_get.text)
                    time.sleep(5)
                    self.authorise()
                    continue
            except:
                logger.error("Exception occurred", exc_info=True)
                logger.critical("Try to get alpha stats failed. Reason: %s %s %s %s", r_get.status_code, r_get.reason, r_get.text, r_get.content)
                time.sleep(5)
                self.authorise()
                continue
            #В settings попадает чуть больше: то что у нас и так зафиксировано
            alpha = {'alpha_id': stats_response_dict['id'], 
                     'code': stats_response_dict['code'], 
                     'turnover': stats_response_dict['is']['turnover'],
                     'sharpe': stats_response_dict['is']['sharpe'],
                     'fitness': stats_response_dict['is']['fitness'],
                     'sim_settings': stats_response_dict['settings'], 
                     'pnl': stats_response_dict['is']['pnl'],
                     'bookSize': stats_response_dict['is']['bookSize'],
                     'longCount': stats_response_dict['is']['longCount'],
                     'shortCount': stats_response_dict['is']['shortCount'],
                     'returns': stats_response_dict['is']['returns'],
                     'drawdown': stats_response_dict['is']['drawdown'],
                     'margin': stats_response_dict['is']['margin'],
                     'grade': stats_response_dict['grade']
            }
            
            logger.debug("Get stats was successful: alpha_id %s", alpha_id)
            return alpha

    def simulate(self, alpha):
        logger.info("Simulate %s", alpha.code)
        code = alpha.code
        sim_settings = alpha.sim_settings
        
        headers = { 'Accept': 'application/json;version=2.0',
            #'Accept-Encoding': 'gzip, deflate, br',
            #'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            #'Connection': 'keep-alive',
            #'Content-Length': '0',
            #'Content-Type': 'application/json',
            #'Cookie': 't=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJCWHlnR1BQZHRkNDVCRjFscWVjNlVPempRNVlQTlZmTyIsImV4cCI6MTU2NDc0OTE0OH0.XVY9dI_NkZL91E5bYN64_lYaR5LelrAgBo0QtpRY3Cc; Domain=.worldquantvrc.com; HttpOnly; Path=/; Secure',
            #'Host': 'api.worldquantvrc.com',
            #'Origin': 'https://websim.worldquantvrc.com',
            #'Referer': 'https://websim.worldquantvrc.com/sign-in',
            #'TE': 'Trailers',
            #'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'
                  }
        
        data = {
                    "type":"REGULAR",
                    "settings":{"nanHandling": sim_settings["nanHandling"],
                                "instrumentType": "EQUITY",
                                "delay": sim_settings["delay"],
                                "universe": sim_settings["universe"],
                                "truncation": sim_settings["truncation"],
                                "unitHandling": "VERIFY",
                                "pasteurization": sim_settings["pasteurization"],
                                "region": sim_settings["region"],
                                "language": "FASTEXPR",
                                "decay": sim_settings["decay"],
                                "neutralization": sim_settings["neutralization"],
                                "visualization": False},
                    "regular": alpha.code
                    }
        
        while True:
            r = self.session.post('https://api.worldquantvrc.com/simulations', json = data, headers=headers)
            '''print(r.content)
            print(r.status_code)
            print(r.reason)
            print('Here')
            print(r.headers)'''
            #Здесь может возникать ошибка с превышением лимита альф
            try:
                alpha_send_id = r.headers['Location'].split('simulations/')[1]
            except:
                logger.error("Exception occurred", exc_info=True)
                logger.critical("Simulate response failed. Reason: %s %s %s %s", r.status_code, r.reason, r.text, r.content)
                time.sleep(5)
                continue
            
            send_response_dict = {}
            while send_response_dict.get('alpha') is None:
                r_get = self.session.get('https://api.worldquantvrc.com/simulations/'+alpha_send_id)
                #добавить try и учесть limit of alpa simulations
                #answer_json = r_get.json()
                time.sleep(2)
                try:
                    send_response_dict = r_get.json()
                    logger.info('Simulating: %s', send_response_dict)
                except:
                    logger.error("Exception occurred", exc_info=True)
                    logger.critical("Simulate response failed. Reason: %s %s %s", r.status_code, r.reason, r.text)
                    send_response_dict = {}
                    continue

            #print(send_response_dict)
            logger.info('Simulation was successful: alpha_id %s', send_response_dict['alpha'])
            alpha_id = send_response_dict['alpha']
            '''print(alpha_get.json())
            print()
            print()
            print()
            print(alpha_get.content)'''
            alpha = self.get_stats(alpha_id)
            #подумать про break
            return alpha
            #print('Just debug')
            
    def multisimulate(self, alphas):
        logger.info("Multisimulate")
        #Каждый i - экземпляр класса alpha
        alpha_package = []
        for i in alphas:
            code = i.code
            sim_settings = i.sim_settings
        
            data = {
                        "type":"SIMULATE",
                        "settings":{"nanHandling": sim_settings["nanHandling"],
                                    "instrumentType": "EQUITY",
                                    "delay": sim_settings["delay"],
                                    "universe": sim_settings["universe"],
                                    "truncation": sim_settings["truncation"],
                                    "unitHandling": "VERIFY",
                                    "pasteurization": sim_settings["pasteurization"],
                                    "region": sim_settings["region"],
                                    "language": "FASTEXPR",
                                    "decay": sim_settings["decay"],
                                    "neutralization": sim_settings["neutralization"],
                                    "visualization": False},
                                    "code": code
                        }
            alpha_package.append(data)
        
        while True:
            r = self.session.post('https://api.worldquantvrc.com/simulations', json = alpha_package)
            print(r.content)
            print(r.status_code)
            print(r.reason)
            print('Here')
            print(r.headers)
            #break
            
            parent_alpha_send_id = r.headers['Location'].split('simulations/')[1]
            send_response_dict = {}
            while send_response_dict.get('id') is None:
                r_get = self.session.get('https://api.worldquantvrc.com/simulations/'+parent_alpha_send_id)
                #добавить try и учесть limit of alpa simulations
                answer_json = r_get.json()
                logger.info('Multisimulating: %s', answer_json)
                time.sleep(2)
                try:
                    send_response_dict = r_get.json()
                except:
                    logger.error("Exception occurred", exc_info=True)
                    logger.critical("Simulate response failed. Reason: %s %s %s", r.status_code, r.reason, r.text)
                    send_response_dict = {}
                    continue
            logger.info('Multisimulation was successful: alpha_ids %s', send_response_dict['children'])
            alpha_send_ids = send_response_dict['children']
            print(alpha_send_ids)
            alpha_ids = []
            for i in alpha_send_ids:
                r_get = self.session.get('https://api.worldquantvrc.com/simulations/'+i)
                alpha_ids.append(r_get.json()['alpha'])
            print(alpha_ids)
            result = []
            for j in alpha_ids:
                result.append(self.get_stats(j))
            print(result)
            return(result)
            break
            
    def correlation(self, corr_type, alpha_id):
        #Добавить logging
        if corr_type == 'self':
            logger.info("Try to get self correlation")
            #Проблемы со связью -> временные ошибки на уровне self.session.get() вполне возможны
            while True:
                try:
                    r = self.session.get('https://api.worldquantvrc.com/alphas/'+alpha_id+'/correlations/self')
                    time.sleep(2)
                    r = self.session.get('https://api.worldquantvrc.com/alphas/'+alpha_id+'/correlations/self')
                    response_json = r.json()
                    if response_json.get('records') is None:
                        continue
                    correlations = {}
                    for i in response_json['records']:
                        correlations[i[0]] = i[5]
                    #print(correlations) - оставим возможность вернуть словарь на будущее
                    maximum = max([correlations[i] for i in correlations])
                    logger.info("Prod correlation received successfully")
                    return maximum
                except:
                    logger.critical("Try to get self_correlation failed. Reason: %s %s %s", r.status_code, r.reason, r.text)
                    logger.error("Exception occurred", exc_info=True)
                    continue
        elif corr_type == 'prod':
            logger.info("Try to get prod correlation")
            #Проблемы со связью -> временные ошибки на уровне self.session.get() вполне возможны
            while True:
                try:
                    r = self.session.get('https://api.worldquantvrc.com/alphas/'+alpha_id+'/correlations/prod')
                    time.sleep(2)
                    r = self.session.get('https://api.worldquantvrc.com/alphas/'+alpha_id+'/correlations/prod')
                    response_json = r.json()
                    if response_json.get('records') is None:
                        continue
                    correlations = [i[1] for i in response_json['records'] if i[2] is not None and i[2] > 0]
                    maximum = max(correlations) 
                    logger.info("Prod correlation received successfully")
                    return maximum
                except:
                    logger.critical("Try to get prod correlation failed. Reason: %s %s %s", r.status_code, r.reason, r.text)
                    logger.error("Exception occurred", exc_info=True)
                    continue
        else:
            return 'Wrong corr_type'
        
    def simulate_boost(self, alphas):
        logger.info("Simulate_boost")
        headers = {'Accept': 'application/json;version=2.0'}
        
        alpha_send_ids = []
        #post-запросы надо посылать по каждой альфе до успешного ответа
        for i in alphas:
            code = i.code
            sim_settings = i.sim_settings
            data = {
                    "type":"REGULAR",
                    "settings":{"nanHandling": sim_settings["nanHandling"],
                                "instrumentType": "EQUITY",
                                "delay": sim_settings["delay"],
                                "universe": sim_settings["universe"],
                                "truncation": sim_settings["truncation"],
                                "unitHandling": "VERIFY",
                                "pasteurization": sim_settings["pasteurization"],
                                "region": sim_settings["region"],
                                "language": "FASTEXPR",
                                "decay": sim_settings["decay"],
                                "neutralization": sim_settings["neutralization"],
                                "visualization": False},
                    "regular": i.code
                    }
            logger.info("Simulate %s", i.code)
           
            total_attempts = 0
            while True:
                #print('!')
                total_attempts += 1
                try:
                    r = self.session.post('https://api.worldquantvrc.com/simulations', json=data, headers=headers)
                    '''print(r.content)
                    print(r.status_code)
                    print(r.reason)
                    print('Here')
                    print(r.headers)'''
                    #Здесь может возникать ошибка с превышением лимита альф 
                    #возможно должно быть 'Location',но с маленькой тоже работает
                    alpha_send_id = r.headers['Location'].split('simulations/')[1]
                    alpha_send_ids.append(alpha_send_id)
                    break
                #Надо научиться отлавдивать переаутентификацию через status_code
                except:
                    logger.error("Exception occurred", exc_info=True)
                    logger.critical("Simulate response failed. Reason: %s %s %s %s", r.status_code, r.reason, r.text, r.content)
                    if total_attempts > 15:
                        #для этой альфы результат возвращён не будет
                        break
                    if total_attempts % 5 != 0:
                        time.sleep(5)
                        continue
                    else:
                        self.authorise()
                        continue
        #закончился цикл запросов post на симуляцию
        logger.info("Simulate successfully started.  Alpha_send_ids: %s",  alpha_send_ids)
        
        #get-запросы надо посылать пачками, т.е. for внутри while, а не наоборот
        alpha_ids = []
        
        total_attempts = 0
        not_get_ids = alpha_send_ids
        while not_get_ids != []:
            time.sleep(10)
            current_ids = not_get_ids
            #теперь мы не знаем, какие получим, а какие нет
            not_get_ids = []
            total_attempts += 1            
            try:
                for alpha_send_id in current_ids:
                    r_get = self.session.get('https://api.worldquantvrc.com/simulations/'+alpha_send_id)
                    if r_get.json().get('alpha') is not None:
                        alpha_ids.append(r_get.json()['alpha'])
                    else:
                        not_get_ids.append(alpha_send_id)
                        logger.info('Simulating: %s %s', alpha_send_id, r_get.json())
                logger.info("Current not execute alpha_send_ids: %s", not_get_ids)
            except:
                logger.error("Exception occurred", exc_info=True)
                logger.critical("Simulate response failed. Reason: %s %s %s %s", r_get.status_code, r_get.reason, r_get.text, r_get.content)
                if total_attempts > 30:
                    #для этих альф результатом будет ничего
                    break
                if total_attempts % 5 != 0:
                    continue
                else:
                    self.authorise()
                    continue
         
        #закончился цикл запросов get на получение alpha_id по итогу симуляции
        if alpha_ids == []:
            return []
        resulted_alphas = []
        for alpha_id in alpha_ids:
            alpha = self.get_stats(alpha_id)
            if alpha is None:
                continue
            else:
                resulted_alphas.append(alpha)
                
        logger.info("Simulate_boost was successful")
        return resulted_alphas
    
    def multisimulate_boost(self, lst_of_alphas):
        logger.info("Multisimulate_boost")
        headers = {'Accept': 'application/json;version=2.0'}
        #Пакуем большой список альф (<= 100) в упаковки по 10 штук
        lst_of_package = []
        alpha_package = []
        for i in range(len(lst_of_alphas)):
            alpha_package.append(lst_of_alphas[i])
            if (i+1) % 10 == 0:
                lst_of_package.append(alpha_package)
                alpha_package = []
        if alpha_package != []:
            #в последнюю упаковку положили что осталось <10 альф
            lst_of_package.append(alpha_package)
        #упаковали
        
        #блок отправки post-запросов
        parent_alpha_send_ids = []
        for alpha_package in lst_of_package:
            alpha_send_package = []
            for i in alpha_package:
                code = i.code
                sim_settings = i.sim_settings

                data = {
                            "type":"REGULAR",
                            "settings":{"nanHandling": sim_settings["nanHandling"],
                                        "instrumentType": "EQUITY",
                                        "delay": sim_settings["delay"],
                                        "universe": sim_settings["universe"],
                                        "truncation": sim_settings["truncation"],
                                        "unitHandling": "VERIFY",
                                        "pasteurization": sim_settings["pasteurization"],
                                        "region": sim_settings["region"],
                                        "language": "FASTEXPR",
                                        "decay": sim_settings["decay"],
                                        "neutralization": sim_settings["neutralization"],
                                        "visualization": False},
                                        "regular": code
                            }
                alpha_send_package.append(data)
            #по каждой мультисимуляции дожидаемся успешной отправки
            total_attempts = 0
            while True:
                total_attempts += 1
                try:
                    r = self.session.post('https://api.worldquantvrc.com/simulations', json = alpha_send_package, headers=headers)
                    logger.info("Simulate request was sent. Alpha_send_package: %s", alpha_send_package)
                    '''print(r.content)
                    print(r.status_code)
                    print(r.reason)
                    print('Here')
                    print(r.headers)'''
                    parent_alpha_send_id = r.headers['location'].split('simulations/')[1]
                    parent_alpha_send_ids.append(parent_alpha_send_id)
                    break
                except:
                    logger.error("Exception occurred", exc_info=True)
                    logger.critical("Simulate response failed. Reason: %s %s %s %s", r.status_code, r.reason, r.text, r.content)
                    if total_attempts > 15:
                        #для этой десятки результат возвращён не будет
                        break
                    if total_attempts % 5 != 0:
                        continue
                    else:
                        self.authorise()
                        continue
        logger.info("Simulate successfully started.  Parent_alpha_send_ids: %s",  parent_alpha_send_ids)
        #закончили блок post-запросов
        #получили parent_alpha_send_ids - 10 id симуляций
        print('!!!')
        alpha_send_ids = []
        
        total_attempts = 0
        not_get_ids = parent_alpha_send_ids
        while not_get_ids != []:
            current_ids = not_get_ids
            #теперь мы не знаем, какие получим, а какие нет
            not_get_ids = []
            #!Поменял время сна на 30 секунд!
            time.sleep(30)
            total_attempts += 1
            try:
                for package_send_id in current_ids:
                    r_get = self.session.get('https://api.worldquantvrc.com/simulations/' + package_send_id)
                    logger.info("Request to get children was sent. Package_send_id %s", package_send_id)
                    if r_get.json().get('id') is not None:
                        alpha_send_ids.extend(r_get.json()['children'])
                    else:
                        not_get_ids.append(package_send_id)
                        logger.info('Simulating: %s %s', package_send_id, r_get.json())
                logger.info("Current not execute parent_alpha_send_ids: %s",  not_get_ids)
            
            except:
                logger.error("Exception occurred", exc_info=True)
                logger.critical("Simulate response failed. Reason: %s %s %s %s", r.status_code, r.reason, r.text, r.content)
                if total_attempts > 30:
                    #для всех этих альф результатом будет ничего
                    break
                if total_attempts % 5 != 0:
                    continue
                else:
                    self.authorise()
                    continue
        logger.info('All alpha_send_id has got: %s', alpha_send_ids)
        #получили alpha_send_ids

        alpha_ids = []
        
        total_attempts = 0
        not_get_ids = alpha_send_ids
        while not_get_ids != []:
            current_ids = not_get_ids
            not_get_ids = []
            time.sleep(2)
            total_attempts += 1
            try:
                for alpha_send_id in current_ids:
                    r_get = self.session.get('https://api.worldquantvrc.com/simulations/'+alpha_send_id)
                    if r_get.json().get('alpha') is not None:
                        alpha_ids.append(r_get.json()['alpha'])
                    else:
                        logger.info('Try to get alpha_id. Alpha_send_id: %s %s %s %s %s', alpha_send_id, r_get.json(), r_get.status_code, r_get.reason, r_get.text)
                        not_get_ids.append(alpha_send_id)
                logger.info("Current not execute alpha_send_ids: %s",  not_get_ids)
            except:
                    logger.error("Exception occurred", exc_info=True)
                    logger.critical("Try to get alpha_ids failed. Reason: %s %s %s %s", r.status_code, r.reason, r.text, r.content)
                    if total_attempts > 30:
                        #для этих альф результатом будет ничего
                        break
                    if total_attempts % 5 != 0:
                        continue
                    else:
                        self.authorise()
                        continue
            #получили alpha_ids
            
        if alpha_ids == []:
            return []
        resulted_alphas = []
        #Кажется, что пока что достаточно параллелить только симуляцию (т.е. post-запросы)
        for alpha_id in alpha_ids:
            alpha = self.get_stats(alpha_id)
            if alpha is None:
                 continue
            else:
                resulted_alphas.append(alpha)
                
        #подумать про break
        logger.info("Multisimulate_boost was successful")
        return resulted_alphas
            
                 
#W = WebSim('ruterminals@gmail.com', '*****')
#W.authorise()
            
                
        
                
                


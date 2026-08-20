import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import pooling
import json
import time
import threading
import traceback
import warnings
import config

# Ignorar o aviso do Paho MQTT sobre a versão da API
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Configurações do MySQL Pool
dbconfig = {
    "host": config.MYSQL_HOST,
    "port": config.MYSQL_PORT,
    "user": config.MYSQL_USER,
    "password": config.MYSQL_PASSWORD,
    "database": config.MYSQL_DATABASE,
    "autocommit": True
}

# A variável global para o Pool
connection_pool = None

def get_db_connection():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = pooling.MySQLConnectionPool(pool_name="pool_jogador", pool_size=5, **dbconfig)
        except Exception as e:
            print(f"[!] Erro ao inicializar o MySQL Pool: {e}")
            return None
    
    try:
        return connection_pool.get_connection()
    except Exception as e:
        print(f"[!] Erro ao obter ligação do MySQL: {e}")
        return None

# Clientes MQTT
client_local = mqtt.Client(client_id=f"jogador_local_{config.GROUP_NUMBER}")
client_cloud = mqtt.Client(client_id=f"jogador_cloud_{config.GROUP_NUMBER}")

# Garantir que não tentamos marcar a mesma sala várias vezes simultaneamente
pontuacao_lock = threading.Lock()
locked_rooms = set()

# Estado do Atuador (AC)
is_ac_on = False

# Estado do Alerta de Som (portas fechadas por ruído)
is_sound_alert_on = False

def get_corridors_for_room(cursor, room_id):
    """Obtém todos os corredores que SAEM e ENTRAM numa sala (unidirecionais).
    Retorna lista de tuplos (RoomOrigin, RoomDestiny) para usar nos comandos CloseDoor/OpenDoor."""
    sim_query = "(SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1)"
    
    corridors = []
    
    # Corredores que SAEM da sala (RoomA = sala → RoomB)
    cursor.execute(f"""
        SELECT RoomA, RoomB FROM corredores_mapa 
        WHERE idSimulacao = {sim_query} AND RoomA = %s
    """, (room_id,))
    corridors.extend(cursor.fetchall())
    
    # Corredores que ENTRAM na sala (RoomA → RoomB = sala)
    cursor.execute(f"""
        SELECT RoomA, RoomB FROM corredores_mapa 
        WHERE idSimulacao = {sim_query} AND RoomB = %s
    """, (room_id,))
    corridors.extend(cursor.fetchall())
    
    return corridors


def unlock_room_delayed(player_id, room_id, delay=6.0):
    """Espera 'delay' segundos e reabre as portas da sala."""
    time.sleep(delay)
    print(f"[BOT] A reabrir portas da Sala {room_id} apos {delay}s...")
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        with conn.cursor() as cursor:
            corridors = get_corridors_for_room(cursor, room_id)
            
            for origin, dest in corridors:
                msg = f"{{Type: OpenDoor, Player:{player_id}, RoomOrigin: {origin}, RoomDestiny: {dest}}}"
                client_cloud.publish(config.TOPIC_ACTUATORS, msg)
                print(f"[MQTT Cloud] Abrir: {msg}")
    except Exception as e:
        print(f"[ERRO] Falha ao reabrir portas: {e}")
    finally:
        locked_rooms.discard(room_id)
        if 'conn' in locals() and conn is not None and conn.is_connected():
            conn.close()

def check_and_score():
    """Verifica se há alguma sala equilibrada e executa Lock & Score."""
    with pontuacao_lock:
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            with conn.cursor() as cursor:
                # 1. Procurar salas equilibradas e elegíveis
                query_salas = """
                    SELECT idSala 
                    FROM ocupacaolabirinto 
                    WHERE idSimulacao = (SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1)
                      AND nrMarsamisOdd = nrMarsamisEven 
                      AND nrMarsamisOdd > 0 
                      AND tentativasPontuacao < 3
                """
                cursor.execute(query_salas)
                salas = cursor.fetchall()
                
                for sala in salas:
                    room_id = sala[0]
                    
                    if room_id in locked_rooms:
                        continue
                        
                    locked_rooms.add(room_id)
                    print(f"[BOT] Equilibrio detetado na Sala {room_id}! A iniciar Lock & Score...")
                    
                    # 2. Obter TODOS os corredores ligados a esta sala (unidirecionais)
                    corridors = get_corridors_for_room(cursor, room_id)
                    
                    # Passo A: Trancar TODAS as portas (saídas E entradas)
                    for origin, dest in corridors:
                        msg_close = f"{{Type: CloseDoor, Player:{config.GROUP_NUMBER_INT}, RoomOrigin: {origin}, RoomDestiny: {dest}}}"
                        client_cloud.publish(config.TOPIC_ACTUATORS, msg_close)
                        print(f"[MQTT Cloud] Trancar: {msg_close}")
                    
                    # Dar 1 segundo para as portas fechar fisicamente no simulador
                    time.sleep(1.0)
                    
                    # Passo B: Pontuar
                    msg_score = f"{{Type: Score, Player:{config.GROUP_NUMBER_INT}, Room: {room_id}}}"
                    client_cloud.publish(config.TOPIC_ACTUATORS, msg_score)
                    print(f"[MQTT Cloud] SCORE! {msg_score}")
                    
                    # Atualizar base de dados
                    cursor.execute("UPDATE ocupacaolabirinto SET tentativasPontuacao = tentativasPontuacao + 1 WHERE idSimulacao = (SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1) AND idSala = %s", (room_id,))
                    
                    # Passo C: Reabrir (em background passado 10s)
                    threading.Thread(target=unlock_room_delayed, args=(config.GROUP_NUMBER_INT, room_id, 10.0)).start()
                    
        except Exception as e:
            print(f"[ERRO] Falha no check_and_score: {e}")
            traceback.print_exc()
        finally:
            if 'conn' in locals() and conn is not None and conn.is_connected():
                conn.close()

def check_temperature_alert():
    """Consulta a tabela alertas e liga/desliga o AC."""
    global is_ac_on
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        with conn.cursor() as cursor:
            # Ir buscar o estado do alerta de temperatura para a simulação ativa
            query = """
                SELECT Temperatura 
                FROM alertas 
                WHERE idSimulacao = (SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1)
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                temp_alert = result[0] # 1 se estiver quente, 0 se estiver normal
                
                print(f"[BOT] Recebida nova temperatura! Estado Alerta BD: {temp_alert} | AC atual: {'LIGADO' if is_ac_on else 'DESLIGADO'}")
                
                if temp_alert == 1 and not is_ac_on:
                    # Acabou de aquecer: Ligar o AC
                    msg_ac = f"{{Type: AcOn, Player:{config.GROUP_NUMBER_INT}}}"
                    client_cloud.publish(config.TOPIC_ACTUATORS, msg_ac)
                    print(f"==================================================")
                    print(f"[MQTT Cloud] 🌡️ ALERTA TEMP! A ligar o ar condicionado")
                    print(f"[MQTT Cloud] -> Mensagem enviada: {msg_ac}")
                    print(f"==================================================")
                    is_ac_on = True
                    
                elif temp_alert == 0 and is_ac_on:
                    # Voltou ao normal: Desligar o AC
                    msg_ac = f"{{Type: AcOff, Player:{config.GROUP_NUMBER_INT}}}"
                    client_cloud.publish(config.TOPIC_ACTUATORS, msg_ac)
                    print(f"==================================================")
                    print(f"[MQTT Cloud] ❄️ TEMP NORMALIZADA! A desligar o AC")
                    print(f"[MQTT Cloud] -> Mensagem enviada: {msg_ac}")
                    print(f"==================================================")
                    is_ac_on = False

    except Exception as e:
        print(f"[ERRO] Falha ao verificar alerta de temperatura: {e}")
    finally:
        if 'conn' in locals() and conn is not None and conn.is_connected():
            conn.close()

def check_sound_alert():
    """Consulta a tabela alertas e fecha/abre portas conforme o som."""
    global is_sound_alert_on
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        with conn.cursor() as cursor:
            query = """
                SELECT Som 
                FROM alertas 
                WHERE idSimulacao = (SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1)
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                sound_alert = result[0]
                
                print(f"[BOT] Recebido novo som! Estado Alerta BD: {sound_alert} | Portas por ruido: {'FECHADAS' if is_sound_alert_on else 'ABERTAS'}")
                
                if sound_alert == 1 and not is_sound_alert_on:
                    # Som alto: Fechar TODAS as portas do labirinto
                    msg_close = f"{{Type: CloseAllDoor, Player: {config.GROUP_NUMBER_INT}}}"
                    client_cloud.publish(config.TOPIC_ACTUATORS, msg_close)
                    print(f"==================================================")
                    print(f"[MQTT Cloud] 🔊 ALERTA SOM! A fechar todas as portas")
                    print(f"[MQTT Cloud] -> Mensagem enviada: {msg_close}")
                    print(f"==================================================")
                    is_sound_alert_on = True
                    
                elif sound_alert == 0 and is_sound_alert_on:
                    # Som normalizado: Reabrir TODAS as portas
                    msg_open = f"{{Type: OpenAllDoor, Player:{config.GROUP_NUMBER_INT}}}"
                    client_cloud.publish(config.TOPIC_ACTUATORS, msg_open)
                    print(f"==================================================")
                    print(f"[MQTT Cloud] 🔇 SOM NORMALIZADO! A reabrir todas as portas")
                    print(f"[MQTT Cloud] -> Mensagem enviada: {msg_open}")
                    print(f"==================================================")
                    is_sound_alert_on = False

    except Exception as e:
        print(f"[ERRO] Falha ao verificar alerta de som: {e}")
    finally:
        if 'conn' in locals() and conn is not None and conn.is_connected():
            conn.close()

def on_local_message(client, userdata, msg):
    """Callback quando uma mensagem é processada pelo Script 1."""
    # Dar uma fraçao de segundo para a SP inserir e o trigger correr
    time.sleep(0.1)
    
    if msg.topic == config.TOPIC_OUT_MOV:
        check_and_score()
    elif msg.topic == config.TOPIC_OUT_TEMP:
        check_temperature_alert()
    elif msg.topic == config.TOPIC_OUT_SOUND:
        check_sound_alert()

def main():
    print(f"=== INICIANDO SCRIPT 3 (JOGADOR BOT) - GRUPO {config.GROUP_NUMBER} ===")
    
    # Configurar e Ligar ao MQTT Cloud (para Atuadores)
    print(f"A ligar ao Broker Cloud (Atuadores): {config.MQTT_BROKER_PUBLIC}...")
    client_cloud.connect(config.MQTT_BROKER_PUBLIC, config.MQTT_PORT_PUBLIC, 60)
    client_cloud.loop_start()
    
    # Configurar e Ligar ao MQTT Local (para escutar Movimentos validos)
    print(f"A ligar ao Broker Local (Escuta de Movimentos): {config.MQTT_BROKER_LOCAL}...")
    client_local.on_message = on_local_message
    client_local.connect(config.MQTT_BROKER_LOCAL, config.MQTT_PORT_LOCAL, 60)
    
    # Subscrever aos tópicos validados
    client_local.subscribe(config.TOPIC_OUT_MOV)
    client_local.subscribe(config.TOPIC_OUT_TEMP)
    client_local.subscribe(config.TOPIC_OUT_SOUND)
    print(f"Subscrito em {config.TOPIC_OUT_MOV}, {config.TOPIC_OUT_TEMP} e {config.TOPIC_OUT_SOUND}. A aguardar eventos...")
    
    try:
        client_local.loop_forever()
    except KeyboardInterrupt:
        print("Script terminado pelo utilizador.")
    finally:
        client_local.loop_stop()
        client_cloud.loop_stop()
        client_local.disconnect()
        client_cloud.disconnect()

if __name__ == "__main__":
    main()

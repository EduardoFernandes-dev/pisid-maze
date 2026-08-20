import json
import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error as MySQLError

from config import (
    MQTT_BROKER_LOCAL, MQTT_PORT_LOCAL,
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    TOPIC_OUT_MOV, TOPIC_OUT_TEMP, TOPIC_OUT_SOUND,
)

# --- Estatísticas Globais ---
stats = {
    "received": 0,
    "inserted": 0,
    "errors": 0,
}

# --- Ligação ao MySQL ---
def connect_mysql():
    """Tenta ligar ao MySQL local. Retorna a conexão ou None."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            autocommit=True,
        )
        if conn.is_connected():
            print(f"[✓ MySQL] Ligado a {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}\n")
            return conn
    except MySQLError as e:
        print(f"[!] Erro ao ligar ao MySQL: {e}\n")
    return None

def ensure_connection(conn):
    """Verifica se a conexão ao MySQL está viva. Reconecta se necessário."""
    if conn is None or not conn.is_connected():
        print("[MySQL] A reconectar...")
        return connect_mysql()
    return conn

# --- Inserção via Stored Procedures ---
def insert_movement(cursor, payload):
    hour = payload.get("Hour", None)
    room_origin = int(payload.get("RoomOrigin", 0))
    room_destiny = int(payload.get("RoomDestiny", 0))
    marsami = int(payload.get("Marsami", 0))
    status = int(payload.get("Status", 0))
    cursor.callproc("sp_inserir_passagem", [hour, room_origin, room_destiny, marsami, status])

def insert_temperature(cursor, payload):
    hour = payload.get("Hour", None)
    try:
        temp_val = float(payload.get("Temperature", 0))
        temperature = str(round(temp_val, 6))
    except ValueError:
        temperature = str(payload.get("Temperature", ""))[:50]
    cursor.callproc("sp_inserir_temperatura", [hour, temperature])

def insert_sound(cursor, payload):
    hour = payload.get("Hour", None)
    try:
        sound_val = float(payload.get("Sound", 0))
        sound = str(round(sound_val, 6))
    except ValueError:
        sound = str(payload.get("Sound", ""))[:50]
    cursor.callproc("sp_inserir_som", [hour, sound])

# --- Callbacks do MQTT ---
mysql_conn = None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[✓ MQTT] Conectado ao Broker Local com sucesso (Código: {rc})")
        # Subscrever aos 3 tópicos (com QoS 2 para garantir entrega sem duplicados)
        client.subscribe([(TOPIC_OUT_MOV, 2), (TOPIC_OUT_TEMP, 2), (TOPIC_OUT_SOUND, 2)])
        print(f"[*] À escuta dos tópicos:")
        print(f"   ↳ {TOPIC_OUT_MOV}")
        print(f"   ↳ {TOPIC_OUT_TEMP}")
        print(f"   ↳ {TOPIC_OUT_SOUND}\n")
    else:
        print(f"[!] Falha na conexão MQTT. Código de erro: {rc}")

def on_message(client, userdata, msg):
    global mysql_conn, last_message_time
    import time
    last_message_time = time.time()
    
    try:
        raw_payload = msg.payload.decode("utf-8")
        data = json.loads(raw_payload)
        
        # A mensagem chega como um JSON simples, sem wrappers.
        payload = data
        
        stats["received"] += 1
        tag = "MOVIMENTOS" if "mov" in msg.topic else "TEMPERATURA" if "temp" in msg.topic else "RUÍDO"

        # --- MONITOR VISUAL (Print no ecrã como o colega) ---
        print(f"[NOVA MENSAGEM - {tag}]")
        print(f"   ↳ Tópico de Origem: {msg.topic}")
        print(f"   ↳ Dados Recebidos:  {payload}")

        # --- INSERÇÃO NO MYSQL ---
        mysql_conn = ensure_connection(mysql_conn)

        if mysql_conn is None:
            print(f"   ↳ [!] ERRO: Sem ligação ao MySQL. Dados NÃO inseridos.\n")
            stats["errors"] += 1
            return

        try:
            cursor = mysql_conn.cursor()

            if "mov" in msg.topic:
                insert_movement(cursor, payload)
            elif "temp" in msg.topic:
                insert_temperature(cursor, payload)
            elif "sound" in msg.topic:
                insert_sound(cursor, payload)

            cursor.close()
            stats["inserted"] += 1
            print(f"   ↳ [✓] Inserido no MySQL (Stored Procedure) com sucesso.\n")

        except MySQLError as e:
            stats["errors"] += 1
            print(f"   ↳ [!] Erro MySQL ao inserir: {e}\n")
            # Forçar reconexão na próxima mensagem
            try:
                mysql_conn.close()
            except:
                pass
            mysql_conn = None

        # Resumo estatístico
        if stats["received"] > 0 and stats["received"] % 20 == 0:
            print(f"{'=' * 60}")
            print(f"  ESTATÍSTICAS SCRIPT 3:")
            print(f"  Recebidas: {stats['received']} | "
                  f"Inseridas: {stats['inserted']} | "
                  f"Erros MySQL: {stats['errors']}")
            print(f"{'=' * 60}\n")

    except json.JSONDecodeError:
        print(f"[!] Erro: A mensagem recebida não é um JSON válido: {raw_payload}\n")
    except Exception as e:
        print(f"[!] Erro inesperado a processar a mensagem: {e}\n")


# --- Arranque do Sistema ---
if __name__ == "__main__":
    print("=" * 60)
    print("  SCRIPT 3, PC2 (Monitor MQTT + MySQL Stored Procedures)")
    print(f"  Broker MQTT:  {MQTT_BROKER_LOCAL}:{MQTT_PORT_LOCAL}")
    print(f"  MySQL:        {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    print("=" * 60)
    print()

    mysql_conn = connect_mysql()
    if mysql_conn is None:
        print("[!] AVISO: MySQL não disponível. O script vai tentar reconectar quando receber mensagens.")

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        print(f"A conectar ao broker MQTT em {MQTT_BROKER_LOCAL}:{MQTT_PORT_LOCAL}...")
        mqtt_client.connect(MQTT_BROKER_LOCAL, MQTT_PORT_LOCAL, 60)
        
        import time
        global last_message_time
        last_message_time = time.time()
        
        mqtt_client.loop_start()
        
        while True:
            time.sleep(1)
            # Apenas verifica o timeout se já tiver começado a receber mensagens (para dar tempo ao Mazerun de arrancar)
            if stats["received"] > 0:
                if time.time() - last_message_time > 10:
                    print("\n" + "="*60)
                    print("[!] Nenhum dado recebido há mais de 10 segundos!")
                    print("[*] A assumir que a simulação do Mazerun terminou.")
                    
                    mysql_conn = ensure_connection(mysql_conn)
                    if mysql_conn and mysql_conn.is_connected():
                        try:
                            cursor = mysql_conn.cursor()
                            # Muda todas as simulações ativas (0) para terminadas (1)
                            cursor.execute("UPDATE simulacao SET IsActive = 1 WHERE IsActive = 0")
                            cursor.close()
                            print("[✓] Simulação marcada como TERMINADA (IsActive = 1) na base de dados.")
                        except Exception as e:
                            print(f"[!] Erro ao atualizar o estado da simulação: {e}")
                    
                    print("="*60 + "\n")
                    
                    # Faz reset ao contador para ficar à espera de uma nova simulação sem entrar em loop
                    stats["received"] = 0

    except KeyboardInterrupt:
        print("\nScript interrompido pelo utilizador. A desligar de forma segura...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
        print("Desconectado com sucesso.")
    except Exception as e:
        print(f"[!] Erro fatal: {e}")
        mqtt_client.loop_stop()
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()

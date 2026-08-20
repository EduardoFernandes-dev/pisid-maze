import paho.mqtt.client as mqtt
import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

BROKER = "broker.mqtt-dashboard.com"
TOPIC = "pisid_mazeact"

def on_connect(client, userdata, flags, rc):
    print(f"[OK] Ligado ao broker. A escutar TUDO em '{TOPIC}'...\n")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        player = data.get("Player", "?")
        msg_type = data.get("Type", "?")
        
        # Destacar as nossas mensagens (Player 16)
        tag = " <<< NOS!" if player == 16 else ""
        
        if msg_type == "Score":
            print(f"[SCORE]     Player={player}, Room={data.get('Room', '?')}{tag}")
        elif msg_type == "CloseDoor":
            print(f"[CLOSE]     Player={player}, {data.get('RoomOrigin','?')}->{data.get('RoomDestiny','?')}{tag}")
        elif msg_type == "OpenDoor":
            print(f"[OPEN]      Player={player}, {data.get('RoomOrigin','?')}->{data.get('RoomDestiny','?')}{tag}")
        elif msg_type == "CloseAllDoor":
            print(f"[CLOSEALL]  Player={player}{tag}")
        elif msg_type == "OpenAllDoor":
            print(f"[OPENALL]   Player={player}{tag}")
        else:
            print(f"[{msg_type}] Player={player} | {data}{tag}")
    except:
        print(f"[RAW] {msg.payload.decode()}")

client = mqtt.Client(client_id="espia_mazeact_16")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883, 60)

print(f"A ligar a {BROKER} no topico '{TOPIC}'...")
client.loop_forever()

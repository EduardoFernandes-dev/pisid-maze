# =============================================================================
# CONFIGURAÇÃO CENTRALIZADA DO PROJETO PISID - Grupo 16
# =============================================================================
# Este ficheiro contém todas as constantes partilhadas pelos scripts.
# PC1 usa: MQTT público (entrada) + MongoDB + MQTT local (saída)
# PC2 usa: MQTT local do PC1 (entrada) + MySQL local
# =============================================================================

# --- Identificação do Grupo ---
GROUP_NUMBER = "16"
GROUP_NUMBER_INT = 16

# --- MQTT: Broker Público (Mazerun → Script 1) ---
MQTT_BROKER_PUBLIC = "broker.mqtt-dashboard.com"
MQTT_PORT_PUBLIC = 1883

# --- MQTT: Broker Local no PC1 (Script 1 → Script 2) ---
# No PC1 (onde corre o Mosquitto Docker) usa-se "localhost"
# No PC2, mudar para o IP do PC1 na rede local
MQTT_BROKER_LOCAL = "localhost" #"192.168.1.4"  # IP do PC1 na rede local
MQTT_PORT_LOCAL = 1883

# --- MongoDB (PC1) ---
MONGO_URI = "mongodb://mongo1:27020,mongo2:27018,mongo3:27019/?replicaSet=rs0"
MONGO_DB_NAME = "pisid_maze"

# --- MySQL (PC2) ---
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "aluno"
MYSQL_PASSWORD = "aluno"
MYSQL_DATABASE = "pisid_maze"

# --- MySQL Nuvem (read-only, para consulta de SetupMaze/Corridor) ---
MYSQL_CLOUD_HOST = "194.210.86.10"
MYSQL_CLOUD_USER = "aluno"
MYSQL_CLOUD_PASSWORD = "aluno"
MYSQL_CLOUD_DATABASE = "maze"

# --- Tópicos MQTT de Entrada (Mazerun → Script 1) ---
TOPIC_IN_MOV = f"pisid_mazemov_{GROUP_NUMBER}"
TOPIC_IN_TEMP = f"pisid_mazetemp_{GROUP_NUMBER}"
TOPIC_IN_SOUND = f"pisid_mazesound_{GROUP_NUMBER}"

# --- Tópicos MQTT de Saída (Script 1 → Script 2 via Broker LOCAL) ---
TOPIC_OUT_MOV = f"pisid_maze_out_mov_{GROUP_NUMBER}"
TOPIC_OUT_TEMP = f"pisid_maze_out_temp_{GROUP_NUMBER}"
TOPIC_OUT_SOUND = f"pisid_maze_out_sound_{GROUP_NUMBER}"

# --- Tópicos MQTT Atuadores (Script 3 → Nuvem) ---
TOPIC_ACTUATORS = "pisid_mazeact"

# --- Validador ---
ZSCORE_THRESHOLD = 3.0
SLIDING_WINDOW_SIZE = 5
FUTURE_TOLERANCE_SECONDS = 5

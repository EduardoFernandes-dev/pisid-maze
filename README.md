# PISID Maze

Sistema distribuído de simulação de um labirinto em tempo real (projeto PISID,
ISCTE-IUL). Os sensores do labirinto são publicados por MQTT e passam por uma
camada de dados com MySQL (relacional) e MongoDB (replica set), com validação,
monitorização e migração de dados entre as duas bases.

## Arquitetura e fluxo de dados

1. **Mazerun** simula o labirinto e publica dados de sensores (movimento,
   temperatura, som) num broker MQTT público.
2. **script_1_mongodb.py** subscreve o broker público, valida os dados e guarda
   no MongoDB (replica set de 3 nós).
3. **script_2_mongo_to_mqtt.py** lê do MongoDB e publica num broker MQTT local
   (Mosquitto).
4. **script_3_mysql_monitor.py** subscreve o broker local e regista no MySQL,
   usando stored procedures.
5. **jogador.py** (jogador), a **dashboard PHP** e o **app Android** completam o
   sistema.

## Stack

- Android (Java, Gradle) e Python para jogadores e monitorização
- PHP (Apache) para a dashboard web
- Mosquitto (MQTT) para comunicação em tempo real
- MySQL (relacional) e MongoDB (replica set)
- Docker para orquestrar os serviços (1 ou 2 PCs)

## Como correr

Pré-requisitos: Docker Desktop, Python 3 (pacotes `paho-mqtt`, `pymongo`,
`mysql.connector`) e, para os scripts em Windows, os `.bat` da raiz.

Tudo num PC (desenvolvimento):

    docker compose up -d

Depois, carregar as stored procedures e iniciar os scripts por ordem:

    docker exec -i pisid_mysql mysql -uroot -proot pisid_maze < mysql-init/02_stored_procedures.sql
    docker exec -i pisid_mysql mysql -uroot -proot pisid_maze < mysql-init/04_form_procedures.sql
    python ficheiros_auxiliares/script_0_setup.py
    python ficheiros_auxiliares/script_1_mongodb.py
    python ficheiros_auxiliares/script_2_mongo_to_mqtt.py
    python ficheiros_auxiliares/script_3_mysql_monitor.py
    python ficheiros_auxiliares/jogador.py

Em Windows, o `SETUP.bat` sobe o Docker e o `RUN_ALL.bat` faz todo o fluxo e
abre os terminais em split screen.

Dois PCs (produção): usar `docker compose -f docker-compose-pc1.yml` no PC1
(MQTT + MongoDB) e `docker compose -f docker-compose-pc2.yml` no PC2 (MySQL +
dashboard), e no `ficheiros_auxiliares/config.py` apontar `MQTT_BROKER_LOCAL`
para o IP do PC1 na rede.

Acessos (dev local): dashboard em `http://localhost`, phpMyAdmin em
`http://localhost:8080` (aluno/aluno), MQTT na porta 1883. As credenciais
(`root/root`, `aluno/aluno`) são apenas para desenvolvimento local.

### Nota sobre o simulador Mazerun

O `mazerun.exe` é um simulador compilado do enunciado e NÃO está incluído no
repositório (binário grande, ~30 MB). O `RUN_ALL.bat` espera-o em
`ficheiros_auxiliares/mazerun/mazerun.exe`. Para correr o fluxo completo com
dados reais, coloca o simulador nesse caminho; os scripts de dados correm à
mesma (apenas sem fonte de dados de sensores).

## Estrutura

- `android/`, aplicação Android (abrir no Android Studio)
- `html/` + `php-docker/`, dashboard web em PHP
- `mosquitto/`, configuração do broker MQTT
- `mysql-init/`, inicialização do MySQL e stored procedures
- `ficheiros_auxiliares/`, scripts Python (configuração central em `config.py`,
  validação, backups, monitorização) e o simulador Mazerun (externo)
- `docker-compose*.yml`, composição dos serviços (1 PC e 2 PCs)

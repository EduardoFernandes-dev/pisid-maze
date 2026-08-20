USE pisid_maze;

DELIMITER //

-- Inserir medição de passagem/movimento
DROP PROCEDURE IF EXISTS sp_inserir_passagem;

CREATE PROCEDURE sp_inserir_passagem(
    IN p_Hora TIMESTAMP,
    IN p_SalaOrigem INT,
    IN p_SalaDestino INT,
    IN p_Marsami INT,
    IN p_Status INT
)
BEGIN
    DECLARE v_idSimulacao INT;
    
    -- Tenta obter a simulação ativa (assumindo que há uma IsActive = 0)
    -- Se não houver, pega na última inserida por segurança (fallback para testes)
    SELECT idSimulacao INTO v_idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1;
    IF v_idSimulacao IS NULL THEN
        SELECT idSimulacao INTO v_idSimulacao FROM simulacao ORDER BY idSimulacao DESC LIMIT 1;
    END IF;

    -- Levantar um erro explícito se não houver NENHUMA simulação na BD
    IF v_idSimulacao IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERRO: Nenhuma Simulação existe na Base de Dados!';
    END IF;

    -- Só avança se existir uma simulação
    IF v_idSimulacao IS NOT NULL THEN

        -- Caso especial: Origin=0 e Destiny=0 significa marsami preso (cansaço ou sem saída)
        -- Apenas marcar como cansado, não criar/mover nada
        IF p_SalaOrigem = 0 AND p_SalaDestino = 0 THEN
            IF EXISTS (SELECT 1 FROM marsamis WHERE idSimulacao = v_idSimulacao AND idMarsami = p_Marsami) THEN
                UPDATE marsamis SET Cansado = 1
                WHERE idSimulacao = v_idSimulacao AND idMarsami = p_Marsami;
            END IF;
        ELSE
            -- Verifica se o Marsami já existe nesta simulação
            IF NOT EXISTS (SELECT 1 FROM marsamis WHERE idSimulacao = v_idSimulacao AND idMarsami = p_Marsami) THEN
                -- Cria o marsami, na largada, a SalaOrigem é 0 (spawner), logo a sala real é o Destino
                INSERT INTO marsamis (idSimulacao, idMarsami, Tipo, Cansado, idSalaAtual) 
                VALUES (
                    v_idSimulacao, 
                    p_Marsami, 
                    IF(p_Marsami % 2 = 0, 'Even', 'Odd'), 
                    IF(p_Status = 2, 1, 0), 
                    p_SalaDestino
                );
            ELSE
                -- Se já existe, atualiza a sala em que está e o estado de cansaço
                UPDATE marsamis 
                SET idSalaAtual = p_SalaDestino,
                    Cansado = IF(p_Status = 2, 1, 0)
                WHERE idSimulacao = v_idSimulacao AND idMarsami = p_Marsami;
            END IF;

            -- ATUALIZAR A OCUPAÇÃO DO LABIRINTO (Nº de Pares/Ímpares)
            -- Subtrai da sala de origem (ignorar sala 0 = spawner)
            IF p_SalaOrigem > 0 THEN
                UPDATE ocupacaolabirinto
                SET nrMarsamisOdd = (SELECT COUNT(*) FROM marsamis WHERE idSimulacao = v_idSimulacao AND idSalaAtual = p_SalaOrigem AND Tipo = 'Odd'),
                    nrMarsamisEven = (SELECT COUNT(*) FROM marsamis WHERE idSimulacao = v_idSimulacao AND idSalaAtual = p_SalaOrigem AND Tipo = 'Even')
                WHERE idSimulacao = v_idSimulacao AND idSala = p_SalaOrigem;
            END IF;

            -- Adiciona à sala de destino (ignorar sala 0)
            IF p_SalaDestino > 0 THEN
                UPDATE ocupacaolabirinto
                SET nrMarsamisOdd = (SELECT COUNT(*) FROM marsamis WHERE idSimulacao = v_idSimulacao AND idSalaAtual = p_SalaDestino AND Tipo = 'Odd'),
                    nrMarsamisEven = (SELECT COUNT(*) FROM marsamis WHERE idSimulacao = v_idSimulacao AND idSalaAtual = p_SalaDestino AND Tipo = 'Even')
                WHERE idSimulacao = v_idSimulacao AND idSala = p_SalaDestino;
            END IF;
        END IF;

        -- Registar sempre no histórico de movimentos
        INSERT INTO historico_movimentos (idSimulacao, idMarsami, Hora, SalaOrigem, SalaDestino, Status)
        VALUES (v_idSimulacao, p_Marsami, p_Hora, p_SalaOrigem, p_SalaDestino, p_Status);
    END IF;
END //

-- Inserir medição de temperatura
DROP PROCEDURE IF EXISTS sp_inserir_temperatura;

CREATE PROCEDURE sp_inserir_temperatura(
    IN p_Hora TIMESTAMP,
    IN p_Temperatura VARCHAR(50)
)
BEGIN
    DECLARE v_idSimulacao INT;
    
    SELECT idSimulacao INTO v_idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1;
    IF v_idSimulacao IS NULL THEN
        SELECT idSimulacao INTO v_idSimulacao FROM simulacao ORDER BY idSimulacao DESC LIMIT 1;
    END IF;

    IF v_idSimulacao IS NOT NULL THEN
        INSERT INTO temperatura (idSimulacao, Hora, Temp)
        VALUES (v_idSimulacao, p_Hora, CAST(p_Temperatura AS DECIMAL(6,2)));
    END IF;
END //

-- Inserir leitura de som/ruído
DROP PROCEDURE IF EXISTS sp_inserir_som;

CREATE PROCEDURE sp_inserir_som(
    IN p_Hora TIMESTAMP,
    IN p_Som VARCHAR(50)
)
BEGIN
    DECLARE v_idSimulacao INT;
    
    SELECT idSimulacao INTO v_idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1;
    IF v_idSimulacao IS NULL THEN
        SELECT idSimulacao INTO v_idSimulacao FROM simulacao ORDER BY idSimulacao DESC LIMIT 1;
    END IF;

    IF v_idSimulacao IS NOT NULL THEN
        INSERT INTO som (idSimulacao, Hora, Som)
        VALUES (v_idSimulacao, p_Hora, CAST(p_Som AS DECIMAL(6,2)));
    END IF;
END //

DELIMITER //

-- Inserir configuração estática do labirinto (SetupMaze) da Nuvem
DROP PROCEDURE IF EXISTS sp_inserir_setupmaze;

CREATE PROCEDURE sp_inserir_setupmaze(
    IN p_nrRooms INT,
    IN p_nrMarsamis INT,
    IN p_nrPlayers INT,
    IN p_normalTemp DECIMAL(6,2),
    IN p_tempVarHighTol DECIMAL(6,2),
    IN p_tempVarLowTol DECIMAL(6,2),
    IN p_normalSom DECIMAL(6,2),
    IN p_somVarTol DECIMAL(6,2)
)
BEGIN
    INSERT INTO setupmaze (nrRooms, nrMarsamis, nrPlayers, normalTemp, tempVarHighTol, tempVarLowTol, normalSom, somVarTol)
    VALUES (p_nrRooms, p_nrMarsamis, p_nrPlayers, p_normalTemp, p_tempVarHighTol, p_tempVarLowTol, p_normalSom, p_somVarTol);
END //

-- Inserir corredor válido vindo do mapa da Nuvem
DROP PROCEDURE IF EXISTS sp_inserir_corredor_mapa;

CREATE PROCEDURE sp_inserir_corredor_mapa(
    IN p_RoomA INT,
    IN p_RoomB INT
)
BEGIN
    DECLARE v_idSimulacao INT;
    
    -- Tenta obter a simulação ativa
    SELECT idSimulacao INTO v_idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1;
    IF v_idSimulacao IS NULL THEN
        SELECT idSimulacao INTO v_idSimulacao FROM simulacao ORDER BY idSimulacao DESC LIMIT 1;
    END IF;

    IF v_idSimulacao IS NOT NULL THEN
        INSERT INTO corredores_mapa (idSimulacao, RoomA, RoomB)
        VALUES (v_idSimulacao, p_RoomA, p_RoomB);
    END IF;
END //

DELIMITER ;

-- ==========================================
-- Triggers para Alertas (Temperatura e Som)
-- =========================================
DELIMITER $$

DROP TRIGGER IF EXISTS alertVerifyTemp$$

CREATE TRIGGER alertVerifyTemp
AFTER INSERT ON temperatura
FOR EACH ROW
BEGIN
    DECLARE v_tempTol DECIMAL(6,2);

    SELECT sm.tempVarHighTol INTO v_tempTol
    FROM setupmaze sm
    JOIN simulacao s ON s.IDSetup = sm.idSetup
    WHERE s.idSimulacao = NEW.idSimulacao
    LIMIT 1;

    IF (SELECT COUNT(*) FROM alertas WHERE idSimulacao = NEW.idSimulacao) > 0 THEN
        UPDATE alertas
        SET Temperatura = (NEW.Temp > v_tempTol)
        WHERE idSimulacao = NEW.idSimulacao;
    ELSE
        INSERT INTO alertas (idSimulacao, Som, Temperatura)
        VALUES (NEW.idSimulacao, 0, NEW.Temp > v_tempTol);
    END IF;
END$$

DROP TRIGGER IF EXISTS alertVerifySom$$

CREATE TRIGGER alertVerifySom
AFTER INSERT ON som
FOR EACH ROW
BEGIN
    DECLARE v_somTol DECIMAL(6,2);

    SELECT sm.somVarTol INTO v_somTol
    FROM setupmaze sm
    JOIN simulacao s ON s.IDSetup = sm.idSetup
    WHERE s.idSimulacao = NEW.idSimulacao
    LIMIT 1;

    IF (SELECT COUNT(*) FROM alertas WHERE idSimulacao = NEW.idSimulacao) > 0 THEN
        UPDATE alertas
        SET Som = (NEW.Som > v_somTol)
        WHERE idSimulacao = NEW.idSimulacao;
    ELSE
        INSERT INTO alertas (idSimulacao, Som, Temperatura)
        VALUES (NEW.idSimulacao, NEW.Som > v_somTol, 0);
    END IF;
END$$

DELIMITER ;

-- ============================================
-- PISID, Stored Procedures para Formulários
-- Grupo 16
-- ============================================

USE pisid_maze;

-- ============================================
-- SP: Criar_Jogo (S2)
-- Cria uma nova simulação para a equipa
-- ============================================
DROP PROCEDURE IF EXISTS Criar_Jogo;
DELIMITER //
CREATE PROCEDURE Criar_Jogo(
    IN p_Descricao TEXT,
    IN p_IDEquipa INT,
    IN p_CriadorEmail VARCHAR(50)
)
BEGIN
    -- Verificar se o criador pertence à equipa
    DECLARE v_equipa INT;
    SELECT Equipa INTO v_equipa FROM utilizador WHERE Email = p_CriadorEmail;
    
    IF v_equipa IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Utilizador não encontrado.';
    ELSEIF v_equipa != p_IDEquipa THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'O utilizador não pertence à equipa indicada.';
    ELSE
        INSERT INTO simulacao (Descricao, IDEquipa, IDSetup, IsActive, CriadorEmail, DataHoraInicio)
        VALUES (p_Descricao, p_IDEquipa, NULL, -1, p_CriadorEmail, NULL);
        
        SELECT LAST_INSERT_ID() AS idSimulacao;
    END IF;
END //
DELIMITER ;


-- ============================================
-- SP: Iniciar_Jogo (S3)
-- Inicia uma simulação (muda IsActive para 0)
-- Apenas o criador pode iniciar
-- Não pode haver outra simulação ativa na equipa
-- ============================================
DROP PROCEDURE IF EXISTS Iniciar_Jogo;
DELIMITER //
CREATE PROCEDURE Iniciar_Jogo(
    IN p_IDSimulacao INT,
    IN p_IDEquipa INT,
    IN p_CriadorEmail VARCHAR(50)
)
BEGIN
    DECLARE v_criador VARCHAR(50);
    DECLARE v_estado INT;
    DECLARE v_ativas INT;
    
    -- Verificar se a simulação existe e obter dados
    SELECT CriadorEmail, IsActive INTO v_criador, v_estado
    FROM simulacao WHERE idSimulacao = p_IDSimulacao AND IDEquipa = p_IDEquipa;
    
    IF v_criador IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Simulação não encontrada.';
    ELSEIF v_criador != p_CriadorEmail THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Apenas o criador pode iniciar a simulação.';
    ELSEIF v_estado != -1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A simulação não está no estado inicial (-1).';
    ELSE
        -- Verificar se já há simulação ativa na equipa
        SELECT COUNT(*) INTO v_ativas FROM simulacao 
        WHERE IDEquipa = p_IDEquipa AND IsActive = 0;
        
        IF v_ativas > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Já existe uma simulação ativa nesta equipa.';
        ELSE
            UPDATE simulacao 
            SET IsActive = 0, DataHoraInicio = NOW() 
            WHERE idSimulacao = p_IDSimulacao;
        END IF;
    END IF;
END //
DELIMITER ;


-- ============================================
-- SP: Alterar_Jogo (S4)
-- Edita parâmetros de uma simulação existente
-- Apenas o criador pode alterar, e a simulação
-- não pode estar em curso (IsActive deve ser -1)
-- ============================================
DROP PROCEDURE IF EXISTS Alterar_Jogo;
DELIMITER //
CREATE PROCEDURE Alterar_Jogo(
    IN p_IDSimulacao INT,
    IN p_Descricao TEXT,
    IN p_CriadorEmail VARCHAR(50)
)
BEGIN
    DECLARE v_criador VARCHAR(50);
    DECLARE v_estado INT;
    
    SELECT CriadorEmail, IsActive INTO v_criador, v_estado
    FROM simulacao WHERE idSimulacao = p_IDSimulacao;
    
    IF v_criador IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Simulação não encontrada.';
    ELSEIF v_criador != p_CriadorEmail THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Apenas o criador pode alterar a simulação.';
    ELSEIF v_estado != -1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Não é possível alterar uma simulação que já foi iniciada ou terminada.';
    ELSE
        UPDATE simulacao 
        SET Descricao = p_Descricao
        WHERE idSimulacao = p_IDSimulacao;
    END IF;
END //
DELIMITER ;


-- ============================================
-- SP: SP_Inserir_Utilizador (U1)
-- Cria um novo utilizador
-- ============================================
DROP PROCEDURE IF EXISTS SP_Inserir_Utilizador;
DELIMITER //
CREATE PROCEDURE SP_Inserir_Utilizador(
    IN p_Nome VARCHAR(100),
    IN p_Telemovel VARCHAR(12),
    IN p_Email VARCHAR(50),
    IN p_DataNasc DATE,
    IN p_Tipo VARCHAR(3),
    IN p_Equipa INT
)
BEGIN
    DECLARE v_existe INT;
    
    -- Verificar email duplicado
    SELECT COUNT(*) INTO v_existe FROM utilizador WHERE Email = p_Email;
    
    IF v_existe > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Já existe um utilizador com este email.';
    ELSE
        -- Verificar se a equipa existe
        SELECT COUNT(*) INTO v_existe FROM equipa WHERE idEquipa = p_Equipa;
        IF v_existe = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Equipa não encontrada.';
        ELSE
            INSERT INTO utilizador (Nome, Telemovel, Email, DataNasc, Tipo, Equipa)
            VALUES (p_Nome, p_Telemovel, p_Email, p_DataNasc, p_Tipo, p_Equipa);
            
            SELECT LAST_INSERT_ID() AS idUtilizador;
        END IF;
    END IF;
END //
DELIMITER ;


-- ============================================
-- SP: SP_Eliminar_Utilizador (U2)
-- Apaga um utilizador (o admin não pode apagar-se
-- a si próprio)
-- ============================================
DROP PROCEDURE IF EXISTS SP_Eliminar_Utilizador;
DELIMITER //
CREATE PROCEDURE SP_Eliminar_Utilizador(
    IN p_idUtilizador INT,
    IN p_AdminEmail VARCHAR(50)
)
BEGIN
    DECLARE v_email_alvo VARCHAR(50);
    
    SELECT Email INTO v_email_alvo FROM utilizador WHERE idUtilizador = p_idUtilizador;
    
    IF v_email_alvo IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Utilizador não encontrado.';
    ELSEIF v_email_alvo = p_AdminEmail THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Não pode apagar a sua própria conta.';
    ELSE
        DELETE FROM utilizador WHERE idUtilizador = p_idUtilizador;
    END IF;
END //
DELIMITER ;


-- ============================================
-- SP: Alterar_utilizador (U3)
-- Atualiza dados pessoais do utilizador
-- Expandida para incluir Email e DataNasc
-- ============================================
DROP PROCEDURE IF EXISTS Alterar_utilizador;
DELIMITER //
CREATE PROCEDURE Alterar_utilizador(
    IN p_Email VARCHAR(50),
    IN p_Nome VARCHAR(100),
    IN p_Telemovel VARCHAR(12),
    IN p_NovoEmail VARCHAR(50),
    IN p_DataNasc DATE
)
BEGIN
    DECLARE v_existe INT;
    DECLARE v_email_dup INT;
    
    -- Verificar se o utilizador existe
    SELECT COUNT(*) INTO v_existe FROM utilizador WHERE Email = p_Email;
    
    IF v_existe = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Utilizador não encontrado.';
    ELSE
        -- Verificar se o novo email já está em uso por outro utilizador
        IF p_NovoEmail != p_Email THEN
            SELECT COUNT(*) INTO v_email_dup FROM utilizador 
            WHERE Email = p_NovoEmail;
            IF v_email_dup > 0 THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email já está em uso por outro utilizador.';
            END IF;
        END IF;
        
        -- Atualizar dados do utilizador (só executa se não houve SIGNAL acima)
        UPDATE utilizador 
        SET Nome = p_Nome, Telemovel = p_Telemovel, Email = p_NovoEmail, DataNasc = p_DataNasc
        WHERE Email = p_Email;
        
        -- Se o email mudou, atualizar CriadorEmail nas simulações
        IF p_NovoEmail != p_Email THEN
            UPDATE simulacao SET CriadorEmail = p_NovoEmail WHERE CriadorEmail = p_Email;
        END IF;
    END IF;
END //
DELIMITER ;

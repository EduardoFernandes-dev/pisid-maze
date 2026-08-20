USE pisid_maze;

-- Inserir a equipa
INSERT INTO equipa (idEquipa, nomeEquipa) VALUES (16, 'Grupo 16');

-- Inserir os utilizadores adaptados à nova estrutura
INSERT INTO utilizador (Equipa, Nome, Tipo, Telemovel, Email, DataNasc) 
VALUES 
    (16, 'Joana Silva', 'USR', '912345678', 'jps@exemplo.com', '1992-01-01'),
    (16, 'Afonso Nóia', 'USR', '910000001', 'aps@exemplo.com', '2000-01-01'),
    (16, 'Tomás Francisco', 'USR', '910000002', 'tps@exemplo.com', '2001-10-10'),
    (16, 'Duarte Alexandre', 'USR', '910000003', 'dps@exemplo.com', '2002-10-01'),
    (16, 'Tomás Leal', 'USR', '910000010', 'tpsl@exemplo.com', '1998-10-10'),
    (16, 'Eduardo Fernandes', 'USR', '910000112', 'edps@exemplo.com', '1995-05-10'),
    (16, 'Diego Pazos', 'USR', '910000121', 'ddps@exemplo.com', '1999-12-31');

-- Os dados da simulação (SetupMaze, Simulacao e ocupacaolabirinto)
-- vão ser agora injetados dinamicamente pelo script_2_mysql ao arrancar
-- indo buscar diretamente à nuvem do ISCTE!

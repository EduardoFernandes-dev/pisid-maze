<?php
require_once 'config.php';
requireLogin();

$user_email = $_SESSION['user_email'];
$user_nome = $_SESSION['user_nome'];
$user_equipa = $_SESSION['user_equipa'];

$message = '';
$msg_type = '';
$is_edit = false;
$sim = null;

// Se tem ID, é modo edição
if (isset($_GET['id'])) {
    $id = intval($_GET['id']);
    $stmt = $conn->prepare("SELECT * FROM simulacao WHERE idSimulacao = ? AND IDEquipa = ?");
    $stmt->bind_param("ii", $id, $user_equipa);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 1) {
        $sim = $result->fetch_assoc();
        $is_edit = true;
        
        // Verificar se o criador é o utilizador logado
        if ($sim['CriadorEmail'] !== $user_email) {
            $message = 'Apenas o criador da simulação pode editá-la.';
            $msg_type = 'error';
        }
        
        // Verificar se não está no estado inicial (S11, bloquear edição)
        if ($sim['IsActive'] != -1) {
            $message = 'Não é possível editar uma simulação que já foi iniciada ou terminada.';
            $msg_type = 'error';
        }
    } else {
        header("Location: dashboard.php");
        exit();
    }
    $stmt->close();
}

// Processar formulário
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $descricao = trim($_POST['descricao'] ?? '');
    
    if ($is_edit) {
        // Alterar simulação existente
        if ($sim['CriadorEmail'] === $user_email && $sim['IsActive'] == -1) {
            $stmt = $conn->prepare("UPDATE simulacao SET Descricao = ? WHERE idSimulacao = ? AND CriadorEmail = ?");
            $stmt->bind_param("sis", $descricao, $sim['idSimulacao'], $user_email);
            $stmt->execute();
            
            if ($stmt->affected_rows >= 0) {
                header("Location: dashboard.php");
                exit();
            }
            $stmt->close();
        }
    } else {
        // Criar nova simulação (IsActive = -1, DataHoraInicio = NULL)
        $stmt = $conn->prepare("INSERT INTO simulacao (Descricao, IDEquipa, IsActive, CriadorEmail, DataHoraInicio, IDSetup) VALUES (?, ?, -1, ?, NULL, NULL)");
        $stmt->bind_param("sis", $descricao, $user_equipa, $user_email);
        $stmt->execute();
        
        if ($stmt->affected_rows > 0) {
            header("Location: dashboard.php");
            exit();
        } else {
            $message = 'Erro ao criar simulação.';
            $msg_type = 'error';
        }
        $stmt->close();
    }
}

// Mensagem de criação bem-sucedida (redirect)
if (isset($_GET['created'])) {
    $message = 'Simulação criada com sucesso!';
    $msg_type = 'success';
    if (isset($_GET['id'])) {
        $id = intval($_GET['id']);
        $stmt = $conn->prepare("SELECT * FROM simulacao WHERE idSimulacao = ? AND IDEquipa = ?");
        $stmt->bind_param("ii", $id, $user_equipa);
        $stmt->execute();
        $result = $stmt->get_result();
        if ($result->num_rows === 1) {
            $sim = $result->fetch_assoc();
            $is_edit = true;
        }
        $stmt->close();
    }
}

$iniciais = getIniciais($user_nome);
$can_edit = !$is_edit || ($sim['CriadorEmail'] === $user_email && $sim['IsActive'] == -1);
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="<?php echo $is_edit ? 'Editar simulação' : 'Criar nova simulação'; ?>, PISID Maze">
    <title><?php echo $is_edit ? 'Editar Simulação #' . $sim['idSimulacao'] : 'Nova Simulação'; ?>, PISID Maze</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar">
        <a href="dashboard.php" class="navbar-brand">
            🧪 PISID Maze
        </a>
        <div class="navbar-links">
            <a href="dashboard.php" class="nav-link" id="nav-dashboard">📊 Dashboard</a>
            <?php if (isAdmin()): ?>
                <a href="manage_users.php" class="nav-link" id="nav-users">👥 Manage Users</a>
            <?php endif; ?>
            <a href="profile.php" class="nav-link" id="nav-profile">👤 Perfil</a>
            <div class="user-info">
                <div class="user-avatar"><?php echo $iniciais; ?></div>
                <span class="user-name"><?php echo htmlspecialchars($user_nome); ?></span>
            </div>
            <a href="logout.php" class="nav-link danger" id="nav-logout">Sair</a>
        </div>
    </nav>

    <div class="page-wrapper">
        <!-- Header -->
        <div class="page-header">
            <h1><?php echo $is_edit ? '✏️ Editar Simulação #' . $sim['idSimulacao'] : '＋ Nova Simulação'; ?></h1>
            <p><?php echo $is_edit ? 'Modifique os parâmetros da simulação' : 'Configure uma nova simulação para a equipa'; ?></p>
        </div>

        <?php if ($message): ?>
            <div class="alert alert-<?php echo $msg_type; ?>">
                <span><?php echo $msg_type === 'success' ? '✅' : '⚠️'; ?></span>
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>

        <div class="card" style="max-width: 640px;">
            <form method="POST" id="simulation-form">
                <?php if ($is_edit): ?>
                    <!-- Campos não editáveis -->
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label" for="id_simulacao">ID Simulação</label>
                            <input type="text" id="id_simulacao" class="form-input" value="#<?php echo $sim['idSimulacao']; ?>" disabled>
                            <p class="form-hint">Chave primária, não editável</p>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="equipa">Equipa</label>
                            <input type="text" id="equipa" class="form-input" value="Equipa <?php echo $sim['IDEquipa']; ?>" disabled>
                            <p class="form-hint">Chave estrangeira, não editável</p>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="criador">Criador</label>
                        <input type="text" id="criador" class="form-input" value="<?php echo htmlspecialchars($sim['CriadorEmail']); ?>" disabled>
                        <p class="form-hint">Chave estrangeira, não editável</p>
                    </div>

                    <?php if ($sim['DataHoraInicio']): ?>
                        <div class="form-group">
                            <label class="form-label">Data de Início</label>
                            <input type="text" class="form-input" value="<?php echo date('d/m/Y H:i:s', strtotime($sim['DataHoraInicio'])); ?>" disabled>
                        </div>
                    <?php endif; ?>

                    <div class="separator"></div>
                <?php endif; ?>

                <!-- Campo editável: Descrição -->
                <div class="form-group">
                    <label class="form-label" for="descricao">Descrição</label>
                    <textarea 
                        id="descricao" 
                        name="descricao" 
                        class="form-textarea" 
                        placeholder="Descreva a simulação (opcional)..."
                        <?php echo !$can_edit ? 'disabled' : ''; ?>
                    ><?php echo htmlspecialchars($sim['Descricao'] ?? $_POST['descricao'] ?? ''); ?></textarea>
                    <p class="form-hint">Campo opcional</p>
                </div>

                <div class="separator"></div>

                <div class="btn-group">
                    <?php if ($can_edit): ?>
                        <button type="submit" class="btn btn-primary" id="btn-save">
                            <?php echo $is_edit ? '💾 Guardar Alterações' : '✅ Criar Simulação'; ?>
                        </button>
                    <?php endif; ?>
                    <a href="dashboard.php" class="btn btn-secondary" id="btn-cancel">Cancelar</a>
                </div>
            </form>
        </div>
    </div>

    <div class="footer">
        PISID 2025/26, Grupo 16 · ISCTE-IUL
    </div>
</body>
</html>

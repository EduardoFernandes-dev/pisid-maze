<?php
require_once 'config.php';
requireAdmin();

$user_nome = $_SESSION['user_nome'];
$message = '';
$msg_type = '';

// Buscar equipas para o dropdown
$equipas_result = $conn->query("SELECT idEquipa, nomeEquipa FROM equipa ORDER BY idEquipa ASC");
$equipas = [];
while ($row = $equipas_result->fetch_assoc()) {
    $equipas[] = $row;
}

// Processar formulário
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nome = trim($_POST['nome'] ?? '');
    $telemovel = trim($_POST['telemovel'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $datanasc = $_POST['datanasc'] ?? null;
    $tipo = $_POST['tipo'] ?? 'USR';
    $equipa = intval($_POST['equipa'] ?? 0);
    
    // Validações
    if (empty($nome)) {
        $message = 'O nome é obrigatório.';
        $msg_type = 'error';
    } elseif (empty($email)) {
        $message = 'O email é obrigatório.';
        $msg_type = 'error';
    } elseif ($equipa <= 0) {
        $message = 'Selecione uma equipa válida.';
        $msg_type = 'error';
    } elseif (!in_array($tipo, ['USR', 'ADM'])) {
        $message = 'Tipo de utilizador inválido.';
        $msg_type = 'error';
    } else {
        // Verificar email duplicado
        $check = $conn->prepare("SELECT COUNT(*) as cnt FROM utilizador WHERE Email = ?");
        $check->bind_param("s", $email);
        $check->execute();
        $dup = $check->get_result()->fetch_assoc();
        $check->close();
        
        if ($dup['cnt'] > 0) {
            $message = 'Já existe um utilizador com este email.';
            $msg_type = 'error';
        } else {
            $datanasc_val = !empty($datanasc) ? $datanasc : null;
            $telemovel_val = !empty($telemovel) ? $telemovel : null;
            
            $stmt = $conn->prepare("INSERT INTO utilizador (Nome, Telemovel, Email, DataNasc, Tipo, Equipa) VALUES (?, ?, ?, ?, ?, ?)");
            $stmt->bind_param("sssssi", $nome, $telemovel_val, $email, $datanasc_val, $tipo, $equipa);
            $stmt->execute();
            
            if ($stmt->affected_rows > 0) {
                header("Location: manage_users.php?created=1");
                exit();
            } else {
                $message = 'Erro ao criar utilizador.';
                $msg_type = 'error';
            }
            $stmt->close();
        }
    }
}

$iniciais = getIniciais($user_nome);
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Criar utilizador, PISID Maze">
    <title>Novo Utilizador, PISID Maze</title>
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
            <a href="manage_users.php" class="nav-link" id="nav-users">👥 Manage Users</a>
            <a href="profile.php" class="nav-link" id="nav-profile">👤 Perfil</a>
            <div class="user-info">
                <div class="user-avatar"><?php echo $iniciais; ?></div>
                <span class="user-name"><?php echo htmlspecialchars($user_nome); ?></span>
            </div>
            <a href="logout.php" class="nav-link danger" id="nav-logout">Sair</a>
        </div>
    </nav>

    <div class="page-wrapper">
        <div class="page-header">
            <h1>＋ Novo Utilizador</h1>
            <p>Criar uma nova conta de utilizador</p>
        </div>

        <?php if ($message): ?>
            <div class="alert alert-<?php echo $msg_type; ?>">
                <span><?php echo $msg_type === 'success' ? '✅' : '⚠️'; ?></span>
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>

        <div class="card" style="max-width: 640px;">
            <form method="POST" id="create-user-form">
                <div class="form-group">
                    <label class="form-label" for="nome">Nome *</label>
                    <input 
                        type="text" 
                        id="nome" 
                        name="nome" 
                        class="form-input" 
                        value="<?php echo htmlspecialchars($_POST['nome'] ?? ''); ?>"
                        placeholder="Nome completo"
                        maxlength="100"
                        required
                    >
                </div>

                <div class="form-group">
                    <label class="form-label" for="email">Email *</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        class="form-input" 
                        value="<?php echo htmlspecialchars($_POST['email'] ?? ''); ?>"
                        placeholder="exemplo@iscte-iul.pt"
                        maxlength="50"
                        required
                    >
                    <p class="form-hint">Deve ser único no sistema</p>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label" for="telemovel">Telemóvel</label>
                        <input 
                            type="tel" 
                            id="telemovel" 
                            name="telemovel" 
                            class="form-input" 
                            value="<?php echo htmlspecialchars($_POST['telemovel'] ?? ''); ?>"
                            placeholder="9XXXXXXXX"
                            maxlength="12"
                        >
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="datanasc">Data de Nascimento</label>
                        <input 
                            type="date" 
                            id="datanasc" 
                            name="datanasc" 
                            class="form-input" 
                            value="<?php echo htmlspecialchars($_POST['datanasc'] ?? ''); ?>"
                        >
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label" for="tipo">Tipo *</label>
                        <select id="tipo" name="tipo" class="form-select" required>
                            <option value="USR" <?php echo ($_POST['tipo'] ?? '') === 'USR' ? 'selected' : ''; ?>>USR, Utilizador Normal</option>
                            <option value="ADM" <?php echo ($_POST['tipo'] ?? '') === 'ADM' ? 'selected' : ''; ?>>ADM, Administrador</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="equipa">Equipa *</label>
                        <select id="equipa" name="equipa" class="form-select" required>
                            <option value="">Selecionar equipa...</option>
                            <?php foreach ($equipas as $eq): ?>
                                <option value="<?php echo $eq['idEquipa']; ?>" <?php echo (intval($_POST['equipa'] ?? 0) === $eq['idEquipa']) ? 'selected' : ''; ?>>
                                    <?php echo htmlspecialchars($eq['nomeEquipa'] ?? 'Equipa ' . $eq['idEquipa']); ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                </div>

                <div class="separator"></div>

                <div class="btn-group">
                    <button type="submit" class="btn btn-primary" id="btn-create-user">
                        ✅ Criar Utilizador
                    </button>
                    <a href="manage_users.php" class="btn btn-secondary" id="btn-cancel">Cancelar</a>
                </div>
            </form>
        </div>
    </div>

    <div class="footer">
        PISID 2025/26, Grupo 16 · ISCTE-IUL
    </div>
</body>
</html>

<?php
require_once 'config.php';
requireLogin();

$user_email = $_SESSION['user_email'];
$user_nome = $_SESSION['user_nome'];
$user_equipa = $_SESSION['user_equipa'];
$user_tipo = $_SESSION['user_tipo'];

$message = '';
$msg_type = '';

// Buscar dados atuais do utilizador
$stmt = $conn->prepare("SELECT Nome, Telemovel, Tipo, Email, DataNasc, Equipa FROM utilizador WHERE Email = ?");
$stmt->bind_param("s", $user_email);
$stmt->execute();
$result = $stmt->get_result();
$user = $result->fetch_assoc();
$stmt->close();

// Processar alterações do perfil
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $novo_nome = trim($_POST['nome'] ?? '');
    $novo_telemovel = trim($_POST['telemovel'] ?? '');
    $novo_email = trim($_POST['novo_email'] ?? '');
    $novo_datanasc = $_POST['datanasc'] ?? null;
    
    if (empty($novo_nome)) {
        $message = 'O nome é obrigatório.';
        $msg_type = 'error';
    } elseif (empty($novo_email)) {
        $message = 'O email é obrigatório.';
        $msg_type = 'error';
    } else {
        // Verificar se o novo email já está em uso por outro
        if ($novo_email !== $user_email) {
            $check = $conn->prepare("SELECT COUNT(*) as cnt FROM utilizador WHERE Email = ?");
            $check->bind_param("s", $novo_email);
            $check->execute();
            $dup = $check->get_result()->fetch_assoc();
            $check->close();
            
            if ($dup['cnt'] > 0) {
                $message = 'Este email já está em uso por outro utilizador.';
                $msg_type = 'error';
            }
        }
        
        if (empty($message)) {
            $datanasc_val = !empty($novo_datanasc) ? $novo_datanasc : null;
            
            $stmt = $conn->prepare("UPDATE utilizador SET Nome = ?, Telemovel = ?, Email = ?, DataNasc = ? WHERE Email = ?");
            $stmt->bind_param("sssss", $novo_nome, $novo_telemovel, $novo_email, $datanasc_val, $user_email);
            $stmt->execute();
            
            if ($stmt->affected_rows >= 0) {
                // Se o email mudou, atualizar CriadorEmail nas simulações
                if ($novo_email !== $user_email) {
                    $upd = $conn->prepare("UPDATE simulacao SET CriadorEmail = ? WHERE CriadorEmail = ?");
                    $upd->bind_param("ss", $novo_email, $user_email);
                    $upd->execute();
                    $upd->close();
                }
                
                $message = 'Perfil atualizado com sucesso!';
                $msg_type = 'success';
                
                // Atualizar sessão
                $_SESSION['user_nome'] = $novo_nome;
                $_SESSION['user_telemovel'] = $novo_telemovel;
                $_SESSION['user_email'] = $novo_email;
                $user_email = $novo_email;
                $user_nome = $novo_nome;
                
                // Atualizar dados locais
                $user['Nome'] = $novo_nome;
                $user['Telemovel'] = $novo_telemovel;
                $user['Email'] = $novo_email;
                $user['DataNasc'] = $datanasc_val;
            } else {
                $message = 'Erro ao atualizar perfil.';
                $msg_type = 'error';
            }
            $stmt->close();
        }
    }
}

$iniciais = getIniciais($user['Nome']);
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Perfil do utilizador, PISID Maze">
    <title>Perfil, PISID Maze</title>
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
            <a href="profile.php" class="nav-link active" id="nav-profile">👤 Perfil</a>
            <div class="user-info">
                <div class="user-avatar"><?php echo $iniciais; ?></div>
                <span class="user-name"><?php echo htmlspecialchars($user['Nome']); ?></span>
            </div>
            <a href="logout.php" class="nav-link danger" id="nav-logout">Sair</a>
        </div>
    </nav>

    <div class="page-wrapper">
        <div class="page-header">
            <h1>👤 Meu Perfil</h1>
            <p>Gerir os seus dados pessoais</p>
        </div>

        <?php if ($message): ?>
            <div class="alert alert-<?php echo $msg_type; ?>">
                <span><?php echo $msg_type === 'success' ? '✅' : '⚠️'; ?></span>
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>

        <div class="card" style="max-width: 640px;">
            <!-- Profile Header -->
            <div class="profile-header">
                <div class="profile-avatar"><?php echo $iniciais; ?></div>
                <div class="profile-meta">
                    <h2><?php echo htmlspecialchars($user['Nome']); ?></h2>
                    <p><?php echo htmlspecialchars($user['Email']); ?> · Equipa <?php echo $user['Equipa']; ?></p>
                </div>
            </div>

            <div class="separator"></div>

            <form method="POST" id="profile-form">
                <!-- Campos não editáveis -->
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label" for="equipa">Equipa</label>
                        <input type="text" id="equipa" class="form-input" value="Equipa <?php echo $user['Equipa']; ?>" disabled>
                        <p class="form-hint">Não editável</p>
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="tipo">Tipo</label>
                        <input type="text" id="tipo" class="form-input" value="<?php echo htmlspecialchars($user['Tipo']); ?>" disabled>
                        <p class="form-hint">Não editável</p>
                    </div>
                </div>

                <div class="separator"></div>

                <!-- Campos editáveis -->
                <div class="form-group">
                    <label class="form-label" for="nome">Nome *</label>
                    <input 
                        type="text" 
                        id="nome" 
                        name="nome" 
                        class="form-input" 
                        value="<?php echo htmlspecialchars($user['Nome']); ?>"
                        placeholder="O seu nome completo"
                        required
                    >
                </div>

                <div class="form-group">
                    <label class="form-label" for="novo_email">Email *</label>
                    <input 
                        type="email" 
                        id="novo_email" 
                        name="novo_email" 
                        class="form-input" 
                        value="<?php echo htmlspecialchars($user['Email']); ?>"
                        placeholder="exemplo@iscte-iul.pt"
                        required
                    >
                    <p class="form-hint">Se alterar o email, as suas simulações serão atualizadas automaticamente</p>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label" for="telemovel">Telemóvel</label>
                        <input 
                            type="tel" 
                            id="telemovel" 
                            name="telemovel" 
                            class="form-input" 
                            value="<?php echo htmlspecialchars($user['Telemovel'] ?? ''); ?>"
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
                            value="<?php echo $user['DataNasc'] ?? ''; ?>"
                        >
                    </div>
                </div>

                <div class="separator"></div>

                <div class="btn-group">
                    <button type="submit" class="btn btn-primary" id="btn-save-profile">
                        💾 Guardar Alterações
                    </button>
                    <a href="logout.php" class="btn btn-danger" id="btn-logout">
                        🚪 Terminar Sessão
                    </a>
                </div>
            </form>
        </div>
    </div>

    <div class="footer">
        PISID 2025/26, Grupo 16 · ISCTE-IUL
    </div>
</body>
</html>

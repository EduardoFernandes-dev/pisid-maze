<?php
require_once 'config.php';
requireAdmin();

$user_email = $_SESSION['user_email'];
$user_nome = $_SESSION['user_nome'];

$message = '';
$msg_type = '';

// Mensagem de criação bem-sucedida (redirect de create_user.php)
if (isset($_GET['created'])) {
    $message = 'Utilizador criado com sucesso!';
    $msg_type = 'success';
}

// Processar ação: Apagar utilizador
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    
    if ($action === 'apagar') {
        $id = intval($_POST['id_utilizador']);
        
        // Verificar que não está a apagar-se a si próprio
        $check = $conn->prepare("SELECT Email FROM utilizador WHERE idUtilizador = ?");
        $check->bind_param("i", $id);
        $check->execute();
        $alvo = $check->get_result()->fetch_assoc();
        $check->close();
        
        if (!$alvo) {
            $message = 'Utilizador não encontrado.';
            $msg_type = 'error';
        } elseif ($alvo['Email'] === $user_email) {
            $message = 'Não pode apagar a sua própria conta.';
            $msg_type = 'error';
        } else {
            $stmt = $conn->prepare("DELETE FROM utilizador WHERE idUtilizador = ?");
            $stmt->bind_param("i", $id);
            $stmt->execute();
            
            if ($stmt->affected_rows > 0) {
                $message = 'Utilizador apagado com sucesso.';
                $msg_type = 'success';
            } else {
                $message = 'Não foi possível apagar o utilizador.';
                $msg_type = 'error';
            }
            $stmt->close();
        }
    }
}

// Buscar todos os utilizadores
$result = $conn->query("
    SELECT u.idUtilizador, u.Nome, u.Email, u.Telemovel, u.Tipo, 
           u.DataNasc, u.Equipa, e.nomeEquipa
    FROM utilizador u
    LEFT JOIN equipa e ON u.Equipa = e.idEquipa
    ORDER BY u.idUtilizador ASC
");

$users = [];
while ($row = $result->fetch_assoc()) {
    $users[] = $row;
}

$iniciais = getIniciais($user_nome);
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Gestão de utilizadores, PISID Maze">
    <meta http-equiv="refresh" content="15">
    <title>Manage Users, PISID Maze</title>
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
            <a href="manage_users.php" class="nav-link active" id="nav-users">👥 Manage Users</a>
            <a href="profile.php" class="nav-link" id="nav-profile">👤 Perfil</a>
            <div class="user-info">
                <div class="user-avatar"><?php echo $iniciais; ?></div>
                <span class="user-name"><?php echo htmlspecialchars($user_nome); ?></span>
            </div>
            <a href="logout.php" class="nav-link danger" id="nav-logout">Sair</a>
        </div>
    </nav>

    <div class="page-wrapper">
        <!-- Mensagens -->
        <?php if ($message): ?>
            <div class="alert alert-<?php echo $msg_type; ?>">
                <span><?php echo $msg_type === 'success' ? '✅' : '⚠️'; ?></span>
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>

        <!-- Header -->
        <div class="dashboard-header">
            <div>
                <h1 class="dashboard-title">👥 Gestão de Utilizadores</h1>
                <p style="color: #64748b; font-size: 0.875rem; margin-top: 0.25rem;">Criar e gerir contas de utilizadores</p>
            </div>
            <a href="create_user.php" class="btn btn-primary" id="btn-new-user">
                ＋ Novo Utilizador
            </a>
        </div>

        <!-- Tabela de Utilizadores -->
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Lista de Utilizadores</h2>
                <p class="card-subtitle"><?php echo count($users); ?> utilizador(es) registado(s)</p>
            </div>

            <?php if (count($users) > 0): ?>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nome</th>
                                <th>Email</th>
                                <th>Telemóvel</th>
                                <th>Tipo</th>
                                <th>Equipa</th>
                                <th>Data Nasc.</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($users as $u): ?>
                                <tr>
                                    <td><strong>#<?php echo $u['idUtilizador']; ?></strong></td>
                                    <td><?php echo htmlspecialchars($u['Nome']); ?></td>
                                    <td><?php echo htmlspecialchars($u['Email']); ?></td>
                                    <td><?php echo htmlspecialchars($u['Telemovel'] ?? ', '); ?></td>
                                    <td>
                                        <?php if ($u['Tipo'] === 'ADM'): ?>
                                            <span class="badge badge-admin">ADM</span>
                                        <?php else: ?>
                                            <span class="badge badge-user">USR</span>
                                        <?php endif; ?>
                                    </td>
                                    <td><?php echo htmlspecialchars($u['nomeEquipa'] ?? 'Equipa ' . $u['Equipa']); ?></td>
                                    <td><?php echo $u['DataNasc'] ? date('d/m/Y', strtotime($u['DataNasc'])) : ', '; ?></td>
                                    <td>
                                        <div class="table-actions">
                                            <?php if ($u['Email'] !== $user_email): ?>
                                                <form method="POST" style="display:inline;">
                                                    <input type="hidden" name="action" value="apagar">
                                                    <input type="hidden" name="id_utilizador" value="<?php echo $u['idUtilizador']; ?>">
                                                    <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('Apagar o utilizador <?php echo htmlspecialchars($u['Nome']); ?>?')">🗑️ Apagar</button>
                                                </form>
                                            <?php else: ?>
                                                <span style="color: #94a3b8; font-size: 0.8rem;">(você)</span>
                                            <?php endif; ?>
                                        </div>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            <?php else: ?>
                <div class="empty-state">
                    <div class="icon">👥</div>
                    <h3>Nenhum utilizador encontrado</h3>
                    <p>Crie o primeiro utilizador.</p>
                    <a href="create_user.php" class="btn btn-primary">＋ Criar Utilizador</a>
                </div>
            <?php endif; ?>
        </div>
    </div>

    <div class="footer">
        PISID 2025/26, Grupo 16 · ISCTE-IUL
    </div>
</body>
</html>

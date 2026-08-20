<?php
require_once 'config.php';
requireLogin();

$user_email = $_SESSION['user_email'];
$user_nome = $_SESSION['user_nome'];
$user_equipa = $_SESSION['user_equipa'];
$user_tipo = $_SESSION['user_tipo'];

$message = '';
$msg_type = '';

// Processar ação: Iniciar simulação
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    
    if ($action === 'iniciar') {
        $id = intval($_POST['id_simulacao']);
        // Verificar se já existe simulação ativa na equipa
        $check = $conn->prepare("SELECT COUNT(*) as cnt FROM simulacao WHERE IDEquipa = ? AND IsActive = 0");
        $check->bind_param("i", $user_equipa);
        $check->execute();
        $check_result = $check->get_result()->fetch_assoc();
        $check->close();
        
        if ($check_result['cnt'] > 0) {
            $message = 'Já existe uma simulação ativa. Aguarde que termine antes de iniciar outra.';
            $msg_type = 'error';
        } else {
            // Verificar se o user é o criador
            $stmt = $conn->prepare("SELECT CriadorEmail, IsActive FROM simulacao WHERE idSimulacao = ? AND IDEquipa = ?");
            $stmt->bind_param("ii", $id, $user_equipa);
            $stmt->execute();
            $sim_data = $stmt->get_result()->fetch_assoc();
            $stmt->close();
            
            if (!$sim_data) {
                $message = 'Simulação não encontrada.';
                $msg_type = 'error';
            } elseif ($sim_data['CriadorEmail'] !== $user_email) {
                $message = 'Apenas o criador pode iniciar a simulação.';
                $msg_type = 'error';
            } elseif ($sim_data['IsActive'] != -1) {
                $message = 'A simulação não está no estado inicial.';
                $msg_type = 'error';
            } else {
                // Atualizar BD
                $stmt = $conn->prepare("UPDATE simulacao SET IsActive = 0, DataHoraInicio = NOW() WHERE idSimulacao = ?");
                $stmt->bind_param("i", $id);
                $stmt->execute();
                
                if ($stmt->affected_rows > 0) {
                    // PHP corre nativamente no Windows, lançar o RUN_ALL.bat
                    $project_dir = realpath(__DIR__ . '/..');
                    $bat_path = $project_dir . '\\RUN_ALL.bat';
                    pclose(popen("start \"\" \"$bat_path\"", 'r'));
                    
                    $message = 'Simulação #' . $id . ' iniciada com sucesso! O Mazerun e os Scripts abriram em janelas separadas.';
                    $msg_type = 'success';
                } else {
                    $message = 'Não foi possível iniciar a simulação.';
                    $msg_type = 'error';
                }
                $stmt->close();
            }
        }
    }
}

// Buscar simulações criadas pelo utilizador
$stmt = $conn->prepare("SELECT * FROM simulacao WHERE CriadorEmail = ? ORDER BY idSimulacao DESC");
$stmt->bind_param("s", $user_email);
$stmt->execute();
$simulacoes = $stmt->get_result();

$total = 0;
$simulacao_ativa = null;
$rows = [];
while ($row = $simulacoes->fetch_assoc()) {
    $rows[] = $row;
    $total++;
    if ($row['IsActive'] == 0) {
        $simulacao_ativa = $row;
    }
}
$stmt->close();
$tem_ativa = ($simulacao_ativa !== null);

$iniciais = getIniciais($user_nome);
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Dashboard de gestão de simulações PISID.">
    <meta http-equiv="refresh" content="15">
    <title>Dashboard, PISID Maze</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar">
        <a href="dashboard.php" class="navbar-brand">
            🧪 PISID Maze
        </a>
        <div class="navbar-links">
            <a href="dashboard.php" class="nav-link active" id="nav-dashboard">📊 Dashboard</a>
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
        <!-- Mensagens -->
        <?php if ($message): ?>
            <div class="alert alert-<?php echo $msg_type; ?>">
                <span><?php echo $msg_type === 'success' ? '✅' : '⚠️'; ?></span>
                <?php echo $message; ?>
            </div>
        <?php endif; ?>

        <!-- Header -->
        <div class="dashboard-header">
            <div>
                <h1 class="dashboard-title">Minhas <span>Simulações</span></h1>
                <p style="color: #64748b; font-size: 0.875rem; margin-top: 0.25rem;">Gestão das suas simulações do labirinto</p>
            </div>
            <a href="edit_simulation.php" class="btn btn-primary" id="btn-new-simulation">
                ＋ Nova Simulação
            </a>
        </div>

        <!-- Estatísticas -->
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-label">Total Simulações</div>
                <div class="stat-value"><?php echo $total; ?></div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Simulação Ativa</div>
                <?php if ($simulacao_ativa): ?>
                    <div class="stat-value accent">#<?php echo $simulacao_ativa['idSimulacao']; ?></div>
                <?php else: ?>
                    <div class="stat-value" style="color: #94a3b8;">Nenhuma</div>
                <?php endif; ?>
            </div>
        </div>

        <!-- Tabela de Simulações -->
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Lista de Simulações</h2>
                <p class="card-subtitle">Todas as simulações criadas pela equipa</p>
            </div>

            <?php if (count($rows) > 0): ?>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Descrição</th>
                                <th>Início</th>
                                <th>Criador</th>
                                <th>Estado</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($rows as $sim): ?>
                                <tr>
                                    <td><strong>#<?php echo $sim['idSimulacao']; ?></strong></td>
                                    <td><?php echo htmlspecialchars($sim['Descricao'] ?? ', '); ?></td>
                                    <td><?php echo $sim['DataHoraInicio'] ? date('d/m/Y H:i', strtotime($sim['DataHoraInicio'])) : ', '; ?></td>
                                    <td><?php echo htmlspecialchars($sim['CriadorEmail'] ?? ', '); ?></td>
                                    <td>
                                        <?php if ($sim['IsActive'] == 0): ?>
                                            <span class="badge badge-active"><span class="badge-dot"></span> A correr</span>
                                        <?php elseif ($sim['IsActive'] == 1): ?>
                                            <span class="badge badge-inactive"><span class="badge-dot"></span> Terminada</span>
                                        <?php else: ?>
                                            <span class="badge badge-inactive"><span class="badge-dot"></span> Criada</span>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <div class="table-actions">
                                            <?php if ($sim['IsActive'] == -1 && $sim['CriadorEmail'] === $user_email): ?>
                                                <a href="edit_simulation.php?id=<?php echo $sim['idSimulacao']; ?>" class="btn btn-sm btn-secondary" title="Editar">✏️ Editar</a>
                                            <?php endif; ?>
                                            
                                            <?php if ($sim['IsActive'] == -1 && !$tem_ativa && $sim['CriadorEmail'] === $user_email): ?>
                                                <form method="POST" style="display:inline;">
                                                    <input type="hidden" name="action" value="iniciar">
                                                    <input type="hidden" name="id_simulacao" value="<?php echo $sim['idSimulacao']; ?>">
                                                    <button type="submit" class="btn btn-sm btn-success" title="Iniciar" onclick="return confirm('Iniciar simulação #<?php echo $sim['idSimulacao']; ?>?')">▶️ Iniciar</button>
                                                </form>
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
                    <div class="icon">🧪</div>
                    <h3>Nenhuma simulação encontrada</h3>
                    <p>Crie a primeira simulação da equipa para começar.</p>
                    <a href="edit_simulation.php" class="btn btn-primary">＋ Criar Simulação</a>
                </div>
            <?php endif; ?>
        </div>
    </div>

    <div class="footer">
        PISID 2025/26, Grupo 16 · ISCTE-IUL
    </div>
</body>
</html>

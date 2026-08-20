<?php
require_once 'config.php';

// Se já estiver autenticado, redireciona para o dashboard
if (isset($_SESSION['user_email'])) {
    header("Location: dashboard.php");
    exit();
}

$error = '';

// Processar formulário de login
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email'] ?? '');
    
    if (empty($email)) {
        $error = 'Por favor, introduza o seu email.';
    } else {
        $stmt = $conn->prepare("SELECT Nome, Email, Telemovel, Tipo, Equipa FROM utilizador WHERE Email = ?");
        $stmt->bind_param("s", $email);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows === 1) {
            $user = $result->fetch_assoc();
            $_SESSION['user_email'] = $user['Email'];
            $_SESSION['user_nome'] = $user['Nome'];
            $_SESSION['user_tipo'] = $user['Tipo'];
            $_SESSION['user_equipa'] = $user['Equipa'];
            $_SESSION['user_telemovel'] = $user['Telemovel'];
            
            header("Location: dashboard.php");
            exit();
        } else {
            $error = 'Email não encontrado. Verifique as suas credenciais.';
        }
        $stmt->close();
    }
}
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="PISID - Plataforma de gestão de simulações de labirinto. Login.">
    <title>Login, PISID Maze</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="login-wrapper">
        <div class="card login-card">
            <div class="login-logo">
                <div class="icon">🧪</div>
                <h1>PISID Maze</h1>
                <p>Plataforma de Simulação, Grupo 16</p>
            </div>
            
            <?php if ($error): ?>
                <div class="alert alert-error">
                    <span>⚠️</span> <?php echo htmlspecialchars($error); ?>
                </div>
            <?php endif; ?>
            
            <form method="POST" action="index.php" id="login-form">
                <div class="form-group">
                    <label class="form-label" for="email">Email</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        class="form-input" 
                        placeholder="exemplo@iscte-iul.pt"
                        value="<?php echo htmlspecialchars($_POST['email'] ?? ''); ?>"
                        required
                        autofocus
                    >
                    <p class="form-hint">Introduza o email registado na equipa</p>
                </div>
                
                <button type="submit" class="btn btn-primary btn-block" id="btn-login">
                    Entrar
                </button>
            </form>
        </div>
    </div>
    
    <div class="footer">
        PISID 2025/26, Grupo 16 · ISCTE-IUL
    </div>
</body>
</html>

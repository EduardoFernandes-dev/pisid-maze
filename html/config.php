<?php
session_start();

// Configuração da ligação à base de dados MySQL
$db_host = 'localhost';    // PHP corre nativamente no Windows
$db_user = 'aluno';
$db_pass = 'aluno';
$db_name = 'pisid_maze';

$conn = new mysqli($db_host, $db_user, $db_pass, $db_name);

if ($conn->connect_error) {
    die("Erro de ligação à base de dados: " . $conn->connect_error);
}

$conn->set_charset("utf8");

/**
 * Verifica se o utilizador está autenticado.
 * Se não estiver, redireciona para a página de login.
 */
function requireLogin() {
    if (!isset($_SESSION['user_email'])) {
        header("Location: index.php");
        exit();
    }
}

/**
 * Verifica se o utilizador autenticado é administrador (Tipo = 'ADM').
 * Se não for, redireciona para o dashboard.
 */
function requireAdmin() {
    requireLogin();
    if (!isset($_SESSION['user_tipo']) || $_SESSION['user_tipo'] !== 'ADM') {
        header("Location: dashboard.php");
        exit();
    }
}

/**
 * Retorna as iniciais do nome do utilizador para o avatar.
 */
function getIniciais($nome) {
    $partes = explode(' ', $nome);
    $iniciais = strtoupper(substr($partes[0], 0, 1));
    if (count($partes) > 1) {
        $iniciais .= strtoupper(substr(end($partes), 0, 1));
    }
    return $iniciais;
}

/**
 * Verifica se o utilizador atual é admin.
 */
function isAdmin() {
    return isset($_SESSION['user_tipo']) && $_SESSION['user_tipo'] === 'ADM';
}
?>

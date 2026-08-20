package com.maze;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class MazeLoginActivity extends AppCompatActivity {

    private EditText etHost, etUsername, etPassword, etDatabase;
    private Button btnConnect;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_maze_login);

        etHost = findViewById(R.id.etHost);
        etUsername = findViewById(R.id.etUsername);
        etPassword = findViewById(R.id.etPassword);
        etDatabase = findViewById(R.id.etDatabase);
        btnConnect = findViewById(R.id.btnConnect);

        btnConnect.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                attemptLogin();
            }
        });
    }

    private void attemptLogin() {
        final String host = etHost.getText().toString().trim();
        final String username = etUsername.getText().toString().trim();
        final String password = etPassword.getText().toString().trim();
        final String database = etDatabase.getText().toString().trim();

        if (host.isEmpty() || username.isEmpty() || password.isEmpty() || database.isEmpty()) {
            Toast.makeText(this, "Preencha todos os campos!", Toast.LENGTH_SHORT).show();
            return;
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                java.sql.Connection conn = null;
                try {
                    // Invocação do driver JDBC
                    Class.forName("com.mysql.jdbc.Driver");
                    
                    // Configuração da string de conexão JDBC direta
                    String connectionUrl = "jdbc:mysql://" + host + ":3306/" + database + "?useSSL=false&allowPublicKeyRetrieval=true";
                    
                    // A própria tentativa de estabelecer a conexão valida as credenciais
                    conn = java.sql.DriverManager.getConnection(connectionUrl, username, password);

                    if (conn != null) {
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Toast.makeText(MazeLoginActivity.this, "Autenticação JDBC bem-sucedida!", Toast.LENGTH_SHORT).show();
                                Intent intent = new Intent(MazeLoginActivity.this, MainActivity.class);
                                intent.putExtra("host", host);
                                intent.putExtra("database", database);
                                intent.putExtra("username", username);
                                intent.putExtra("password", password);
                                startActivity(intent);
                                finish();
                            }
                        });
                    }

                } catch (Exception e) {
                    Log.e("MazeLogin", "Erro na autenticação JDBC: " + e.getMessage());
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            Toast.makeText(MazeLoginActivity.this, "Falha na autenticação: credenciais inválidas ou erro de rede", Toast.LENGTH_LONG).show();
                        }
                    });
                } finally {
                    try { if (conn != null) conn.close(); } catch (Exception e) {}
                }
            }
        }).start();
    }
}

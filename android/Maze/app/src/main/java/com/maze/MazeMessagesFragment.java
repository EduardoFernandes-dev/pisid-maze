package com.maze;

import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.maze.models.Mensagem;

import java.util.ArrayList;
import java.util.List;

public class MazeMessagesFragment extends Fragment {

    private static final String ARG_HOST = "host";
    private static final String ARG_DATABASE = "database";
    private static final String ARG_USERNAME = "username";
    private static final String ARG_PASSWORD = "password";

    private String host;
    private String database;
    private String username;
    private String password;
    private RecyclerView rvMessages;
    private MessageAdapter adapter;

    public MazeMessagesFragment() {
        // Required empty public constructor
    }

    public static MazeMessagesFragment newInstance(String host, String database, String username, String password) {
        MazeMessagesFragment fragment = new MazeMessagesFragment();
        Bundle args = new Bundle();
        args.putString(ARG_HOST, host);
        args.putString(ARG_DATABASE, database);
        args.putString(ARG_USERNAME, username);
        args.putString(ARG_PASSWORD, password);
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {
            host = getArguments().getString(ARG_HOST);
            database = getArguments().getString(ARG_DATABASE);
            username = getArguments().getString(ARG_USERNAME);
            password = getArguments().getString(ARG_PASSWORD);
        }
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_maze_messages, container, false);
        rvMessages = view.findViewById(R.id.rvMessages);
        rvMessages.setLayoutManager(new LinearLayoutManager(getContext()));
        adapter = new MessageAdapter(new ArrayList<>());
        rvMessages.setAdapter(adapter);
        return view;
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        fetchMessages();
    }

    private void fetchMessages() {
        new Thread(new Runnable() {
            @Override
            public void run() {
                java.sql.Connection conn = null;
                java.sql.Statement stmt = null;
                java.sql.ResultSet rs = null;
                final List<Mensagem> messages = new ArrayList<>();

                try {
                    Class.forName("com.mysql.jdbc.Driver");
                    String connectionUrl = "jdbc:mysql://" + host + ":3306/" + database + "?useSSL=false&allowPublicKeyRetrieval=true";
                    conn = java.sql.DriverManager.getConnection(connectionUrl, username, password);
                    stmt = conn.createStatement();

                    // Query direta na tabela mensagens do Grupo 16
                    String sql = "SELECT Hora, Sala, Sensor, Leitura, TipoAlerta, Msg FROM mensagens ORDER BY Hora DESC";
                    rs = stmt.executeQuery(sql);

                    while (rs.next()) {
                        Mensagem msg = new Mensagem();
                        msg.setHora(rs.getString("Hora"));
                        msg.setSala(rs.getInt("Sala"));
                        msg.setSensor(rs.getString("Sensor"));
                        msg.setLeitura(rs.getString("Leitura"));
                        msg.setTipoAlerta(rs.getString("TipoAlerta"));
                        msg.setMsg(rs.getString("Msg"));
                        messages.add(msg);
                    }

                    if (getActivity() != null) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                adapter.setMessages(messages);
                            }
                        });
                    }

                } catch (Exception e) {
                    Log.e("MazeMessages", "Erro JDBC: " + e.getMessage());
                    if (getActivity() != null) {
                        getActivity().runOnUiThread(() -> Toast.makeText(getContext(), "Erro JDBC: " + e.getMessage(), Toast.LENGTH_LONG).show());
                    }
                } finally {
                    try { if (rs != null) rs.close(); } catch (Exception e) {}
                    try { if (stmt != null) stmt.close(); } catch (Exception e) {}
                    try { if (conn != null) conn.close(); } catch (Exception e) {}
                }
            }
        }).start();
    }
}

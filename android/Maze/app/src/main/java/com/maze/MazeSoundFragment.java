package com.maze;

import android.graphics.Color;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.Legend;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.components.YAxis;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;
import com.github.mikephil.charting.interfaces.datasets.ILineDataSet;
import com.maze.models.SoundData;

import java.util.ArrayList;
import java.util.List;

public class MazeSoundFragment extends Fragment {

    private static final String ARG_HOST = "host";
    private static final String ARG_DATABASE = "database";
    private static final String ARG_USERNAME = "username";
    private static final String ARG_PASSWORD = "password";

    private String host;
    private String database;
    private String username;
    private String password;
    private LineChart lineChart;

    public MazeSoundFragment() {
        // Required empty public constructor
    }

    public static MazeSoundFragment newInstance(String host, String database, String username, String password) {
        MazeSoundFragment fragment = new MazeSoundFragment();
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
        View view = inflater.inflate(R.layout.fragment_maze_sound, container, false);
        lineChart = view.findViewById(R.id.lineChartSound);
        return view;
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        setupChart();
        fetchSoundData();
    }

    private void setupChart() {
        lineChart.getDescription().setEnabled(false);
        lineChart.setTouchEnabled(true);
        lineChart.setDragEnabled(true);
        lineChart.setScaleEnabled(true);
        lineChart.setPinchZoom(true);

        XAxis xAxis = lineChart.getXAxis();
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        xAxis.setDrawGridLines(false);
        xAxis.setGranularity(1f);

        YAxis leftAxis = lineChart.getAxisLeft();
        leftAxis.setAxisMinimum(0f);
        lineChart.getAxisRight().setEnabled(false);

        Legend legend = lineChart.getLegend();
        legend.setForm(Legend.LegendForm.LINE);
        legend.setTextSize(12f);
        
        lineChart.setNoDataText("A carregar dados do MySQL via JDBC...");
    }

    private void fetchSoundData() {
        new Thread(new Runnable() {
            @Override
            public void run() {
                java.sql.Connection conn = null;
                java.sql.Statement stmt = null;
                java.sql.ResultSet rs = null;
                final List<SoundData> soundList = new ArrayList<>();
                float threshold = 0f;

                try {
                    Class.forName("com.mysql.jdbc.Driver");
                    String connectionUrl = "jdbc:mysql://" + host + ":3306/" + database + "?useSSL=false&allowPublicKeyRetrieval=true";
                    conn = java.sql.DriverManager.getConnection(connectionUrl, username, password);
                    stmt = conn.createStatement();

                    // 1. Procurar limite na tabela setupmaze
                    rs = stmt.executeQuery("SELECT somVarTol FROM setupmaze LIMIT 1");
                    if (rs.next()) {
                        threshold = rs.getFloat("somVarTol");
                    }
                    rs.close();

                    // 2. Procurar leituras na tabela som
                    rs = stmt.executeQuery("SELECT Som, Hora FROM som WHERE idSimulacao = (SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1) ORDER BY Hora ASC");
                    while (rs.next()) {
                        SoundData data = new SoundData();
                        data.setValue(rs.getFloat("Som"));
                        data.setHora(rs.getString("Hora"));
                        soundList.add(data);
                    }

                    final float finalThreshold = threshold;
                    if (getActivity() != null) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                updateChart(soundList, finalThreshold);
                            }
                        });
                    }

                } catch (Exception e) {
                    Log.e("MazeSound", "Erro JDBC: " + e.getMessage());
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

    private void updateChart(List<SoundData> soundList, float threshold) {
        if (soundList == null || soundList.isEmpty()) {
            lineChart.setNoDataText("Sem dados de som no MySQL.");
            lineChart.invalidate();
            return;
        }

        ArrayList<Entry> soundEntries = new ArrayList<>();
        ArrayList<Entry> limitEntries = new ArrayList<>();

        for (int i = 0; i < soundList.size(); i++) {
            SoundData data = soundList.get(i);
            soundEntries.add(new Entry(i, data.getValue()));
            limitEntries.add(new Entry(i, threshold));
        }

        LineDataSet soundSet = new LineDataSet(soundEntries, "Nível de Som (Leitura)");
        soundSet.setColor(Color.BLUE);
        soundSet.setLineWidth(2f);
        soundSet.setCircleColor(Color.BLUE);
        soundSet.setDrawCircles(true);
        soundSet.setDrawValues(false);

        LineDataSet limitSet = new LineDataSet(limitEntries, "Limite (" + threshold + ")");
        limitSet.setColor(Color.RED);
        limitSet.setLineWidth(2f);
        limitSet.setDrawCircles(false);
        limitSet.setDrawValues(false);
        limitSet.enableDashedLine(10f, 5f, 0f);

        ArrayList<ILineDataSet> dataSets = new ArrayList<>();
        dataSets.add(soundSet);
        dataSets.add(limitSet);

        lineChart.setData(new LineData(dataSets));
        lineChart.invalidate();
    }
}

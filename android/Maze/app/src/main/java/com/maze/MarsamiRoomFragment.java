package com.maze;

import android.annotation.SuppressLint;
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

import com.github.mikephil.charting.charts.BarChart;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.data.BarData;
import com.github.mikephil.charting.data.BarDataSet;
import com.github.mikephil.charting.data.BarEntry;
import com.github.mikephil.charting.formatter.IndexAxisValueFormatter;
import com.github.mikephil.charting.interfaces.datasets.IBarDataSet;
import com.maze.models.RoomData;

import java.util.ArrayList;
import java.util.List;

public class MarsamiRoomFragment extends Fragment {

    private static final String ARG_HOST = "host";
    private static final String ARG_DATABASE = "database";
    private static final String ARG_USERNAME = "username";
    private static final String ARG_PASSWORD = "password";

    private String host;
    private String database;
    private String username;
    private String password;

    private BarChart barChart;

    public MarsamiRoomFragment() {
        // Required empty public constructor
    }

    public static MarsamiRoomFragment newInstance(String host, String database, String username, String password) {
        MarsamiRoomFragment fragment = new MarsamiRoomFragment();
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

    @SuppressLint("MissingInflatedId")
    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_marsami_room, container, false);
        barChart = view.findViewById(R.id.barChart);
        setupChart();
        return view;
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        fetchRoomData();
    }

    private void setupChart() {
        barChart.getDescription().setEnabled(false);
        barChart.setPinchZoom(false);
        barChart.setDrawBarShadow(false);
        barChart.setDrawGridBackground(false);

        XAxis xAxis = barChart.getXAxis();
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        xAxis.setDrawGridLines(false);
        xAxis.setDrawAxisLine(true);
        xAxis.setGranularity(1f);
        xAxis.setGranularityEnabled(true);
        xAxis.setCenterAxisLabels(true);

        barChart.getAxisLeft().setDrawGridLines(true);
        barChart.getAxisLeft().setAxisMinimum(0f);
        barChart.getAxisLeft().setGranularity(1f);
        barChart.getAxisRight().setEnabled(false);

        barChart.setFitBars(true);
        barChart.animateY(1500);
        barChart.setNoDataText("A carregar dados do MySQL via JDBC...");
    }

    private void fetchRoomData() {
        new Thread(new Runnable() {
            @Override
            public void run() {
                java.sql.Connection conn = null;
                java.sql.Statement stmt = null;
                java.sql.ResultSet rs = null;
                final List<RoomData> roomDataList = new ArrayList<>();

                try {
                    Class.forName("com.mysql.jdbc.Driver");
                    String connectionUrl = "jdbc:mysql://" + host + ":3306/" + database + "?useSSL=false&allowPublicKeyRetrieval=true";
                    conn = java.sql.DriverManager.getConnection(connectionUrl, username, password);

                    String sql = "SELECT idSala, nrMarsamisEven, nrMarsamisOdd FROM ocupacaolabirinto WHERE idSimulacao = (SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1) ORDER BY idSala ASC";
                    stmt = conn.createStatement();
                    rs = stmt.executeQuery(sql);

                    while (rs.next()) {
                        RoomData room = new RoomData();
                        room.setRoom(rs.getString("idSala"));
                        room.setNumberEven(rs.getString("nrMarsamisEven"));
                        room.setNumberOdd(rs.getString("nrMarsamisOdd"));
                        roomDataList.add(room);
                    }

                    if (getActivity() != null) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                updateChart(roomDataList);
                            }
                        });
                    }

                } catch (Exception e) {
                    Log.e("MarsamiRoomFragment", "Erro JDBC: " + e.getMessage());
                    if (getActivity() != null) {
                        getActivity().runOnUiThread(() -> Toast.makeText(getContext(), "Erro JDBC Direto: " + e.getMessage(), Toast.LENGTH_LONG).show());
                    }
                } finally {
                    try { if (rs != null) rs.close(); } catch (Exception e) {}
                    try { if (stmt != null) stmt.close(); } catch (Exception e) {}
                    try { if (conn != null) conn.close(); } catch (Exception e) {}
                }
            }
        }).start();
    }

    private void updateChart(List<RoomData> roomDataList) {
        if (roomDataList == null || roomDataList.isEmpty()) {
            barChart.clear();
            barChart.invalidate();
            barChart.setNoDataText("Nenhum registo retornado pelo MySQL.");
            return;
        }

        ArrayList<BarEntry> entriesEven = new ArrayList<>();
        ArrayList<BarEntry> entriesOdd = new ArrayList<>();
        ArrayList<String> roomLabels = new ArrayList<>();

        for (int i = 0; i < roomDataList.size(); i++) {
            RoomData room = roomDataList.get(i);
            float x = i;

            float evenValue = 0f;
            try { evenValue = Float.parseFloat(room.getNumberEven()); } catch (Exception e) {}

            float oddValue = 0f;
            try { oddValue = Float.parseFloat(room.getNumberOdd()); } catch (Exception e) {}

            entriesEven.add(new BarEntry(x, evenValue));
            entriesOdd.add(new BarEntry(x, oddValue));
            roomLabels.add("Sala " + room.getRoom());
        }

        BarDataSet setEven = new BarDataSet(entriesEven, "Nº Par");
        setEven.setColor(Color.BLUE);
        setEven.setDrawValues(true);

        BarDataSet setOdd = new BarDataSet(entriesOdd, "Nº Ímpar");
        setOdd.setColor(Color.RED);
        setOdd.setDrawValues(true);

        ArrayList<IBarDataSet> dataSets = new ArrayList<>();
        dataSets.add(setEven);
        dataSets.add(setOdd);

        BarData barData = new BarData(dataSets);
        float groupSpace = 0.08f;
        float barSpace = 0.02f;
        float barWidth = 0.44f;

        barData.setBarWidth(barWidth);
        float startX = 0f;
        barChart.getXAxis().setAxisMinimum(startX);
        barChart.getXAxis().setAxisMaximum(startX + barData.getGroupWidth(groupSpace, barSpace) * roomDataList.size());

        barData.groupBars(startX, groupSpace, barSpace);

        XAxis xAxis = barChart.getXAxis();
        xAxis.setValueFormatter(new IndexAxisValueFormatter(roomLabels));
        xAxis.setLabelCount(roomLabels.size(), false);

        barChart.setData(barData);
        barChart.invalidate();
    }
}

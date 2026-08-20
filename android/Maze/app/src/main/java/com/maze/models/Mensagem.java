package com.maze.models;

import com.google.gson.annotations.SerializedName;

public class Mensagem {
    @SerializedName("Hora")
    private String hora;

    @SerializedName("Sala")
    private int sala;

    @SerializedName("Sensor")
    private String sensor;

    @SerializedName("Leitura")
    private String leitura;

    @SerializedName("TipoAlerta")
    private String tipoAlerta;

    @SerializedName("Msg")
    private String msg;

    public Mensagem() {}

    public String getHora() { return hora; }
    public int getSala() { return sala; }
    public String getSensor() { return sensor; }
    public String getLeitura() { return leitura; }
    public String getTipoAlerta() { return tipoAlerta; }
    public String getMsg() { return msg; }

    public void setHora(String hora) { this.hora = hora; }
    public void setSala(int sala) { this.sala = sala; }
    public void setSensor(String sensor) { this.sensor = sensor; }
    public void setLeitura(String leitura) { this.leitura = leitura; }
    public void setTipoAlerta(String tipoAlerta) { this.tipoAlerta = tipoAlerta; }
    public void setMsg(String msg) { this.msg = msg; }
}

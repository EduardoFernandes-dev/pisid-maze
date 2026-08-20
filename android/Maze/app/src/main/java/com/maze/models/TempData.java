package com.maze.models;

import com.google.gson.annotations.SerializedName;

public class TempData {

    @SerializedName("Leitura")
    private float value;

    @SerializedName("Hora")
    private String hora;

    public TempData() {
    }

    public TempData(float value, String hora) {
        this.value = value;
        this.hora = hora;
    }

    public float getValue() {
        return value;
    }

    public String getHora() {
        return hora;
    }

    public void setValue(float value) {
        this.value = value;
    }

    public void setHora(String hora) {
        this.hora = hora;
    }
}

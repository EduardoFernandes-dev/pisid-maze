package com.maze;

import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.maze.models.Mensagem;

import java.util.List;

public class MessageAdapter extends RecyclerView.Adapter<MessageAdapter.MessageViewHolder> {

    private List<Mensagem> messages;

    public MessageAdapter(List<Mensagem> messages) {
        this.messages = messages;
    }

    @NonNull
    @Override
    public MessageViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_message, parent, false);
        return new MessageViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull MessageViewHolder holder, int position) {
        Mensagem msg = messages.get(position);

        holder.tvSensor.setText(msg.getSensor());
        holder.tvTime.setText(msg.getHora());
        holder.tvSala.setText("Sala: " + msg.getSala());
        holder.tvLeitura.setText("Leitura: " + msg.getLeitura());
        holder.tvText.setText(msg.getMsg());
        holder.tvTipo.setText("Tipo: " + msg.getTipoAlerta());

        // Lógica de Destaque Visual (Grupo 16)
        if (msg.getTipoAlerta() != null && 
           (msg.getTipoAlerta().equalsIgnoreCase("Crítico") || 
            msg.getMsg().toLowerCase().contains("limite"))) {
            holder.container.setBackgroundColor(Color.parseColor("#FFCDD2")); // Vermelho claro
            holder.tvText.setTextColor(Color.RED);
            holder.tvTipo.setTextColor(Color.RED);
        } else if (msg.getTipoAlerta() != null && msg.getTipoAlerta().equalsIgnoreCase("Aviso")) {
            holder.container.setBackgroundColor(Color.parseColor("#FFF9C4")); // Amarelo claro
            holder.tvText.setTextColor(Color.BLACK);
            holder.tvTipo.setTextColor(Color.parseColor("#FBC02D"));
        } else {
            holder.container.setBackgroundColor(Color.WHITE);
            holder.tvText.setTextColor(Color.BLACK);
            holder.tvTipo.setTextColor(Color.GRAY);
        }
    }

    @Override
    public int getItemCount() {
        return messages == null ? 0 : messages.size();
    }

    public void setMessages(List<Mensagem> messages) {
        this.messages = messages;
        notifyDataSetChanged();
    }

    static class MessageViewHolder extends RecyclerView.ViewHolder {
        TextView tvSensor, tvTime, tvSala, tvLeitura, tvText, tvTipo;
        LinearLayout container;

        public MessageViewHolder(@NonNull View itemView) {
            super(itemView);
            tvSensor = itemView.findViewById(R.id.tvMsgSensor);
            tvTime = itemView.findViewById(R.id.tvMsgTime);
            tvSala = itemView.findViewById(R.id.tvMsgSala);
            tvLeitura = itemView.findViewById(R.id.tvMsgLeitura);
            tvText = itemView.findViewById(R.id.tvMsgText);
            tvTipo = itemView.findViewById(R.id.tvMsgTipo);
            container = itemView.findViewById(R.id.messageContainer);
        }
    }
}

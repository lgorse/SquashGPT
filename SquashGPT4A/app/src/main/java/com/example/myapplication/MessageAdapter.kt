package com.example.squashgpt4a

import android.graphics.Color
import android.graphics.Typeface
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class MessageAdapter(val messages: MutableList<Message>) :
    RecyclerView.Adapter<MessageAdapter.MessageViewHolder>() {

    companion object {
        private const val VIEW_TYPE_USER = 1
        private const val VIEW_TYPE_ASSISTANT = 2
    }

    class MessageViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val messageText: TextView = view.findViewById(R.id.messageText)

        fun bind(message: Message) {
            if (message.isLoading) {
                // Display loading indicator
                messageText.text = when (message.loadingType) {
                    LoadingType.SQUASHGPT -> "🤔 SquashGPT thinking..."
                    LoadingType.API -> "⚡ API processing..."
                    else -> "Loading..."
                }
                messageText.setTextColor(Color.GRAY)
                messageText.setTypeface(null, Typeface.ITALIC)
            } else {
                // Display normal message
                messageText.text = message.text
                messageText.setTextColor(if (message.isUser) Color.WHITE else Color.BLACK)
                messageText.setTypeface(null, Typeface.NORMAL)
            }

            // Your existing bubble styling
        }
    }

    override fun getItemViewType(position: Int): Int {
        return if (messages[position].isUser) VIEW_TYPE_USER else VIEW_TYPE_ASSISTANT
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MessageViewHolder {
        val layoutId = if (viewType == VIEW_TYPE_USER) {
            R.layout.item_message_user
        } else {
            R.layout.item_message_assistant
        }
        val view = LayoutInflater.from(parent.context).inflate(layoutId, parent, false)
        return MessageViewHolder(view)
    }

    override fun onBindViewHolder(holder: MessageViewHolder, position: Int) {
        holder.bind(messages[position])
    }

    override fun getItemCount() = messages.size
}
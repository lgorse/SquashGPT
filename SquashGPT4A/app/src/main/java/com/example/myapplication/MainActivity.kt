package com.example.squashgpt4a

import android.os.Bundle
import android.view.View
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ProgressBar
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var viewModel: ChatViewModel
    private lateinit var adapter: MessageAdapter
    private lateinit var recyclerView: RecyclerView
    private lateinit var messageInput: EditText
    private lateinit var sendButton: ImageButton
    private lateinit var findBookingsButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize ViewModel
        viewModel = ViewModelProvider(this)[ChatViewModel::class.java]

        // Initialize views
        recyclerView = findViewById(R.id.recyclerView)
        messageInput = findViewById(R.id.messageInput)
        sendButton = findViewById(R.id.sendButton)
        findBookingsButton = findViewById(R.id.findBookingsButton)



        // Setup RecyclerView
        adapter = MessageAdapter(mutableListOf())
        recyclerView.adapter = adapter
        recyclerView.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }

        // Observe messages
        lifecycleScope.launch {
            viewModel.messages.collect { messages ->
                adapter.messages.clear()
                adapter.messages.addAll(messages)
                adapter.notifyDataSetChanged()
                if (adapter.itemCount > 0) {
                    recyclerView.scrollToPosition(adapter.itemCount - 1)
                }

                // Hide button once messages start appearing
                if (messages.isNotEmpty()) {
                    findBookingsButton.visibility = View.GONE
                }
            }
        }

        // Find bookings button click
        findBookingsButton.setOnClickListener {
            viewModel.sendMessage(findBookingsButton.text as String)
            findBookingsButton.visibility = View.GONE
        }

        // Send button click
        sendButton.setOnClickListener {
            val text = messageInput.text.toString()
            if (text.isNotBlank()) {
                viewModel.sendMessage(text)
                messageInput.text.clear()
            }
        }
    }
}
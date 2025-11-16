package com.example.squashgpt

import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.squashgpt.data.api.RetrofitClient
import com.example.squashgpt.data.api.SquashAPI
import com.example.squashgpt.databinding.ActivityMainBinding
import com.example.squashgpt.domain.model.LoadingState
import com.example.squashgpt.presentation.ChatAdapter
import com.example.squashgpt.presentation.ChatViewModel

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var adapter: ChatAdapter
    private val userId = "user_${System.currentTimeMillis()}"
    private var shouldScrollToTop = false

    private val viewModel: ChatViewModel by viewModels {
        ChatViewModelFactory(RetrofitClient.apiService, userId)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupToolbar()
        setupRecyclerView()
        setupObservers()
        setupListeners()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_clear -> {
                viewModel.clearChat()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    private fun setupToolbar() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.title = "SquashGPT"
    }

    private fun setupRecyclerView() {
        adapter = ChatAdapter()
        binding.recyclerViewMessages.apply {
            layoutManager = LinearLayoutManager(this@MainActivity).apply {
                stackFromEnd = true
            }
            adapter = this@MainActivity.adapter
        }
    }

    private fun setupObservers() {
        viewModel.messages.observe(this) { messages ->
            adapter.submitList(messages) {
                // After submitList completes, scroll to top if flag is set
                if (shouldScrollToTop && messages.isNotEmpty()) {
                    val layoutManager = binding.recyclerViewMessages.layoutManager as? LinearLayoutManager
                    layoutManager?.scrollToPositionWithOffset(messages.size - 1, 0)
                    shouldScrollToTop = false
                }
            }

            // Show/hide empty state
            if (messages.isEmpty()) {
                binding.emptyStateView.visibility = View.VISIBLE
                binding.recyclerViewMessages.visibility = View.GONE
            } else {
                binding.emptyStateView.visibility = View.GONE
                binding.recyclerViewMessages.visibility = View.VISIBLE
            }
        }

        viewModel.loadingState.observe(this) { state ->
            println("MainActivity - LoadingState changed to: ${state::class.simpleName}")
            when (state) {
                is LoadingState.Idle -> {
                    binding.statusBar.visibility = View.GONE
                    binding.editTextMessage.isEnabled = true
                    binding.buttonSend.isEnabled = true
                }
                is LoadingState.ApiProcessing -> {
                    binding.statusBar.visibility = View.VISIBLE
                    binding.statusText.text = getString(R.string.status_processing)
                    binding.statusBar.setBackgroundColor(ContextCompat.getColor(this, R.color.openai_green))
                    binding.editTextMessage.isEnabled = false
                    binding.buttonSend.isEnabled = false
                }
                is LoadingState.CallingOpenAI -> {
                    binding.statusBar.visibility = View.VISIBLE
                    binding.statusText.text = getString(R.string.status_thinking)
                    binding.statusBar.setBackgroundColor(ContextCompat.getColor(this, R.color.openai_green))
                    binding.editTextMessage.isEnabled = false
                    binding.buttonSend.isEnabled = false
                }
                is LoadingState.StreamingResponse -> {
                    binding.statusBar.visibility = View.VISIBLE
                    binding.statusText.text = getString(R.string.status_responding)
                    binding.statusBar.setBackgroundColor(ContextCompat.getColor(this, R.color.openai_green))
                    binding.editTextMessage.isEnabled = false
                    binding.buttonSend.isEnabled = false
                }
                is LoadingState.Success -> {
                    // Will transition to Idle automatically
                }
                is LoadingState.Error -> {
                    binding.statusBar.visibility = View.GONE
                    binding.editTextMessage.isEnabled = true
                    binding.buttonSend.isEnabled = true
                    Toast.makeText(this, state.message, Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private fun setupListeners() {
        binding.buttonSend.setOnClickListener {
            val message = binding.editTextMessage.text.toString()
            if (message.isNotBlank()) {
                shouldScrollToTop = true
                viewModel.sendMessage(message)
                binding.editTextMessage.text?.clear()
            }
        }
    }

    class ChatViewModelFactory(
        private val api: SquashAPI,
        private val userId: String
    ) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(ChatViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return ChatViewModel(api, userId) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}

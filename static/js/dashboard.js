document.addEventListener("DOMContentLoaded", () => {
  const chatMessages = document.getElementById("chatMessages")
  const queryInput = document.getElementById("queryInput")
  const sendBtn = document.getElementById("sendBtn")
  const suggestionsDropdown = document.getElementById("suggestions")

  let typingTimer
  const doneTypingInterval = 300 // 300ms delay after typing stops

  // Function to add a message to the chat
  function addMessage(content, isUser = false) {
    const messageDiv = document.createElement("div")
    messageDiv.className = isUser ? "message user" : "message bot"

    const messageContent = document.createElement("div")
    messageContent.className = "message-content"
    messageContent.textContent = content

    messageDiv.appendChild(messageContent)
    chatMessages.appendChild(messageDiv)

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight
  }

  // Function to send the query to the server
  function sendQuery() {
    const query = queryInput.value.trim()

    if (query === "") return

    // Add user message to chat
    addMessage(query, true)

    // Show loading indicator
    const loadingDiv = document.createElement("div")
    loadingDiv.className = "message bot"
    const loadingContent = document.createElement("div")
    loadingContent.className = "message-content"
    loadingContent.textContent = "Thinking..."
    loadingDiv.appendChild(loadingContent)
    chatMessages.appendChild(loadingDiv)

    // Send query to server
    const formData = new FormData()
    formData.append("query", query)

    fetch("/search", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        // Remove loading indicator
        chatMessages.removeChild(loadingDiv)

        // Add bot response to chat
        addMessage(data.response)
      })
      .catch((error) => {
        console.error("Error:", error)
        // Remove loading indicator
        chatMessages.removeChild(loadingDiv)

        // Add error message to chat
        addMessage("Sorry, there was an error processing your request.")
      })

    // Clear input field
    queryInput.value = ""

    // Hide suggestions dropdown
    suggestionsDropdown.style.display = "none"
  }

  // Function to get query suggestions
  function getSuggestions() {
    const query = queryInput.value.trim()

    if (query === "") {
      suggestionsDropdown.style.display = "none"
      return
    }

    fetch(`/suggest?query=${encodeURIComponent(query)}`)
      .then((response) => response.json())
      .then((suggestions) => {
        suggestionsDropdown.innerHTML = ""

        if (suggestions.length === 0) {
          suggestionsDropdown.style.display = "none"
          return
        }

        suggestions.forEach((suggestion) => {
          const item = document.createElement("div")
          item.className = "suggestion-item"
          item.textContent = suggestion

          item.addEventListener("click", () => {
            queryInput.value = suggestion
            suggestionsDropdown.style.display = "none"
            queryInput.focus()
          })

          suggestionsDropdown.appendChild(item)
        })

        suggestionsDropdown.style.display = "block"
      })
      .catch((error) => {
        console.error("Error:", error)
        suggestionsDropdown.style.display = "none"
      })
  }

  // Event listeners
  queryInput.addEventListener("keyup", (e) => {
    clearTimeout(typingTimer)

    if (e.key === "Enter") {
      suggestionsDropdown.style.display = "none"
      sendQuery()
      return
    }

    typingTimer = setTimeout(getSuggestions, doneTypingInterval)
  })

  queryInput.addEventListener("keydown", () => {
    clearTimeout(typingTimer)
  })

  sendBtn.addEventListener("click", () => {
    suggestionsDropdown.style.display = "none"
    sendQuery()
  })

  // Hide suggestions dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (e.target !== queryInput && e.target !== suggestionsDropdown) {
      suggestionsDropdown.style.display = "none"
    }
  })
})


document.addEventListener("DOMContentLoaded", () => {
  const chatMessages = document.getElementById("chatMessages")
  const queryInput = document.getElementById("queryInput")
  const sendBtn = document.getElementById("sendBtn")
  const suggestionsList = document.getElementById("suggestionsList")

  // Initial suggestions - we'll only show 3 at a time
  const allSuggestions = [
    "What is mental health?",
    "How to find mental health professional?",
    "What treatment options are available?",
    "Who does mental illness affect?",
    "What causes mental illness?",
    "Can people with mental illness recover?",
    "How to help someone with mental health issues?",
  ]

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

  // Function to update suggestions - limit to 3 random suggestions
  function updateSuggestions(suggestions) {
    suggestionsList.innerHTML = ""

    // If we have specific suggestions, use those (limited to 3)
    // Otherwise, pick 3 random ones from our initial set
    let displaySuggestions = []

    if (suggestions && suggestions.length > 0) {
      displaySuggestions = suggestions.slice(0, 3)
    } else {
      // Get 3 random suggestions from allSuggestions
      const shuffled = [...allSuggestions].sort(() => 0.5 - Math.random())
      displaySuggestions = shuffled.slice(0, 3)
    }

    displaySuggestions.forEach((suggestion) => {
      const item = document.createElement("div")
      item.className = "suggestion-item"
      item.textContent = suggestion

      item.addEventListener("click", () => {
        queryInput.value = suggestion
        queryInput.focus()
      })

      suggestionsList.appendChild(item)
    })
  }

  // Function to get query suggestions from server
  function getSuggestions() {
    const query = queryInput.value.trim()

    if (query === "") {
      // Show 3 random suggestions from our initial set
      updateSuggestions([])
      return
    }

    fetch(`/suggest?query=${encodeURIComponent(query)}`)
      .then((response) => response.json())
      .then((suggestions) => {
        updateSuggestions(suggestions)
      })
      .catch((error) => {
        console.error("Error:", error)
        updateSuggestions([])
      })
  }

  // Handle common greetings
  function handleCommonGreetings(query) {
    const greetings = {
      hello: "Hello! How can I help you with mental health information today?",
      hi: "Hi there! Feel free to ask me any mental health questions.",
      hey: "Hey! I'm here to provide mental health information. What would you like to know?",
      "good morning": "Good morning! How can I assist you with mental health topics today?",
      "good afternoon": "Good afternoon! What mental health information are you looking for?",
      "good evening": "Good evening! I'm here to help with your mental health questions.",
      "how are you":
        "I'm functioning well, thank you! I'm here to provide mental health information. How can I help you?",
      thanks: "You're welcome! Is there anything else you'd like to know about mental health?",
      "thank you": "You're welcome! Feel free to ask if you have more questions about mental health.",
      bye: "Goodbye! Take care of your mental health, and feel free to return if you have more questions.",
      goodbye: "Goodbye! Remember that mental well-being is important. Come back anytime you need information.",
    }

    const lowercaseQuery = query.toLowerCase()

    for (const greeting in greetings) {
      if (lowercaseQuery === greeting || lowercaseQuery.startsWith(greeting + " ")) {
        return greetings[greeting]
      }
    }

    return null
  }

  // Function to send the query to the server
  function sendQuery() {
    const query = queryInput.value.trim()

    if (query === "") return

    // Add user message to chat
    addMessage(query, true)

    // Check for common greetings first
    const greetingResponse = handleCommonGreetings(query)

    if (greetingResponse) {
      // If it's a greeting, respond immediately
      addMessage(greetingResponse)
      queryInput.value = ""
      // Update suggestions after clearing input
      updateSuggestions([])
      return
    }

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

    // Update suggestions after clearing input
    updateSuggestions([])
  }

  // Initialize suggestions with 3 random ones
  updateSuggestions([])

  // Event listeners
  queryInput.addEventListener("input", () => {
    getSuggestions()
  })

  queryInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") {
      sendQuery()
    }
  })

  sendBtn.addEventListener("click", () => {
    sendQuery()
  })

  // Focus input on page load
  queryInput.focus()
})


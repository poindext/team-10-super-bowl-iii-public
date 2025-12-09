const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");

function addMessage(content, sender = "bot") {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.innerText = content;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addMeta(content) {
  const div = document.createElement("div");
  div.className = "meta";
  div.innerText = content;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage(evt) {
  evt.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  addMessage(text, "user");
  inputEl.value = "";
  inputEl.disabled = true;
  formEl.querySelector("button").disabled = true;
  addMessage("Thinking...", "bot");

  try {
    const resp = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!resp.ok) {
      const msg = await resp.text();
      throw new Error(msg || "Request failed");
    }

    const data = await resp.json();
    const last = messagesEl.lastChild;
    if (last && last.classList && last.classList.contains("bot")) {
      last.innerText = data.reply || "(no content)";
    } else {
      addMessage(data.reply || "(no content)", "bot");
    }
    // Tool metadata removed from UI for cleaner interface
    // All tool execution happens server-side securely
  } catch (err) {
    const last = messagesEl.lastChild;
    if (last && last.classList && last.classList.contains("bot")) {
      last.innerText = `Error: ${err.message}`;
    } else {
      addMessage(`Error: ${err.message}`, "bot");
    }
  } finally {
    inputEl.disabled = false;
    formEl.querySelector("button").disabled = false;
    inputEl.focus();
  }
}

formEl.addEventListener("submit", sendMessage);

// Initial welcome
addMessage("Hi! Ask me about clinical trials (e.g., 'trials for diabetes').");


const API_ENDPOINT = "http://192.168.1.47:8000/agent-chat";

const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");

let sessionId = createSessionId();
let loadingNode = null;

appendMessage("system", "已建立新会话，可直接提问。");

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message);
  messageInput.value = "";
  setSending(true);
  loadingNode = appendMessage("assistant", "正在思考中...");

  try {
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: {
        accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`请求失败：${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    sessionId = result.session_id || sessionId;
    const replyText = parseReply(result.reply);
    replaceMessage(loadingNode, replyText || "未返回可展示内容。");
  } catch (error) {
    replaceMessage(
      loadingNode,
      `请求出错：${error instanceof Error ? error.message : "未知异常"}`
    );
  } finally {
    setSending(false);
  }
});

function parseReply(reply) {
  if (typeof reply !== "string") {
    return "";
  }

  const plain = reply.trim();
  if (!plain) {
    return "";
  }

  // Try standard JSON first.
  try {
    const parsed = JSON.parse(plain);
    if (Array.isArray(parsed)) {
      const textPart = parsed.find((item) => item && item.type === "text");
      if (textPart && typeof textPart.text === "string") {
        return textPart.text;
      }
    }
  } catch {
    // Ignore and fallback to Python-like string parser.
  }

  // Fallback: parse Python repr-style payload like:
  // [{'text': '...', 'type': 'text'}]
  const textMatch = plain.match(/'text'\s*:\s*'([\s\S]*?)'\s*,\s*'type'\s*:\s*'text'/);
  if (!textMatch || !textMatch[1]) {
    return "未解析到 text 字段。";
  }

  return textMatch[1]
    .replace(/\\n/g, "\n")
    .replace(/\\'/g, "'")
    .replace(/\\"/g, '"')
    .replace(/\\\\/g, "\\");
}

function appendMessage(role, text) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;

  row.appendChild(bubble);
  chatMessages.appendChild(row);
  scrollToBottom();
  return row;
}

function replaceMessage(node, text) {
  if (!node) {
    appendMessage("assistant", text);
    return;
  }
  const bubble = node.querySelector(".message-bubble");
  if (bubble) {
    bubble.textContent = text;
  }
  scrollToBottom();
}

function setSending(sending) {
  sendButton.disabled = sending;
  messageInput.disabled = sending;
  if (!sending) {
    messageInput.focus();
  }
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function createSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}`;
}

let chats = JSON.parse(localStorage.getItem("grok_chats") || "[]");
function logInitialMessages() {
  const messages = Array.from(document.querySelectorAll("NEW_SELECTOR_HERE"));
  messages.forEach(msg => {
    const text = msg.textContent.trim();
    if (text && text.startsWith("[grok_local]") && !chats.some(c => c.text === text)) {
      const project = text.match(/^\[(.*?)\]/)[1] || "unknown";
      chats.push({ project, text, timestamp: Date.now() });
    }
  });
  localStorage.setItem("grok_chats", JSON.stringify(chats));
  console.log("Initial logged chats:", chats);
}
function logChat(mutations, observer) {
  const messages = Array.from(document.querySelectorAll("NEW_SELECTOR_HERE"));
  messages.forEach(msg => {
    const text = msg.textContent.trim();
    if (text && text.startsWith("[grok_local]") && !chats.some(c => c.text === text)) {
      const project = text.match(/^\[(.*?)\]/)[1] || "unknown";
      chats.push({ project, text, timestamp: Date.now() });
      localStorage.setItem("grok_chats", JSON.stringify(chats));
      console.log("Logged:", text);
    }
  });
}
logInitialMessages();
const observer = new MutationObserver(logChat);
observer.observe(document.body, { childList: true, subtree: true });

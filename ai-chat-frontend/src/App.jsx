import React, { useState, useEffect } from "react";
import Auth from "./Auth";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Welcome back! How can I help you today?" }
  ]);
  const [isGenerating, setIsGenerating] = useState(false);

  // If there is no token, force the user to see the Login screen first
  if (!token) {
    return <Auth onAuthSuccess={() => setToken(localStorage.getItem("token"))} />;
  }

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setMessages([{ role: "assistant", content: "Welcome back! How can I help you today?" }]);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    const userMessage = input;
    setInput("");
    setIsGenerating(true);

    setMessages((prev) => [...prev, { role: "user", content: userMessage }, { role: "assistant", content: "" }]);

    try {
      const encodedPrompt = encodeURIComponent(userMessage);
      
      // NOTICE: We would pass this token to secure endpoints in headers, 
      // but EventSource (SSE) doesn't natively support custom headers.
      // So we append it securely as a URL query parameter string instead!
      const eventSource = new EventSource(
        `http://127.0.0.1:8000/api/chat/stream?prompt=${encodedPrompt}&token=${token}`
      );

      eventSource.onmessage = (event) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content += event.data;
          return updated;
        });
      };

      eventSource.onerror = () => {
        eventSource.close();
        setIsGenerating(false);
      };
    } catch (error) {
      console.error(error);
      setIsGenerating(false);
    }
  };

  return (
    <div style={{ maxWidth: "600px", margin: "50px auto", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>🤖 My Secure AI SaaS</h2>
        <button onClick={handleLogout} style={{ padding: "5px 10px", backgroundColor: "#dc3545", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}>
          Logout
        </button>
      </div>
      
      {/* Chat window UI box */}
      <div style={{ border: "1px solid #ccc", height: "400px", overflowY: "scroll", padding: "15px", marginBottom: "15px", borderRadius: "8px" }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === "user" ? "right" : "left", margin: "10px 0" }}>
            <span style={{ display: "inline-block", padding: "8px 12px", borderRadius: "12px", backgroundColor: msg.role === "user" ? "#007bff" : "#f1f1f1", color: msg.role === "user" ? "#fff" : "#000" }}>
              {msg.content || (isGenerating && index === messages.length - 1 ? "Thinking..." : "")}
            </span>
          </div>
        ))}
      </div>

      <form onSubmit={handleSendMessage} style={{ display: "flex", gap: "10px" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your prompt..."
          style={{ flexGrow: 1, padding: "10px", borderRadius: "4px", border: "1px solid #ccc" }}
          disabled={isGenerating}
        />
        <button type="submit" style={{ padding: "10px 20px", backgroundColor: "#28a745", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }} disabled={isGenerating}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;
import React, { useState } from "react";

function Auth({ onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");

    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/signup";
    
    try {
      const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      if (isLogin) {
        // Save the JWT token securely in the browser
        localStorage.setItem("token", data.access_token);
        // Inform the parent component that login was successful
        onAuthSuccess();
      } else {
        setMessage("Account created successfully! Switching to Login...");
        setIsLogin(true);
        setPassword("");
      }
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div style={{ maxWidth: "400px", margin: "100px auto", padding: "20px", border: "1px solid #ccc", borderRadius: "8px", fontFamily: "sans-serif" }}>
      <h2>{isLogin ? "Login to your SaaS" : "Create SaaS Account"}</h2>
      {message && <p style={{ color: isLogin ? "red" : "green" }}>{message}</p>}
      
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
        <input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ padding: "10px", borderRadius: "4px", border: "1px solid #ccc" }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ padding: "10px", borderRadius: "4px", border: "1px solid #ccc" }}
        />
        <button type="submit" style={{ padding: "10px", backgroundColor: "#007bff", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}>
          {isLogin ? "Sign In" : "Register"}
        </button>
      </form>

      <p style={{ marginTop: "15px", textAlign: "center", fontSize: "14px" }}>
        {isLogin ? "New to the platform? " : "Already have an account? "}
        <span style={{ color: "#007bff", cursor: "pointer", decoration: "underline" }} onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? "Sign Up here" : "Login here"}
        </span>
      </p>
    </div>
  );
}

export default Auth;
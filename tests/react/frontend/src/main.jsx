import React, { useState } from "react";
import { createRoot } from "react-dom/client";

function StreamList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const startStream = async () => {
    setItems([]);
    setLoading(true);
    try {
      const res = await fetch("/stream");
      if (!res.ok) {
        throw new Error(`HTTP error: ${res.status}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (line.trim()) {
            try {
              setItems(items => [...items, JSON.parse(line)]);
            } catch (e) {
              console.error("Failed to parse JSON:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Stream error:", error);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div>
      <button onClick={startStream} disabled={loading}>
        {loading ? "Streaming..." : "Start"}
      </button>
      <ul>
        {items.map(item => (
          <li key={item.id}>{JSON.stringify(item)}</li>
        ))}
      </ul>
    </div>
  );
}

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}
const root = createRoot(rootElement);
root.render(<StreamList />);
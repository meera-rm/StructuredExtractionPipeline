import { useState } from 'react'
import heroImg from './assets/hero.png'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import './App.css'

function App(){

  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleExtract = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${response.status})`);
      }

      setResult(await response.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      id="center"
      style={{
        width: "100%",
        maxWidth: "1000px",
        margin: "0 auto",
        padding: "20px",
        boxSizing: "border-box"
      }}
    >
      <h3
        style={{
          marginTop: "100px",
          marginBottom: "40px",
          fontSize: "32px",
          textAlign: "center"
        }}
      >
        STRUCTURED EXTRACTION PIPELINE
      </h3>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          width: "100%"
        }}
      >
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste your text here..."
          style={{
            width: "100%",
            minHeight: "200px",
            maxHeight: "600px",
            padding: "12px",
            fontSize: "16px",
            resize: "vertical",
            boxSizing: "border-box"
          }}
        />

        <button
          type="button"
          onClick={handleExtract}
          disabled={loading || !text.trim()}
          style={{
            marginTop: "40px",
            padding: "12px 30px",
            fontSize: "24px",
            cursor: loading ? "wait" : "pointer"
          }}
        >
          {loading ? "Extracting..." : "Extract"}
        </button>

        {error && (
          <p style={{ color: "crimson", marginTop: "20px" }}>{error}</p>
        )}

        {result && (
          <pre
            style={{
              width: "100%",
              marginTop: "20px",
              padding: "16px",
              background: "#f5f5f5",
              borderRadius: "8px",
              overflowX: "auto",
              boxSizing: "border-box"
            }}
          >
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </section>
  );
}


export default App

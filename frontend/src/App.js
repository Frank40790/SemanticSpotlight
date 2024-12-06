import React, { useState } from "react";
import axios from "axios";
import "./App.css";

const RelevantTextFinder = () => {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [useHighlight, setUseHighlight] = useState(false);
  const [confidence, setConfidence] = useState(0.5);
  const [numRelevantSentences, setNumRelevantSentences] = useState(5);
  const [sentences, setSentences] = useState([]);
  const [resultHtml, setResultHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please upload a text file.");
      return;
    }

    setSentences([]);
    setResultHtml("");

    setLoading(true);
    setError("");

    const reader = new FileReader();
    reader.onload = async () => {
      const context = reader.result;

      try {
        const response = await axios.post("http://localhost:8000/search/", {
          query,
          n: numRelevantSentences,
          context,
          use_highlight: useHighlight,
          confidence: useHighlight ? confidence : undefined,
        });

        if (useHighlight) {
          setResultHtml(response.data.result_html);
        } else {
          setSentences(response.data.sentences);
        }
      } catch (err) {
        setError(err.response?.data?.detail || "An error occurred.");
      } finally {
        setLoading(false);
      }
    };

    reader.readAsText(file);
  };

  const handleHighlightToggle = () => {
    setUseHighlight((prev) => !prev);
  };

  return (
    <div>
      <h1>Relevant Text Finder</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <input
            type="file"
            accept=".txt"
            onChange={handleFileChange}
          />
        </div>
        <div>
          Query:{" "}
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div>
          <label>Use Highlight:</label>
          <label className="switch">
            <input
              type="checkbox"
              checked={useHighlight}
              onChange={handleHighlightToggle}
            />
            <span className="slider round"></span>
          </label>
        </div>

        {useHighlight ? (
          <div id="confidence_section">
            Confidence (if using Highlight):
            <input
              type="number"
              value={confidence}
              min="0"
              max="1"
              step="0.01"
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
            />
          </div>
        ) : (
          <div id="relevant_sentences_section">
            Number of Relevant Sentences:
            <input
              type="number"
              value={numRelevantSentences}
              min="1"
              onChange={(e) => setNumRelevantSentences(parseInt(e.target.value, 10))}
            />
          </div>
        )}

        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "Submit"}
        </button>
      </form>

      <div>
        {error && <div className="error">{error}</div>}

        {useHighlight ? (
          resultHtml && <div dangerouslySetInnerHTML={{ __html: resultHtml }} />
        ) : (
          sentences.length > 0 && (
            <ul>
              {sentences.map((sentence, index) => (
                <li key={index}>{sentence}</li>
              ))}
            </ul>
          )
        )}
      </div>
    </div>
  );
};

export default RelevantTextFinder;

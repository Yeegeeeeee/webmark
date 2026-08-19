import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useParams } from "react-router-dom";

import { getBookmark } from "../api/bookmarks.js";

export default function BookmarkDetail() {
  const { id } = useParams();
  const [bookmark, setBookmark] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getBookmark(id)
      .then(setBookmark)
      .catch((requestError) => setError(requestError.message));
  }, [id]);

  return (
    <main className="detail-shell">
      <article className="detail-page">
        <button
          className="btn btn-outline-dark btn-sm back-button"
          type="button"
          onClick={() => window.close()}
        >
          Back
        </button>

        {error && <p className="detail-message">{error}</p>}
        {!bookmark && !error && <p className="detail-message">Loading...</p>}

        {bookmark && (
          <>
            <header className="detail-header">
              <span>{bookmark.folder_name}</span>
              <h1>{bookmark.title || bookmark.url}</h1>
              <a href={bookmark.url} target="_blank" rel="noreferrer">
                {bookmark.url}
              </a>
            </header>
            <div className="markdown-content">
              <ReactMarkdown>{bookmark.content || ""}</ReactMarkdown>
            </div>
          </>
        )}
      </article>
    </main>
  );
}

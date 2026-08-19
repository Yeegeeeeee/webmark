import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";

import {
  createBookmark,
  deleteBookmark,
  deleteFolder,
  getBookmarks,
  getFolders,
  renameFolder,
  updateBookmark,
} from "./api/bookmarks.js";
import BookmarkDetail from "./pages/BookmarkDetail.jsx";

const FOLDER_STORAGE_KEY = "webmark-folders";
const BOOKMARKS_PER_PAGE = 5;

function readStoredFolders() {
  try {
    return JSON.parse(localStorage.getItem(FOLDER_STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function BookmarkHome() {
  const [url, setUrl] = useState("");
  const [folder, setFolder] = useState("");
  const [folders, setFolders] = useState(readStoredFolders);
  const [bookmarks, setBookmarks] = useState([]);
  const [recordCount, setRecordCount] = useState(0);
  const [folderFilter, setFolderFilter] = useState("all");
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isEditingFolder, setIsEditingFolder] = useState(false);
  const [editingFolderId, setEditingFolderId] = useState("");
  const [folderEditorMode, setFolderEditorMode] = useState("");
  const [folderName, setFolderName] = useState("");
  const [folderStatus, setFolderStatus] = useState("");
  const [editingBookmarkId, setEditingBookmarkId] = useState(null);
  const [bookmarkTitle, setBookmarkTitle] = useState("");
  const [bookmarkFolderId, setBookmarkFolderId] = useState("");
  const [bookmarkStatus, setBookmarkStatus] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  async function refreshData() {
    const [folderMap, bookmarkList] = await Promise.all([
      getFolders(),
      getBookmarks(),
    ]);
    setFolders(folderMap);
    setBookmarks(bookmarkList);
    setRecordCount(bookmarkList.length);
    setCurrentPage(1);
    localStorage.setItem(FOLDER_STORAGE_KEY, JSON.stringify(folderMap));
  }

  useEffect(() => {
    refreshData().catch(() => {
      // 后端未启动时继续使用 localStorage 中的文件夹缓存。
    });
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setStatus("");

    try {
      const normalizedUrl = /^https?:\/\//i.test(url.trim())
        ? url.trim()
        : `https://${url.trim()}`;
      await createBookmark({ url: normalizedUrl, folder });
      await refreshData();
      setUrl("");
      setFolder("");
      setStatus("保存成功");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsSaving(false);
    }
  }

  function openFolderEditor() {
    if (isEditingFolder) {
      setIsEditingFolder(false);
      return;
    }

    const selectedFolderId = folderFilter === "all" ? "" : folderFilter;
    setEditingFolderId(selectedFolderId);
    setFolderName(folders[selectedFolderId] || "");
    setFolderEditorMode("");
    setFolderStatus("");
    setIsEditingFolder(true);
  }

  async function handleFilterFolder() {
    setFolderStatus("");
    try {
      const bookmarkList = await getBookmarks(
        folderFilter === "all" ? null : folderFilter,
        keyword,
      );
      setBookmarks(bookmarkList);
      setCurrentPage(1);
    } catch (error) {
      setFolderStatus(error.message);
    }
  }

  async function handleSearch(event) {
    event.preventDefault();
    setFolderStatus("");
    try {
      if (!keyword.trim()) {
        const bookmarkList = await getBookmarks();
        setFolderFilter("all");
        setBookmarks(bookmarkList);
        setCurrentPage(1);
        return;
      }

      const bookmarkList = await getBookmarks(
        folderFilter === "all" ? null : folderFilter,
        keyword,
      );
      setBookmarks(bookmarkList);
      setCurrentPage(1);
    } catch (error) {
      setFolderStatus(error.message);
    }
  }

  async function handleRenameFolder() {
    setFolderStatus("");
    try {
      await renameFolder(editingFolderId, folderName);
      await refreshData();
      setIsEditingFolder(false);
    } catch (error) {
      setFolderStatus(error.message);
    }
  }

  async function handleDeleteFolder() {
    setFolderStatus("");
    try {
      await deleteFolder(editingFolderId);
      if (folderFilter === editingFolderId) {
        setFolderFilter("all");
      }
      await refreshData();
      setIsEditingFolder(false);
    } catch (error) {
      setFolderStatus(error.message);
    }
  }

  function openBookmarkEditor(bookmark) {
    setEditingBookmarkId(bookmark.id);
    setBookmarkTitle(bookmark.title || bookmark.url);
    setBookmarkFolderId(String(bookmark.folder_id));
    setBookmarkStatus("");
  }

  async function handleUpdateBookmark() {
    setBookmarkStatus("");
    try {
      await updateBookmark(editingBookmarkId, {
        title: bookmarkTitle,
        folder_id: Number(bookmarkFolderId),
      });
      const bookmarkList = await getBookmarks(
        folderFilter === "all" ? null : folderFilter,
        keyword,
      );
      const allBookmarks = await getBookmarks();
      setBookmarks(bookmarkList);
      setRecordCount(allBookmarks.length);
      setCurrentPage(1);
      setEditingBookmarkId(null);
    } catch (error) {
      setBookmarkStatus(error.message);
    }
  }

  async function handleDeleteBookmark() {
    setBookmarkStatus("");
    try {
      await deleteBookmark(editingBookmarkId);
      const bookmarkList = await getBookmarks(
        folderFilter === "all" ? null : folderFilter,
        keyword,
      );
      const allBookmarks = await getBookmarks();
      setBookmarks(bookmarkList);
      setRecordCount(allBookmarks.length);
      setCurrentPage(1);
      setEditingBookmarkId(null);
    } catch (error) {
      setBookmarkStatus(error.message);
    }
  }

  const pageCount = Math.max(1, Math.ceil(bookmarks.length / BOOKMARKS_PER_PAGE));
  const pageStart = (currentPage - 1) * BOOKMARKS_PER_PAGE;
  const visibleBookmarks = bookmarks.slice(pageStart, pageStart + BOOKMARKS_PER_PAGE);

  useEffect(() => {
    if (currentPage > pageCount) {
      setCurrentPage(pageCount);
    }
  }, [currentPage, pageCount]);

  return (
    <main className="shell">
      <div className="workspace">
        <header className="intro" aria-labelledby="page-title">
          <p className="eyebrow">WEBMARK</p>
          <h1 id="page-title">把值得留下的网页，收进自己的资料库。</h1>
          <form className="input-group save-bar" onSubmit={handleSubmit}>
            <input
              className="form-control url-input"
              type="text"
              placeholder="url"
              aria-label="网址"
              value={url}
              onChange={(event) => {
                setUrl(event.target.value);
                setStatus("");
              }}
              required
            />
            <input
              className="form-control folder-input"
              type="text"
              placeholder="folder"
              aria-label="文件夹"
              list="folder-options"
              value={folder}
              onChange={(event) => {
                setFolder(event.target.value);
                setStatus("");
              }}
              required
            />
            <datalist id="folder-options">
              {Object.entries(folders).map(([id, name]) => (
                <option key={id} value={name} />
              ))}
            </datalist>
            <button className="btn btn-dark save-button" type="submit" disabled={isSaving}>
              {isSaving ? "Saving..." : "Save"}
            </button>
          </form>
          {status && <p className="save-status" role="status">{status}</p>}
        </header>

        <section className="overview" aria-label="收藏概览">
          <div className="record-count">
            <span>Records</span>
            <strong>{recordCount}</strong>
          </div>
          <form className="search-control" onSubmit={handleSearch}>
            <span>Search</span>
            <div className="search-row">
              <input
                className="form-control"
                type="search"
                placeholder="keyword"
                aria-label="关键词搜索"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
              />
              <button className="btn btn-dark" type="submit">Search</button>
            </div>
          </form>
          <div className="filter-control">
            <span>Filter</span>
            <div className="filter-row">
              <select
                className="form-select"
                aria-label="Filter"
                value={folderFilter}
                onChange={(event) => {
                  setFolderFilter(event.target.value);
                  setIsEditingFolder(false);
                  if (event.target.value === "all") {
                    getBookmarks(null, keyword).then((bookmarkList) => {
                      setBookmarks(bookmarkList);
                      setCurrentPage(1);
                    }).catch(() => {});
                  }
                }}
              >
                <option value="all">All folders</option>
                {Object.entries(folders).map(([id, name]) => (
                  <option key={id} value={id}>{name}</option>
                ))}
              </select>
              <button
                className="btn btn-dark filter-button"
                type="button"
                onClick={handleFilterFolder}
              >
                Filter
              </button>
              <button
                className="btn btn-outline-dark edit-folder-button"
                type="button"
                onClick={openFolderEditor}
              >
                Edit
              </button>
            </div>
            {isEditingFolder && (
              <div className="folder-editor">
                {editingFolderId ? (
                  <>
                    <div className="folder-actions">
                      <button className="btn btn-outline-dark btn-sm" type="button" onClick={() => setFolderEditorMode("rename")}>
                        Change name
                      </button>
                      <button className="btn btn-outline-danger btn-sm" type="button" onClick={handleDeleteFolder}>
                        Delete
                      </button>
                    </div>
                    {folderEditorMode === "rename" && (
                      <div className="rename-row">
                        <input
                          className="form-control"
                          aria-label="新文件夹名称"
                          value={folderName}
                          onChange={(event) => setFolderName(event.target.value)}
                        />
                        <button className="btn btn-dark btn-sm" type="button" onClick={handleRenameFolder} disabled={!folderName.trim()}>
                          Save
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="folder-empty-message">Select a folder first.</p>
                )}
                {folderStatus && <small className="folder-status" role="status">{folderStatus}</small>}
              </div>
            )}
          </div>
        </section>

        <section className="bookmark-section" aria-labelledby="bookmark-title">
          <div className="section-heading">
            <h2 id="bookmark-title">Bookmarks</h2>
            <span>{bookmarks.length}</span>
          </div>
          {bookmarks.length === 0 ? (
            <p className="empty-state">No bookmarks yet.</p>
          ) : (
            <ul className="bookmark-list">
              {visibleBookmarks.map((bookmark) => (
                <li className="bookmark-item" key={bookmark.id}>
                  <a
                    className="bookmark-detail-link"
                    href={`/bookmarks/${bookmark.id}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <strong>{bookmark.title || bookmark.url}</strong>
                    <span className="bookmark-url">{bookmark.url}</span>
                    <span>{folders[String(bookmark.folder_id)] || "未分类"}</span>
                  </a>
                  <div className="bookmark-edit-area">
                    <button className="btn btn-outline-dark btn-sm" type="button" onClick={() => openBookmarkEditor(bookmark)}>
                      Edit
                    </button>
                    {editingBookmarkId === bookmark.id && (
                      <div className="bookmark-editor">
                        <input
                          className="form-control form-control-sm"
                          aria-label="收藏标题"
                          value={bookmarkTitle}
                          onChange={(event) => setBookmarkTitle(event.target.value)}
                        />
                        <select
                          className="form-select form-select-sm"
                          aria-label="收藏文件夹"
                          value={bookmarkFolderId}
                          onChange={(event) => setBookmarkFolderId(event.target.value)}
                        >
                          {Object.entries(folders).map(([id, name]) => (
                            <option key={id} value={id}>{name}</option>
                          ))}
                        </select>
                        <div className="bookmark-editor-actions">
                          <button className="btn btn-dark btn-sm" type="button" onClick={handleUpdateBookmark} disabled={!bookmarkTitle.trim() || !bookmarkFolderId}>Save</button>
                          <button className="btn btn-outline-danger btn-sm" type="button" onClick={handleDeleteBookmark}>Delete</button>
                          <button className="btn btn-link btn-sm text-dark" type="button" onClick={() => setEditingBookmarkId(null)}>Cancel</button>
                        </div>
                        {bookmarkStatus && <small className="folder-status" role="status">{bookmarkStatus}</small>}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
          {pageCount > 1 && (
            <nav className="pagination-controls" aria-label="Bookmarks pagination">
              <button
                className="btn btn-outline-dark btn-sm"
                type="button"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((page) => page - 1)}
              >
                Previous
              </button>
              <span>Page {currentPage} of {pageCount}</span>
              <button
                className="btn btn-outline-dark btn-sm"
                type="button"
                disabled={currentPage === pageCount}
                onClick={() => setCurrentPage((page) => page + 1)}
              >
                Next
              </button>
            </nav>
          )}
        </section>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<BookmarkHome />} />
      <Route path="/bookmarks/:id" element={<BookmarkDetail />} />
    </Routes>
  );
}

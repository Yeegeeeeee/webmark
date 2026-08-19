const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/webmark";

export async function createBookmark(bookmark) {
  const response = await fetch(`${API_BASE_URL}/bookmarks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bookmark),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "保存失败");
  }
}

export async function getFolders() {
  const response = await fetch(`${API_BASE_URL}/folders`);
  if (!response.ok) {
    throw new Error("无法读取文件夹");
  }
  return response.json();
}

export async function renameFolder(id, name) {
  const response = await fetch(`${API_BASE_URL}/folders/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "文件夹改名失败");
  }
}

export async function deleteFolder(id) {
  const response = await fetch(`${API_BASE_URL}/folders/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "文件夹删除失败");
  }
}

export async function getBookmarks(folderId = null, keyword = "") {
  const parameters = new URLSearchParams();
  if (folderId !== null) {
    parameters.set("folder_id", folderId);
  }
  if (keyword.trim()) {
    parameters.set("keyword", keyword.trim());
  }
  const query = parameters.size ? `?${parameters.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/bookmarks${query}`);
  if (!response.ok) {
    throw new Error("无法读取收藏");
  }
  const bookmarks = await response.json();
  return Array.isArray(bookmarks) ? bookmarks : [];
}

export async function getBookmark(id) {
  const response = await fetch(`${API_BASE_URL}/bookmarks/${encodeURIComponent(id)}`);
  if (!response.ok) {
    throw new Error(response.status === 404 ? "收藏不存在" : "无法读取收藏");
  }
  return response.json();
}

export async function updateBookmark(id, bookmark) {
  const response = await fetch(`${API_BASE_URL}/bookmarks/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bookmark),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "收藏修改失败");
  }
}

export async function deleteBookmark(id) {
  const response = await fetch(`${API_BASE_URL}/bookmarks/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "收藏删除失败");
  }
}

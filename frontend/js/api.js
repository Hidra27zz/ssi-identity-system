/**
 * Helper gọi REST API backend và các tiện ích dùng chung.
 * BACKEND_URL rỗng = same origin (FastAPI serve cả frontend lẫn API).
 */

const BACKEND_URL = "";

// ── Toast notification ────────────────────────────────────────
export function showToast(message, type = "info", duration = 4000) {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = "toast " + type;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
}

// ── Loading state ─────────────────────────────────────────────
export function setLoading(btnId, loading) {
    const btn = typeof btnId === "string" ? document.getElementById(btnId) : btnId;
    if (!btn) return;
    if (loading) {
        btn.disabled = true;
        btn._orig = btn.innerHTML;
        btn.innerHTML = '<span class="spinner"></span>Đang xử lý...';
    } else {
        btn.disabled = false;
        if (btn._orig) btn.innerHTML = btn._orig;
    }
}

// ── Core fetch ────────────────────────────────────────────────
export async function apiFetch(path, options = {}) {
    const res = await fetch(BACKEND_URL + path, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Lỗi API: " + res.status);
    }
    return res.json();
}

export async function apiPost(path, body) {
    return apiFetch(path, { method: "POST", body: JSON.stringify(body) });
}

export async function apiUpload(path, formData) {
    const res = await fetch(BACKEND_URL + path, { method: "POST", body: formData });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Lỗi upload: " + res.status);
    }
    return res.json();
}

export async function apiRetrieve(path, body) {
    const res = await fetch(BACKEND_URL + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Lỗi tải file: " + res.status);
    }
    return res.blob();
}

// ── localStorage helpers ──────────────────────────────────────
export const store = {
    set: (k, v) => { try { localStorage.setItem("ssi_" + k, v); } catch {} },
    get: (k) => { try { return localStorage.getItem("ssi_" + k) || ""; } catch { return ""; } },
    setSession: (k, v) => { try { sessionStorage.setItem("ssi_" + k, v); } catch {} },
    getSession: (k) => { try { return sessionStorage.getItem("ssi_" + k) || ""; } catch { return ""; } },
};

// ── Format timestamp từ Unix seconds ─────────────────────────
export function formatTs(ts) {
    if (!ts || ts === 0) return "Chưa có";
    return new Date(ts * 1000).toLocaleString("vi-VN");
}

// ── Hiển thị status box ───────────────────────────────────────
export function showStatus(elementId, message, type) {
    const box = document.getElementById(elementId);
    if (!box) return;
    box.innerHTML = message;
    box.className = "status-box " + type;
    box.classList.remove("hidden");
}

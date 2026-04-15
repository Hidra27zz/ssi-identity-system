/**
 * Helper goi REST API backend.
 * Nguoi phu trach: Phuc
 */
import { BACKEND_URL } from "../../shared/constants.js";

export async function apiFetch(path, options = {}) {
    const url = `${BACKEND_URL}${path}`;
    const res = await fetch(url, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "API error");
    }
    return res.json();
}

export async function apiUpload(path, formData) {
    const url = `${BACKEND_URL}${path}`;
    const res = await fetch(url, { method: "POST", body: formData });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Upload error");
    }
    return res.json();
}

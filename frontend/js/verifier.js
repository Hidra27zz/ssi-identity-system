/**
 * Logic cho trang Identity Verifier.
 * Quy trình: Xác minh DID → Kiểm tra NFT → Xin consent → Tải file
 */
import { apiFetch, apiRetrieve, showToast, setLoading, store, formatTs } from "./api.js";

const BLOCK_EXPLORER = "https://sepolia.etherscan.io/tx/";
let _lastVerifiedAddress = "";

// ── Auto-fill từ localStorage ─────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
    const saved = store.get("walletAddress");
    if (saved) {
        const el = document.getElementById("requesterAddress");
        if (el) el.value = saved;
        const el2 = document.getElementById("retrieveRequester");
        if (el2) el2.value = saved;
    }
});

// ── 1. Xác minh DID ──────────────────────────────────────────
export async function verifyDID() {
    const address = document.getElementById("verifyAddress").value.trim();
    if (!address) { showToast("Nhập địa chỉ ví cần kiểm tra", "error"); return; }

    setLoading("btnVerify", true);
    try {
        const result = await apiFetch("/api/did/verify/" + address);
        _lastVerifiedAddress = address;

        // Status box màu sắc theo trạng thái
        const statusBox = document.getElementById("verifyStatusBox");
        if (result.is_valid) {
            statusBox.className = "access-granted";
            statusBox.textContent = "ĐỊNH DANH HỢP LỆ — Đã được xác minh bởi cơ quan có thẩm quyền";
        } else if (result.status === "pending") {
            statusBox.className = "status-box pending";
            statusBox.textContent = "ĐANG CHỜ XÁC MINH — DID đã tạo nhưng chưa được Creator xác minh";
        } else if (result.status === "revoked") {
            statusBox.className = "access-denied";
            statusBox.textContent = "ĐỊNH DANH ĐÃ BỊ THU HỒI — Không thể sử dụng";
        } else {
            statusBox.className = "status-box pending";
            statusBox.textContent = "KHÔNG TÌM THẤY — Địa chỉ này chưa tạo DID";
        }

        // Điền thông tin
        document.getElementById("resultAddress").textContent = result.address;
        const statusEl = document.getElementById("resultStatus");
        statusEl.textContent = (result.status || "not_found").toUpperCase();
        statusEl.className = "status-badge " + (result.status || "not_found");
        document.getElementById("resultDid").textContent = result.did || "Chưa có";
        document.getElementById("resultCid").textContent = result.cid || "Chưa có";
        document.getElementById("resultVerifiedBy").textContent = result.verified_by || "Chưa có";
        document.getElementById("resultUpdateCount").textContent = result.update_count ?? 0;
        document.getElementById("resultTime").textContent = new Date().toLocaleString("vi-VN");

        // Tự động điền form consent và retrieve
        if (result.did) {
            const ownerEl = document.getElementById("ownerDid");
            if (ownerEl) ownerEl.value = result.did;
            const retrieveEl = document.getElementById("retrieveOwnerDid");
            if (retrieveEl) retrieveEl.value = result.did;
        }
        if (result.cid) {
            const cidEl = document.getElementById("retrieveCid");
            if (cidEl) cidEl.value = result.cid;
        }

        document.getElementById("verifyResult").classList.remove("hidden");
        document.getElementById("fullRecord").classList.add("hidden");

        // Đổi màu border card theo trạng thái
        const card = document.getElementById("verifyResultCard");
        if (card) card.className = "card result-card-" + (result.status || "not_found");

    } catch (e) {
        showToast("Lỗi xác minh: " + e.message, "error");
    } finally {
        setLoading("btnVerify", false);
    }
}

// ── Xem chi tiết đầy đủ ──────────────────────────────────────
export async function loadFullRecord() {
    const address = _lastVerifiedAddress || document.getElementById("verifyAddress").value.trim();
    if (!address) return;
    try {
        const r = await apiFetch("/api/did/record/" + address);
        const el = document.getElementById("fullRecord");
        el.innerHTML = `
            <div style="background:#f8fafc;border:1px solid var(--border);border-radius:8px;padding:16px;font-size:.85rem;">
                <div class="info-row"><span class="info-label">Document Hash</span><span class="info-value">${r.doc_hash || "Chưa có"}</span></div>
                <div class="info-row"><span class="info-label">Ngày tạo</span><span class="info-value">${formatTs(r.created_at)}</span></div>
                <div class="info-row"><span class="info-label">Ngày xác minh</span><span class="info-value">${formatTs(r.verified_at)}</span></div>
                <div class="info-row"><span class="info-label">Cập nhật lần cuối</span><span class="info-value">${formatTs(r.updated_at)}</span></div>
                <div class="info-row"><span class="info-label">Số lần cập nhật</span><span class="info-value">${r.update_count}</span></div>
            </div>`;
        el.classList.remove("hidden");
    } catch (e) {
        showToast("Lỗi: " + e.message, "error");
    }
}

// ── 2. Kiểm tra NFT / Token-gated ────────────────────────────
export async function checkNFTAccess() {
    const address = document.getElementById("nftCheckAddress").value.trim();
    if (!address) { showToast("Nhập địa chỉ ví", "error"); return; }

    setLoading("btnCheckAccess", true);
    const resultEl = document.getElementById("nftAccessResult");
    try {
        const result = await apiFetch("/api/nft/verify-access/" + address);
        if (result.has_access) {
            resultEl.innerHTML = '<div class="access-granted">CÓ QUYỀN TRUY CẬP<br><span style="font-size:.9rem;font-weight:400;">' + result.reason + ' — ' + result.token_count + ' token hợp lệ</span></div>';
        } else {
            resultEl.innerHTML = '<div class="access-denied">KHÔNG CÓ QUYỀN TRUY CẬP<br><span style="font-size:.9rem;font-weight:400;">' + result.reason + '</span></div>';
        }
        resultEl.classList.remove("hidden");
    } catch (e) {
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnCheckAccess", false);
    }
}

// ── 3. Xin consent ───────────────────────────────────────────
export async function requestConsent() {
    const ownerDid = document.getElementById("ownerDid").value.trim();
    const requester = document.getElementById("requesterAddress").value.trim();
    const dataType = document.getElementById("dataType").value;

    if (!ownerDid || !requester) {
        showToast("Nhập DID chủ sở hữu và địa chỉ ví của bạn", "error");
        return;
    }

    setLoading("btnRequestConsent", true);
    const resultEl = document.getElementById("consentResult");
    try {
        const result = await apiFetch("/api/consent/request", {
            method: "POST",
            body: JSON.stringify({
                owner_did: ownerDid,
                requester_address: requester,
                data_type: dataType,
            }),
        });
        resultEl.className = "status-box success";
        resultEl.innerHTML = "Yêu cầu đã gửi thành công!<br>Consent ID: <strong>" + result.consent_id + "</strong><br>Chờ chủ sở hữu phê duyệt tại trang User Dashboard.";
        resultEl.classList.remove("hidden");
        store.set("walletAddress", requester);
        showToast("Đã gửi yêu cầu consent", "success");
    } catch (e) {
        resultEl.className = "status-box error";
        resultEl.textContent = "Lỗi: " + e.message;
        resultEl.classList.remove("hidden");
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnRequestConsent", false);
    }
}

// ── 4. Tải file sau khi có consent ───────────────────────────
export async function retrieveFile() {
    const cid = document.getElementById("retrieveCid").value.trim();
    const ownerDid = document.getElementById("retrieveOwnerDid").value.trim();
    const requester = document.getElementById("retrieveRequester").value.trim();
    const privateKey = document.getElementById("retrievePrivateKey").value.trim();

    if (!cid || !ownerDid || !requester || !privateKey) {
        showToast("Nhập đầy đủ CID, DID, địa chỉ ví và private key", "error");
        return;
    }

    setLoading("btnRetrieve", true);
    const resultEl = document.getElementById("retrieveResult");
    resultEl.className = "status-box pending";
    resultEl.textContent = "Đang tải file từ IPFS và giải mã...";
    resultEl.classList.remove("hidden");

    try {
        const blob = await apiRetrieve("/api/retrieve/" + cid, {
            private_key: privateKey,
            owner_did: ownerDid,
            requester_address: requester,
        });

        const url = URL.createObjectURL(blob);
        const type = blob.type;

        if (type.startsWith("image/")) {
            resultEl.className = "status-box success";
            resultEl.innerHTML = 'Tải file thành công!<br><img src="' + url + '" style="max-width:100%;margin-top:10px;border-radius:8px;">';
        } else if (type === "application/pdf") {
            resultEl.className = "status-box success";
            resultEl.innerHTML = 'Tải file thành công! <a href="' + url + '" target="_blank" style="font-weight:600;">Mở file PDF</a>';
        } else {
            const a = document.createElement("a");
            a.href = url;
            a.download = "file_" + cid.slice(0, 8);
            a.click();
            resultEl.className = "status-box success";
            resultEl.textContent = "Tải file thành công! File đã được tải xuống.";
        }
        showToast("Tải file thành công", "success");
    } catch (e) {
        resultEl.className = "status-box error";
        if (e.message.includes("consent")) {
            resultEl.textContent = "Không có quyền truy cập: " + e.message;
        } else if (e.message.includes("Authentication")) {
            resultEl.textContent = "Private key không khớp. Kiểm tra lại private key.";
        } else {
            resultEl.textContent = "Lỗi: " + e.message;
        }
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnRetrieve", false);
    }
}

// Expose to window
Object.assign(window, {
    verifyDID, loadFullRecord, checkNFTAccess,
    requestConsent, retrieveFile,
});

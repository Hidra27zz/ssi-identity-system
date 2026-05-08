/**
 * Logic cho trang Identity User.
 */
import { apiFetch, showToast, setLoading, store, formatTs } from "./api.js";

// ── Auto-fill từ localStorage ─────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
    const saved = store.get("walletAddress");
    if (saved) {
        const fields = ["walletAddress","didWallet","checkAddress","nftAddress"];
        fields.forEach(id => { const el = document.getElementById(id); if (el) el.value = saved; });
        updateSidebar(saved);
    }
    const savedDid = store.get("did");
    if (savedDid) {
        const el = document.getElementById("didString");
        if (el) el.value = savedDid;
        const el2 = document.getElementById("myDidForConsent");
        if (el2) el2.value = savedDid;
        const el3 = document.getElementById("consentDid");
        if (el3) el3.value = savedDid;
    }
});

function updateSidebar(wallet) {
    const el = document.getElementById("sidebarWallet");
    if (el && wallet) el.textContent = wallet.slice(0,6) + "..." + wallet.slice(-4);
}

// ── 1. Tạo Keypair ────────────────────────────────────────────
export async function generateKeypair() {
    const wallet = document.getElementById("walletAddress").value.trim();
    if (!wallet) { showToast("Nhập địa chỉ ví trước", "error"); return; }

    setLoading("btnGenKeypair", true);
    try {
        const result = await apiFetch("/api/crypto/generate-keypair", {
            method: "POST",
            body: JSON.stringify({ wallet_address: wallet }),
        });
        document.getElementById("publicKeyDisplay").value = result.public_key;
        document.getElementById("privateKeyDisplay").value = result.private_key;
        document.getElementById("keypairResult").classList.remove("hidden");
        store.set("walletAddress", wallet);
        updateSidebar(wallet);
        ["didWallet","checkAddress","nftAddress"].forEach(id => {
            const el = document.getElementById(id);
            if (el && !el.value) el.value = wallet;
        });
        showToast("Tạo keypair thành công. Hãy tải private key ngay!", "success");
    } catch (e) {
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnGenKeypair", false);
    }
}

export function downloadPrivateKey() {
    const key = document.getElementById("privateKeyDisplay").value;
    if (!key) return;
    const blob = new Blob([key], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "private_key.pem";
    a.click();
    URL.revokeObjectURL(url);
    showToast("Đã tải private key", "success");
}

export function savePrivateKeyToSession() {
    const key = document.getElementById("privateKeyDisplay").value;
    if (!key) return;
    store.setSession("privateKey", key);
    showToast("Đã lưu private key vào session (sẽ xóa khi đóng tab)", "info");
}

// ── 2. Tạo DID ────────────────────────────────────────────────
export function autoFillDID() {
    const wallet = document.getElementById("didWallet").value.trim()
        || document.getElementById("walletAddress").value.trim();
    if (!wallet) { showToast("Nhập địa chỉ ví trước", "error"); return; }
    document.getElementById("didWallet").value = wallet;
    document.getElementById("didString").value = "did:ssi:" + wallet.toLowerCase();
}

export async function createDID() {
    const wallet = document.getElementById("didWallet").value.trim();
    const did = document.getElementById("didString").value.trim();
    if (!wallet || !did) { showToast("Nhập đầy đủ địa chỉ ví và chuỗi DID", "error"); return; }

    setLoading("btnCreateDID", true);
    const resultEl = document.getElementById("createDIDResult");
    resultEl.className = "status-box pending";
    resultEl.textContent = "Đang gửi giao dịch lên Sepolia...";
    resultEl.classList.remove("hidden");

    try {
        const result = await apiFetch("/api/did/create", {
            method: "POST",
            body: JSON.stringify({ wallet_address: wallet, did }),
        });
        store.set("walletAddress", wallet);
        store.set("did", did);
        updateSidebar(wallet);
        const el2 = document.getElementById("myDidForConsent");
        if (el2) el2.value = did;
        const el3 = document.getElementById("consentDid");
        if (el3) el3.value = did;
        resultEl.className = "status-box success";
        resultEl.innerHTML = "Tạo DID thành công!<br>TX: <a href='https://sepolia.etherscan.io/tx/" + result.tx_hash + "' target='_blank'>" + result.tx_hash + "</a>";
        showToast("Tạo DID thành công!", "success");
    } catch (e) {
        resultEl.className = "status-box error";
        resultEl.textContent = "Lỗi: " + e.message;
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnCreateDID", false);
    }
}

// ── 3. Xem thông tin DID ──────────────────────────────────────
export async function loadDIDInfo() {
    const address = document.getElementById("checkAddress").value.trim();
    if (!address) { showToast("Nhập địa chỉ ví", "error"); return; }

    setLoading("btnLoadDID", true);
    try {
        const r = await apiFetch("/api/did/record/" + address);

        document.getElementById("didValue").textContent = r.did || "Chưa có";

        const statusEl = document.getElementById("didStatus");
        statusEl.textContent = r.status ? r.status.toUpperCase() : "—";
        statusEl.className = "status-badge " + (r.status || "not_found");

        document.getElementById("didCid").textContent = r.ipfs_cid || "Chưa có";
        document.getElementById("didCreatedAt").textContent = formatTs(r.created_at);
        document.getElementById("didVerifiedAt").textContent = formatTs(r.verified_at);
        document.getElementById("didVerifiedBy").textContent = r.verified_by || "Chưa có";
        document.getElementById("didUpdateCount").textContent = r.update_count ?? 0;
        document.getElementById("didInfo").classList.remove("hidden");

        const sidebarStatus = document.getElementById("sidebarStatus");
        if (sidebarStatus) {
            sidebarStatus.textContent = r.status ? r.status.toUpperCase() : "—";
            sidebarStatus.className = "status-badge " + (r.status || "not_found");
        }
        const sidebarDid = document.getElementById("sidebarDid");
        if (sidebarDid) sidebarDid.textContent = r.did ? r.did.slice(0, 20) + "..." : "Chưa có";
    } catch (e) {
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnLoadDID", false);
    }
}

// ── 4. Kiểm tra NFT ───────────────────────────────────────────
export async function checkNFT() {
    const address = document.getElementById("nftAddress").value.trim();
    if (!address) { showToast("Nhập địa chỉ ví", "error"); return; }

    setLoading("btnCheckNFT", true);
    try {
        const [statusRes, accessRes] = await Promise.all([
            apiFetch("/api/nft/status/" + address),
            apiFetch("/api/nft/verify-access/" + address),
        ]);

        const accessEl = document.getElementById("nftAccessResult");
        if (accessRes.has_access) {
            accessEl.innerHTML = '<div class="access-granted">CÓ QUYỀN TRUY CẬP — ' + accessRes.token_count + ' Soulbound Token hợp lệ</div>';
        } else {
            accessEl.innerHTML = '<div class="access-denied">KHÔNG CÓ QUYỀN TRUY CẬP — ' + accessRes.reason + '</div>';
        }

        const listEl = document.getElementById("tokenList");
        if (statusRes.tokens && statusRes.tokens.length > 0) {
            listEl.innerHTML = '<p style="font-weight:600;margin-bottom:8px;font-size:.85rem;">Danh sách token (' + statusRes.token_count + '):</p>';
            for (const tokenId of statusRes.tokens) {
                try {
                    const td = await apiFetch("/api/nft/token/" + tokenId);
                    listEl.innerHTML += '<div class="token-item"><strong>Token #' + td.token_id + '</strong><br>Loại: ' + td.credential_type + '<br>Trạng thái: ' + (td.is_valid ? "Hợp lệ" : "Đã vô hiệu hóa") + '<br>Ngày cấp: ' + formatTs(td.minted_at) + '</div>';
                } catch {}
            }
        } else {
            listEl.innerHTML = '<p class="text-muted">Chưa có token nào.</p>';
        }

        const sidebarNft = document.getElementById("sidebarNft");
        if (sidebarNft) sidebarNft.textContent = accessRes.has_access ? (statusRes.token_count + " token hợp lệ") : "Không có token";

        document.getElementById("nftInfo").classList.remove("hidden");
    } catch (e) {
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnCheckNFT", false);
    }
}

// ── 5. Consent ────────────────────────────────────────────────
export async function loadPendingConsents() {
    const did = (document.getElementById("myDidForConsent") || document.getElementById("consentDid"))?.value.trim();
    if (!did) { showToast("Nhập DID của bạn", "error"); return; }

    const hidden = document.getElementById("consentDid");
    if (hidden) hidden.value = did;

    setLoading("btnLoadConsents", true);
    const list = document.getElementById("consentList");
    list.innerHTML = '<p class="text-muted">Đang tải...</p>';

    try {
        const consents = await apiFetch("/api/consent/pending/" + encodeURIComponent(did));

        if (consents.length === 0) {
            list.innerHTML = '<p class="text-muted" style="font-style:italic;">Không có yêu cầu nào đang chờ.</p>';
            return;
        }

        list.innerHTML = consents.map(c => `
            <div class="consent-item">
                <p><strong>Từ:</strong> ${c.requester_address}</p>
                <p><strong>Loại dữ liệu:</strong> ${c.data_type}</p>
                <p><strong>Thời gian:</strong> ${new Date(c.requested_at).toLocaleString("vi-VN")}</p>
                <div style="display:flex;gap:8px;margin-top:10px;">
                    <button class="btn-success btn-sm" onclick="respondConsent(${c.id},'${did}','approved')">Đồng ý</button>
                    <button class="btn-danger btn-sm" onclick="respondConsent(${c.id},'${did}','rejected')">Từ chối</button>
                </div>
            </div>`).join("");
    } catch (e) {
        list.innerHTML = '<p style="color:var(--danger);">Lỗi: ' + e.message + '</p>';
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnLoadConsents", false);
    }
}

export async function respondConsent(consentId, ownerDid, decision) {
    try {
        await apiFetch("/api/consent/respond", {
            method: "POST",
            body: JSON.stringify({ consent_id: consentId, owner_did: ownerDid, decision }),
        });
        showToast(decision === "approved" ? "Đã đồng ý yêu cầu" : "Đã từ chối yêu cầu", "success");
        loadPendingConsents();
    } catch (e) {
        showToast("Lỗi: " + e.message, "error");
    }
}

Object.assign(window, {
    generateKeypair, downloadPrivateKey, savePrivateKeyToSession,
    autoFillDID, createDID, loadDIDInfo, checkNFT,
    loadPendingConsents, respondConsent,
});

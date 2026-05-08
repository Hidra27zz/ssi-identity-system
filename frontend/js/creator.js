/**
 * Logic cho trang Identity Creator.
 * Quy trình: Lấy public key → Upload ảnh → Upload PDF → Upload metadata → Gửi hash lên blockchain
 */
import { apiFetch, apiUpload, showToast, setLoading, store, showStatus } from "./api.js";

const BLOCK_EXPLORER = "https://sepolia.etherscan.io/tx/";

// Lưu CID tạm trong bộ nhớ
let _publicKey = "";
let _portraitCid = "";
let _documentCid = "";
let _docHash = "";

// ── Auto-fill địa chỉ Creator từ localStorage ─────────────────
window.addEventListener("DOMContentLoaded", () => {
    const saved = store.get("walletAddress");
    if (saved) {
        const el = document.getElementById("creatorAddress");
        if (el && !el.value) el.value = saved;
    }
});

// ── Bước 1: Tải danh sách DID chờ xác minh ───────────────────
export async function loadPendingList() {
    try {
        const rows = await apiFetch("/api/did/pending");
        const el = document.getElementById("pendingList");
        if (rows.length === 0) {
            el.innerHTML = '<p class="text-muted" style="font-style:italic;">Không có DID nào đang chờ xác minh.</p>';
            return;
        }
        el.innerHTML = rows.map(r => `
            <div class="pending-item">
                <p><strong>Ví:</strong> ${r.wallet_address}</p>
                <p><strong>DID:</strong> ${r.did}</p>
                <p><strong>Thời gian:</strong> ${new Date(r.created_at).toLocaleString("vi-VN")}</p>
                <button class="btn-sm" style="margin-top:8px;" onclick="fillFromPending('${r.wallet_address}','${r.did}','${r.doc_hash || ""}','${r.ipfs_cid || ""}')">
                    Chọn người dùng này
                </button>
            </div>`).join("");
    } catch (e) {
        showToast("Lỗi tải danh sách: " + e.message, "error");
    }
}

export function fillFromPending(wallet, did, hash, cid) {
    const fields = { userAddress: wallet, userDid: did, docHash: hash, ipfsCid: cid };
    Object.entries(fields).forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el) el.value = val;
    });
    if (hash) _docHash = hash;
    if (cid) _documentCid = cid;
    showToast("Đã điền thông tin từ danh sách chờ", "info");
    // Chuyển sang bước 2
    if (typeof goToStep === "function") goToStep(2);
}

// ── Bước 2: Lấy public key của user ──────────────────────────
export async function fetchPublicKey() {
    const wallet = document.getElementById("userAddress").value.trim();
    if (!wallet) { showToast("Nhập địa chỉ ví người dùng trước", "error"); return; }

    setLoading("btnFetchPubKey", true);
    const statusEl = document.getElementById("pubKeyStatus");
    try {
        const result = await apiFetch("/api/did/public-key/" + wallet);
        _publicKey = result.public_key_pem;

        // Tự động điền DID nếu chưa có
        const didEl = document.getElementById("userDid");
        if (didEl && !didEl.value) {
            const rec = await apiFetch("/api/did/record/" + wallet).catch(() => null);
            if (rec && rec.did) didEl.value = rec.did;
        }

        statusEl.className = "status-box success";
        statusEl.textContent = "Đã lấy public key thành công. Sẵn sàng upload tài liệu.";
        statusEl.classList.remove("hidden");
        showToast("Đã lấy public key", "success");
    } catch (e) {
        statusEl.className = "status-box error";
        statusEl.textContent = "Lỗi: " + e.message + ". Người dùng cần tạo keypair trước tại trang User.";
        statusEl.classList.remove("hidden");
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnFetchPubKey", false);
    }
}

export function onUserAddressChange() {
    _publicKey = "";
    const el = document.getElementById("pubKeyStatus");
    if (el) el.classList.add("hidden");
}

// ── Bước 3: Upload file lên IPFS ─────────────────────────────
export async function uploadFile(type) {
    if (!_publicKey) {
        showToast("Hãy lấy public key của user trước (Bước 2)", "error");
        return;
    }

    const did = document.getElementById("userDid").value.trim();
    const creator = document.getElementById("creatorAddress").value.trim();
    if (!did) { showToast("Nhập DID của người dùng", "error"); return; }
    if (!creator) { showToast("Nhập địa chỉ ví Creator của bạn", "error"); return; }

    const fileInput = document.getElementById(type === "portrait" ? "portraitFile" : "documentFile");
    const file = fileInput.files[0];
    if (!file) { showToast("Chọn file trước", "error"); return; }

    const btnId = type === "portrait" ? "btnUploadPortrait" : "btnUploadDoc";
    setLoading(btnId, true);

    const cidEl = document.getElementById(type === "portrait" ? "portraitCid" : "documentCid");
    cidEl.textContent = "Đang mã hóa và upload lên IPFS...";
    cidEl.classList.remove("hidden");

    try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("public_key", _publicKey);
        formData.append("did", did);
        formData.append("creator_address", creator);

        const result = await apiUpload("/api/upload", formData);

        if (type === "portrait") {
            _portraitCid = result.cid;
            cidEl.textContent = "Ảnh đã upload. CID: " + result.cid;
        } else {
            _documentCid = result.cid;
            _docHash = result.doc_hash;
            document.getElementById("docHash").value = _docHash;
            document.getElementById("ipfsCid").value = _documentCid;
            cidEl.textContent = "PDF đã upload. CID: " + result.cid;
        }
        showToast("Upload " + (type === "portrait" ? "ảnh" : "PDF") + " thành công", "success");
    } catch (e) {
        cidEl.textContent = "Lỗi: " + e.message;
        showToast("Lỗi upload: " + e.message, "error");
    } finally {
        setLoading(btnId, false);
    }
}

// ── Bước 3c: Upload metadata JSON ────────────────────────────
export async function uploadMetadata() {
    const did = document.getElementById("userDid").value.trim();
    const creator = document.getElementById("creatorAddress").value.trim();
    const docType = document.getElementById("docType").value;
    const issuedBy = document.getElementById("issuedBy").value.trim();

    if (!did) { showToast("Nhập DID người dùng", "error"); return; }
    if (!creator) { showToast("Nhập địa chỉ ví Creator", "error"); return; }
    if (!_portraitCid) { showToast("Upload ảnh chân dung trước (Bước 3.1)", "error"); return; }
    if (!_documentCid) { showToast("Upload PDF trước (Bước 3.2)", "error"); return; }
    if (!issuedBy) { showToast("Nhập cơ quan cấp", "error"); return; }

    setLoading("btnUploadMeta", true);
    const metaEl = document.getElementById("metadataCid");
    metaEl.textContent = "Đang tạo và upload metadata...";
    metaEl.classList.remove("hidden");

    try {
        const formData = new FormData();
        formData.append("did", did);
        formData.append("doc_type", docType);
        formData.append("issued_by", issuedBy);
        formData.append("portrait_cid", _portraitCid);
        formData.append("document_cid", _documentCid);
        formData.append("creator_address", creator);

        const result = await apiUpload("/api/upload/metadata", formData);
        metaEl.textContent = "Metadata đã upload. CID: " + result.cid;
        showToast("Upload metadata thành công", "success");
    } catch (e) {
        metaEl.textContent = "Lỗi: " + e.message;
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnUploadMeta", false);
    }
}

// ── Bước 4: Gửi hash lên blockchain ──────────────────────────
export async function storeHash() {
    const wallet = document.getElementById("userAddress").value.trim();
    const hash = document.getElementById("docHash").value.trim();
    const cid = document.getElementById("ipfsCid").value.trim();
    const creator = document.getElementById("creatorAddress").value.trim();

    if (!wallet || !hash || !cid || !creator) {
        showToast("Vui lòng hoàn tất upload ảnh và PDF trước (hash và CID sẽ tự điền)", "error");
        return;
    }

    setLoading("btnStoreHash", true);
    showStatus("txStatus", "Đang gửi giao dịch lên Sepolia blockchain... (có thể mất 15-30 giây)", "pending");

    try {
        const result = await apiFetch("/api/did/store-hash", {
            method: "POST",
            body: JSON.stringify({
                wallet_address: wallet,
                doc_hash: hash,
                cid: cid,
                creator_address: creator,
            }),
        });
        showStatus("txStatus",
            'Xác minh thành công!<br>TX: <a href="' + BLOCK_EXPLORER + result.tx_hash + '" target="_blank">' + result.tx_hash + '</a><br>Soulbound NFT sẽ được mint tự động.',
            "success"
        );
        showToast("Gửi hash lên blockchain thành công!", "success");
        store.set("walletAddress", creator);
    } catch (e) {
        showStatus("txStatus", "Lỗi: " + e.message, "error");
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnStoreHash", false);
    }
}

// Expose to window
Object.assign(window, {
    loadPendingList, fillFromPending, fetchPublicKey, onUserAddressChange,
    uploadFile, uploadMetadata, storeHash,
});

/**
 * Logic cho trang Identity Creator.
 * Quy trình: Lấy public key → Upload ảnh → Upload PDF → Upload metadata → Gửi hash lên blockchain
 */
import { apiFetch, apiUpload, showToast, setLoading, store, showStatus } from "./api.js";
import { requireRole } from "./auth-guard.js";

const BLOCK_EXPLORER = "https://sepolia.etherscan.io/tx/";

// Lưu CID tạm trong bộ nhớ
let _publicKey = "";
let _portraitCid = "";
let _documentCid = "";
let _docHash = "";
let _creatorAccount = ""; // địa chỉ đã xác thực qua auth-guard

// ── Auth Guard + Auto-fill địa chỉ Creator từ MetaMask ──────────
window.addEventListener("DOMContentLoaded", async () => {
    // Yêu cầu quyền creator — nếu không đủ quyền sẽ redirect về login
    try {
        _creatorAccount = await requireRole("creator");
    } catch {
        return; // requireRole đã xử lý redirect/hiển thị lỗi
    }

    // Điền địa chỉ creator từ account MetaMask đã xác thực
    const el = document.getElementById("creatorAddress");
    if (el) {
        el.value = _creatorAccount;
        el.readOnly = true; // không cho sửa tay — phải dùng đúng account
        el.title = "Địa chỉ được lấy từ MetaMask đang kết nối";
    }

    // Hiển thị badge account trên Navbar (Thiết kế mới)
    const badge = document.createElement("div");
    badge.style.cssText = "display:inline-flex;align-items:center;gap:6px;background:rgba(246, 133, 27, 0.1);color:#f6851b;border:1px solid rgba(246, 133, 27, 0.3);padding:6px 14px;border-radius:20px;font-size:0.85rem;font-weight:600;margin-left:12px;box-shadow:0 2px 8px rgba(246, 133, 27, 0.1);";
    badge.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> ${_creatorAccount.slice(0,6)}...${_creatorAccount.slice(-4)}`;
    
    const navbarLinks = document.querySelector(".navbar-links");
    if (navbarLinks) {
        navbarLinks.appendChild(badge);
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
        el.innerHTML = rows.map(r => {
            const keyBadge = r.has_public_key
                ? '<span style="color:#16a34a;font-size:.78rem;font-weight:600;">[OK] Có Public Key</span>'
                : '<span style="color:#dc2626;font-size:.78rem;font-weight:600;">[CẢNH BÁO] Chưa có Public Key — user cần tạo keypair trước</span>';
            const addrShort = r.wallet_address.slice(0,10) + "..." + r.wallet_address.slice(-6);
            return `
            <div class="pending-item" style="border-left:3px solid ${r.has_public_key ? '#16a34a' : '#f59e0b'};">
                <p><strong>Tài khoản:</strong> <span style="font-family:monospace;font-size:.85rem;">${r.wallet_address}</span></p>
                <p><strong>DID:</strong> <span style="font-family:monospace;font-size:.82rem;">${r.did}</span></p>
                <p><strong>Thời gian:</strong> ${new Date(r.created_at).toLocaleString("vi-VN")}</p>
                <p style="margin-top:4px;">${keyBadge}</p>
                <button class="btn-sm" style="margin-top:8px;${!r.has_public_key ? 'opacity:.5;cursor:not-allowed;' : ''}"
                    onclick="fillFromPending('${r.wallet_address}','${r.did}','${r.doc_hash || ""}','${r.ipfs_cid || ""}')"
                    ${!r.has_public_key ? 'disabled title="User cần tạo keypair RSA trước tại User Dashboard"' : ''}>
                    ${r.has_public_key ? 'Chọn người dùng này' : '[Chờ] User tạo keypair'}
                </button>
            </div>`;
        }).join("");
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
        // Bắt buộc set IPFS CID của Metadata để đẩy lên Blockchain
        document.getElementById("ipfsCid").value = result.cid;
        showToast("Upload metadata thành công", "success");
    } catch (e) {
        metaEl.textContent = "Lỗi: " + e.message;
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnUploadMeta", false);
    }
}

// ── Bước 4a: Gửi hash lên blockchain ───────────────────────
let _lastTxHash = ""; // lưu để hiển thị ở bước 5

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

        _lastTxHash = result.tx_hash || "";

        showStatus("txStatus",
            'Xác minh thành công! → Bước tiếp theo: Mint Soulbound NFT bên dưới.<br>TX: <a href="' +
            BLOCK_EXPLORER + _lastTxHash + '" target="_blank">' + _lastTxHash + '</a>',
            "success"
        );
        showToast("Gửi hash lên blockchain thành công!", "success");

        // Hiển thị phần Mint NFT
        const mintSection = document.getElementById("mintNftSection");
        if (mintSection) {
            mintSection.classList.remove("hidden");
            // Điền sẵn thông tin
            const recipientEl = document.getElementById("mintRecipient");
            if (recipientEl) recipientEl.textContent = wallet;
            const uriEl = document.getElementById("mintMetadataUri");
            if (uriEl) uriEl.value = "ipfs://" + cid;
            // Đồng bộ docType với loại chứng chỉ đã chọn ở bước 3
            const docType = document.getElementById("docType")?.value;
            if (docType) {
                const sel = document.getElementById("mintCredentialType");
                if (sel) sel.value = docType;
            }
            // Scroll xuống
            mintSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    } catch (e) {
        showStatus("txStatus", "Lỗi: " + e.message, "error");
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnStoreHash", false);
    }
}

// ── Bước 4b: Mint Soulbound NFT ──────────────────────────────
export async function mintNFT() {
    const recipient = document.getElementById("userAddress").value.trim();
    const credentialType = document.getElementById("mintCredentialType").value;
    const metadataUri = document.getElementById("mintMetadataUri").value.trim();

    if (!recipient) {
        showToast("Không có địa chỉ người dùng. Vui lòng quay lại bước 2.", "error");
        return;
    }
    if (!metadataUri) {
        showToast("Chưa có Metadata URI. Hoàn tất upload và gửi hash trước.", "error");
        return;
    }

    setLoading("btnMintNFT", true);
    showStatus("mintStatus", "Đang mint Soulbound NFT... (có thể mất 15-30 giây)", "pending");

    try {
        const result = await apiFetch("/api/nft/mint", {
            method: "POST",
            body: JSON.stringify({
                recipient_address: recipient,
                credential_type: credentialType,
                metadata_uri: metadataUri,
            }),
        });

        showStatus(
            "mintStatus",
            'Soulbound NFT đã được mint thành công!<br>TX: <a href="' +
            BLOCK_EXPLORER + result.tx_hash + '" target="_blank">' + result.tx_hash + '</a>',
            "success"
        );
        showToast("Mint NFT thành công!", "success");

        // Điền completion summary cho bước 5
        const el = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };
        el("completeTxHash", _lastTxHash || "—");
        el("completeMintTx", result.tx_hash || "—");
        el("completeNftType", credentialType);
        el("completeRecipient", recipient);

        // Chuyển bước 5 sau 1.5 giây
        setTimeout(() => { if (typeof goToStep === "function") goToStep(5); }, 1500);

    } catch (e) {
        showStatus("mintStatus", "Lỗi mint NFT: " + e.message, "error");
        showToast("Lỗi mint NFT: " + e.message, "error");
    } finally {
        setLoading("btnMintNFT", false);
    }
}

// ── Thu hồi DID (Bổ sung) ────────────────────────────────────
export async function revokeDID() {
    const address = document.getElementById("revokeAddress").value.trim();
    if (!address) {
        showToast("Nhập địa chỉ tài khoản cần thu hồi", "error");
        return;
    }
    
    if (!confirm("CẢNH BÁO: Hành động này sẽ thu hồi vĩnh viễn định danh và vô hiệu hóa tất cả Soulbound NFT của ví này. Bạn có chắc chắn không?")) {
        return;
    }

    setLoading("btnRevokeDID", true);
    const statusEl = document.getElementById("revokeStatus");
    statusEl.className = "status-box pending";
    statusEl.textContent = "Đang gửi giao dịch thu hồi lên blockchain (có thể mất 15-30 giây)...";
    statusEl.classList.remove("hidden");

    try {
        const result = await apiFetch("/api/did/revoke", {
            method: "POST",
            body: JSON.stringify({ wallet_address: address }),
        });

        statusEl.className = "status-box success";
        statusEl.innerHTML = `Thu hồi định danh thành công!<br>TX: <a href="${BLOCK_EXPLORER}${result.tx_hash}" target="_blank">${result.tx_hash}</a>`;
        showToast("Đã thu hồi DID thành công", "success");
    } catch (e) {
        statusEl.className = "status-box error";
        statusEl.textContent = "Lỗi thu hồi: " + e.message;
        showToast("Lỗi: " + e.message, "error");
    } finally {
        setLoading("btnRevokeDID", false);
    }
}

// Expose to window
Object.assign(window, {
    loadPendingList, fillFromPending, fetchPublicKey, onUserAddressChange,
    uploadFile, uploadMetadata, storeHash, mintNFT, revokeDID,
});

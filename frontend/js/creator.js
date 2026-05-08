/**
 * Logic cho Creator Dashboard.
 * Nguoi phu trach: Phuc
 */
import { apiFetch, apiUpload } from "./api.js";
import { BLOCK_EXPLORER_URL } from "../../shared/constants.js";

let portraitCid = "";
let documentCid = "";

// [ĐÃ THÊM] Hàm lấy danh sách chờ
export async function loadPendingRequests() {
    try {
        const requests = await apiFetch("/api/did/pending");
        const listEl = document.getElementById("pendingList");
        listEl.innerHTML = "";

        if (requests.length === 0) {
            listEl.innerHTML = "<p>Không có yêu cầu nào đang chờ xác minh.</p>";
            return;
        }

        requests.forEach(req => {
            const div = document.createElement("div");
            div.style.padding = "10px";
            div.style.borderLeft = "3px solid #007bff";
            div.style.marginBottom = "10px";
            div.style.backgroundColor = "#f8f9fa";
            div.innerHTML = `
                <p><strong>Ví:</strong> ${req.wallet_address}</p>
                <p><strong>DID:</strong> ${req.did}</p>
                <button onclick="selectUser('${req.wallet_address}', '${req.did}')">Xử lý người này</button>
            `;
            listEl.appendChild(div);
        });
    } catch (e) {
        alert(`Lỗi tải danh sách: ${e.message}`);
    }
}

// [ĐÃ THÊM] Hàm tự động điền form khi chọn user từ danh sách
export function selectUser(address, did) {
    document.getElementById("userAddress").value = address;
    document.getElementById("userDid").value = did;
    window.scrollTo({ top: document.getElementById("userAddress").offsetTop, behavior: "smooth" });
}

// [ĐÃ SỬA] Tách logic lấy Public Key ra một hàm riêng để dùng chung
async function fetchPublicKey(walletAddress) {
    try {
        // Cố gắng lấy qua API
        const pubKeyRes = await apiFetch(`/api/did/public-key/${walletAddress}`);
        return pubKeyRes.public_key_pem;
    } catch (e) {
        // Fallback: Giữ lại prompt() đề phòng trường hợp Backend của bạn Thủy chưa sửa xong lỗi DB
        const key = prompt(`Lỗi lấy Public Key từ Server (${e.message}). Vui lòng nhập thủ công:`);
        return key;
    }
}

export async function uploadFile(type) {
    const fileInput = document.getElementById(type === "portrait" ? "portraitFile" : "documentFile");
    const did = document.getElementById("userDid").value.trim();
    const walletAddress = document.getElementById("userAddress").value.trim();
    const file = fileInput.files[0];

    if (!file || !did || !walletAddress) {
        alert("Vui lòng nhập đủ Ví, DID và chọn file.");
        return;
    }

    const publicKey = await fetchPublicKey(walletAddress);
    if (!publicKey) return; // Hủy nếu không có key

    const formData = new FormData();
    formData.append("file", file);
    formData.append("public_key", publicKey);
    formData.append("did", did);

    showStatus(`Đang upload ${type} lên IPFS...`, "pending");

    try {
        const result = await apiUpload("/api/upload", formData);
        if (type === "portrait") {
            portraitCid = result.cid;
            document.getElementById("portraitCid").textContent = `CID: ${result.cid}`;
        } else {
            documentCid = result.cid;
            document.getElementById("documentCid").textContent = `CID: ${result.cid}`;
        }
        showStatus(`Upload ${type} thành công. CID: ${result.cid}`, "success");
    } catch (e) {
        showStatus(`Lỗi upload: ${e.message}`, "error");
    }
}

// [ĐÃ THÊM] Hàm tạo và upload Metadata JSON
export async function uploadMetadata() {
    if (!portraitCid || !documentCid) {
        alert("Vui lòng upload cả Ảnh chân dung và PDF trước khi tạo Metadata.");
        return;
    }

    const walletAddress = document.getElementById("userAddress").value.trim();
    const did = document.getElementById("userDid").value.trim();

    const publicKey = await fetchPublicKey(walletAddress);
    if (!publicKey) return;

    // Tạo object Metadata
    const metadataObj = {
        did: did,
        portrait_cid: portraitCid,
        document_cid: documentCid,
        timestamp: new Date().toISOString()
    };

    // Chuyển Object thành File JSON
    const blob = new Blob([JSON.stringify(metadataObj, null, 2)], { type: "application/json" });
    const file = new File([blob], "metadata.json", { type: "application/json" });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("public_key", publicKey);
    formData.append("did", did);

    showStatus("Đang upload Metadata JSON lên IPFS...", "pending");

    try {
        const result = await apiUpload("/api/upload", formData);
        document.getElementById("metadataCid").textContent = `CID: ${result.cid}`;
        
        // Gán Hash và CID của file JSON vào form gửi Blockchain
        document.getElementById("docHash").value = result.doc_hash;
        document.getElementById("ipfsCid").value = result.cid;
        
        showStatus(`Upload Metadata thành công. Sẵn sàng gửi Blockchain.`, "success");
    } catch (e) {
        showStatus(`Lỗi upload Metadata: ${e.message}`, "error");
    }
}

export async function storeHash() {
    const walletAddress = document.getElementById("userAddress").value.trim();
    const hash = document.getElementById("docHash").value.trim();
    const cid = document.getElementById("ipfsCid").value.trim();
    const creatorAddress = document.getElementById("creatorAddress").value.trim();

    if (!walletAddress || !hash || !cid || !creatorAddress) {
        alert("Vui lòng điền đầy đủ thông tin (Cần hoàn tất upload Metadata trước).");
        return;
    }

    showStatus("Đang gửi giao dịch lên blockchain...", "pending");

    try {
        const result = await apiFetch("/api/did/store-hash", {
            method: "POST",
            body: JSON.stringify({
                wallet_address: walletAddress,
                doc_hash: hash,
                cid: cid,
                creator_address: creatorAddress,
            }),
        });
        const explorerLink = `${BLOCK_EXPLORER_URL}${result.tx_hash}`;
        showStatus(
            `Giao dịch đã gửi. TX: <a href="${explorerLink}" target="_blank">${result.tx_hash}</a>`,
            "success"
        );
    } catch (e) {
        showStatus(`Lỗi: ${e.message}`, "error");
    }
}

function showStatus(message, type) {
    const box = document.getElementById("txStatus");
    box.innerHTML = message;
    box.className = `status-box ${type}`;
    box.classList.remove("hidden");
}

// Khai báo global
window.loadPendingRequests = loadPendingRequests;
window.selectUser = selectUser;
window.uploadFile = uploadFile;
window.uploadMetadata = uploadMetadata;
window.storeHash = storeHash;
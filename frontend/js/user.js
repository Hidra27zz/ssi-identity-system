/**
 * Logic cho User Dashboard.
 * Nguoi phu trach: Phuc
 */
import { apiFetch } from "./api.js";

// [ĐÃ SỬA] Chuyển từ query parameter sang request body
export async function generateKeypair() {
    const walletAddress = document.getElementById("walletAddress").value.trim();
    if (!walletAddress) {
        alert("Vui lòng nhập địa chỉ ví trước.");
        return;
    }

    try {
        const result = await apiFetch(`/api/crypto/generate-keypair`, {
            method: "POST",
            body: JSON.stringify({ wallet_address: walletAddress })
        });
        document.getElementById("publicKeyDisplay").value = result.public_key;
        document.getElementById("privateKeyDisplay").value = result.private_key;
        document.getElementById("keypairResult").classList.remove("hidden");
        alert(result.message || "Tạo Keypair thành công!");
    } catch (e) {
        alert(`Lỗi: ${e.message}`);
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
}

// [ĐÃ SỬA] Gửi wallet_address và did thay vì public_key
export async function createDID() {
    const address = document.getElementById("createDidAddress").value.trim();
    const didString = document.getElementById("createDidString").value.trim();
    
    if (!address || !didString) {
        alert("Vui lòng nhập đủ địa chỉ ví và chuỗi DID.");
        return;
    }

    try {
        const result = await apiFetch(`/api/did/create`, {
            method: "POST",
            body: JSON.stringify({ 
                wallet_address: address, 
                did: didString 
            })
        });
        // API của bạn trả về status: "pending"
        alert(`Tạo DID thành công! Hash giao dịch: ${result.tx_hash}`);
    } catch (e) {
        alert(`Lỗi: ${e.message}`);
    }
}

// [ĐÃ SỬA] Thêm các trường dữ liệu bị thiếu
export async function loadDIDInfo() {
    const address = document.getElementById("checkAddress").value.trim();
    if (!address) return;

    try {
        const result = await apiFetch(`/api/did/record/${address}`);
        document.getElementById("didValue").textContent = result.did || "Chưa có";
        
        const statusEl = document.getElementById("didStatus");
        statusEl.textContent = result.status;
        statusEl.className = `status-badge ${result.status}`;
        
        document.getElementById("didCid").textContent = result.ipfs_cid || "Chưa có";
        
        // Render thêm 3 trường dữ liệu mới
        document.getElementById("didCreatedAt").textContent = result.created_at || "N/A";
        document.getElementById("didVerifiedAt").textContent = result.verified_at || "Chưa xác minh";
        document.getElementById("didUpdateCount").textContent = result.update_count ?? 0;

        document.getElementById("didInfo").classList.remove("hidden");
    } catch (e) {
        alert(`Lỗi: ${e.message}`);
    }
}

// [ĐÃ SỬA] Đọc mảng result.tokens thay vì result.token_id
export async function checkNFT() {
    const address = document.getElementById("nftAddress").value.trim();
    if (!address) return;

    try {
        const result = await apiFetch(`/api/nft/status/${address}`);
        document.getElementById("hasToken").textContent = result.has_valid_token ? "Có" : "Không";
        
        const tokenListEl = document.getElementById("tokenList");
        tokenListEl.innerHTML = ""; // Xóa dữ liệu cũ

        // Xử lý mảng tokens
        if (result.tokens && result.tokens.length > 0) {
            result.tokens.forEach((token, index) => {
                const div = document.createElement("div");
                div.style.padding = "10px";
                div.style.borderLeft = "2px solid #ccc";
                div.style.marginTop = "10px";
                div.innerHTML = `
                    <strong>Token #${index + 1}</strong><br/>
                    Token ID: ${token.token_id || token}<br/>
                    Metadata URI: ${token.metadata_uri || "N/A"}
                `;
                tokenListEl.appendChild(div);
            });
        } else {
            tokenListEl.innerHTML = "<p><i>Không tìm thấy Token ID nào.</i></p>";
        }

        document.getElementById("nftInfo").classList.remove("hidden");
    } catch (e) {
        alert(`Lỗi: ${e.message}`);
    }
}

// ==========================================
// LOGIC QUẢN LÝ CONSENT (PHÊ DUYỆT TRUY CẬP)
// ==========================================

export async function loadPendingConsents() {
    const did = document.getElementById("myDidForConsent")?.value.trim();
    // Nếu bạn đang dùng ID cũ là "consentDid", hãy sửa lại ID bên file HTML cho khớp hoặc đổi ở đây
    if (!did) {
        alert("Vui lòng nhập DID của bạn.");
        return;
    }

    const listEl = document.getElementById("consentList");
    if (!listEl) return;
    
    listEl.innerHTML = "<p>Đang tải danh sách...</p>";

    try {
        // Gọi API lấy danh sách pending dựa trên DID
        const requests = await apiFetch(`/api/consent/pending/${encodeURIComponent(did)}`);
        
        if (requests.length === 0) {
            listEl.innerHTML = "<p>✅ Không có yêu cầu truy cập nào đang chờ.</p>";
            return;
        }

        let html = "";
        requests.forEach(req => {
            const date = new Date(req.requested_at).toLocaleString("vi-VN");
            // Định dạng UI cho từng yêu cầu
            html += `
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px; background: #f9f9f9;">
                <p><strong>Người yêu cầu (Verifier):</strong> ${req.requester_address}</p>
                <p><strong>Loại dữ liệu muốn xem:</strong> <span style="color: blue; font-weight: bold;">${req.data_type}</span></p>
                <p><strong>Ngày yêu cầu:</strong> ${date}</p>
                <div style="margin-top: 10px;">
                    <button onclick="respondConsent(${req.id}, '${did}', 'approved')" style="background: #28a745; color: white; border: none; padding: 8px 12px; cursor: pointer; border-radius: 4px; margin-right: 5px;">✅ Đồng ý</button>
                    <button onclick="respondConsent(${req.id}, '${did}', 'rejected')" style="background: #dc3545; color: white; border: none; padding: 8px 12px; cursor: pointer; border-radius: 4px;">❌ Từ chối</button>
                </div>
            </div>`;
        });
        listEl.innerHTML = html;
    } catch (e) {
        listEl.innerHTML = `<p style="color: red;">Lỗi: ${e.message}</p>`;
    }
}

export async function respondConsent(consentId, ownerDid, decision) {
    const confirmMsg = decision === "approved" ? "Bạn chắc chắn muốn ĐỒNG Ý cho phép truy cập?" : "Bạn chắc chắn muốn TỪ CHỐI yêu cầu này?";
    if (!confirm(confirmMsg)) return;

    try {
        await apiFetch("/api/consent/respond", {
            method: "POST",
            body: JSON.stringify({
                consent_id: consentId,
                owner_did: ownerDid,
                decision: decision
            })
        });
        
        alert(`Đã ${decision === 'approved' ? 'PHÊ DUYỆT' : 'TỪ CHỐI'} yêu cầu thành công!`);
        // Tải lại danh sách sau khi phản hồi
        loadPendingConsents(); 
    } catch (e) {
        alert(`Lỗi khi phản hồi: ${e.message}`);
    }
}

// Khai báo các hàm ra Global để gọi được từ HTML onclick
window.generateKeypair = generateKeypair;
window.downloadPrivateKey = downloadPrivateKey;
window.createDID = createDID; 
window.loadDIDInfo = loadDIDInfo;
window.checkNFT = checkNFT;
window.loadPendingConsents = loadPendingConsents;
window.respondConsent = respondConsent;
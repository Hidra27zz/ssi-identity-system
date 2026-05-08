/**
 * Logic cho Verifier Dashboard.
 * Nguoi phu trach: Phuc
 */
import { apiFetch } from "./api.js";

export async function verifyDID() {
    const address = document.getElementById("verifyAddress").value.trim();
    if (!address) {
        alert("Vui lòng nhập địa chỉ ví cần kiểm tra.");
        return;
    }

    try {
        const result = await apiFetch(`/api/did/verify/${address}`);

        document.getElementById("resultAddress").textContent = result.address;
        
        const statusEl = document.getElementById("resultStatus");
        statusEl.textContent = result.status.toUpperCase();
        // Giả sử style.css của bạn có các class: status-badge valid, invalid, pending...
        statusEl.className = `status-badge ${result.status.toLowerCase()}`;
        
        document.getElementById("resultDid").textContent = result.did || "Không tìm thấy";
        document.getElementById("resultCid").textContent = result.cid || "N/A";
        document.getElementById("resultTime").textContent = new Date().toLocaleString("vi-VN");

        document.getElementById("verifyResult").classList.remove("hidden");
    } catch (e) {
        alert(`Lỗi xác minh: ${e.message}`);
    }
}

export async function requestConsent() {
    const ownerDid = document.getElementById("ownerDid").value.trim();
    const dataType = document.getElementById("dataType").value;
    // Đã sửa: Lấy địa chỉ Verifier từ input thay vì prompt
    const requesterAddress = document.getElementById("requesterAddress").value.trim();

    if (!ownerDid || !requesterAddress) {
        alert("Vui lòng điền đầy đủ DID chủ sở hữu và Địa chỉ ví của bạn.");
        return;
    }

    const resultBox = document.getElementById("consentResult");
    resultBox.textContent = "Đang gửi yêu cầu...";
    resultBox.style.color = "blue";

    try {
        const result = await apiFetch("/api/consent/request", {
            method: "POST",
            body: JSON.stringify({
                owner_did: ownerDid,
                requester_address: requesterAddress,
                data_type: dataType,
            }),
        });
        resultBox.textContent = `✅ Yêu cầu đã gửi. ID: ${result.consent_id}. Đang chờ chủ sở hữu phê duyệt.`;
        resultBox.style.color = "green";
    } catch (e) {
        resultBox.textContent = `❌ Lỗi: ${e.message}`;
        resultBox.style.color = "red";
    }
}
export async function accessData() {
    const consentId = document.getElementById("accessConsentId").value.trim();
    if (!consentId) {
        alert("Vui lòng nhập Consent ID.");
        return;
    }

    const resultBox = document.getElementById("accessResult");
    // Hiện hộp thoại với màu vàng (pending)
    resultBox.classList.remove("hidden");
    resultBox.className = "status-box pending";
    resultBox.innerHTML = "<strong>⏳ Đang tải dữ liệu từ Blockchain & IPFS...</strong>";

    try {
        const result = await apiFetch(`/api/consent/access/${consentId}`);
        
        // Thành công -> Đổi sang màu xanh (success)
        resultBox.className = "status-box success";
        resultBox.innerHTML = `
            <p style="margin-bottom: 8px; font-weight: bold; color: #0f5132;">✅ Truy cập thành công!</p>
            <div class="data-display">
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </div>
        `;
    } catch (e) {
        // Lỗi -> Đổi sang màu đỏ (error)
        resultBox.className = "status-box error";
        resultBox.innerHTML = `<strong>❌ Lỗi truy cập:</strong> ${e.message}`;
    }
}

// Nhớ gắn vào window
window.accessData = accessData;

window.verifyDID = verifyDID;
window.requestConsent = requestConsent;
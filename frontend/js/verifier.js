/**
 * Logic cho Verifier Dashboard.
 * Nguoi phu trach: Phuc
 */
import { apiFetch } from "./api.js";

export async function verifyDID() {
    const address = document.getElementById("verifyAddress").value.trim();
    if (!address) {
        alert("Nhap dia chi vi can kiem tra.");
        return;
    }

    try {
        const result = await apiFetch(`/api/did/verify/${address}`);

        document.getElementById("resultAddress").textContent = result.address;
        const statusEl = document.getElementById("resultStatus");
        statusEl.textContent = result.status;
        statusEl.className = `status-badge ${result.status}`;
        document.getElementById("resultDid").textContent = result.did || "Khong tim thay";
        document.getElementById("resultCid").textContent = result.cid || "N/A";
        document.getElementById("resultTime").textContent = new Date().toLocaleString("vi-VN");

        document.getElementById("verifyResult").classList.remove("hidden");
    } catch (e) {
        alert(`Loi xac minh: ${e.message}`);
    }
}

export async function requestConsent() {
    const ownerDid = document.getElementById("ownerDid").value.trim();
    const dataType = document.getElementById("dataType").value;
    const requesterAddress = prompt("Nhap dia chi vi cua ban (requester):");

    if (!ownerDid || !requesterAddress) return;

    try {
        const result = await apiFetch("/api/consent/request", {
            method: "POST",
            body: JSON.stringify({
                owner_did: ownerDid,
                requester_address: requesterAddress,
                data_type: dataType,
            }),
        });
        document.getElementById("consentResult").textContent =
            `Yeu cau da gui. ID: ${result.consent_id}. Cho chu so huu phe duyet.`;
    } catch (e) {
        document.getElementById("consentResult").textContent = `Loi: ${e.message}`;
    }
}

window.verifyDID = verifyDID;
window.requestConsent = requestConsent;

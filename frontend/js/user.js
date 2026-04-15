/**
 * Logic cho User Dashboard.
 * Nguoi phu trach: Phuc
 */
import { apiFetch } from "./api.js";

export async function generateKeypair() {
    const walletAddress = document.getElementById("walletAddress").value.trim();
    if (!walletAddress) {
        alert("Nhap dia chi vi truoc.");
        return;
    }

    try {
        const result = await apiFetch(`/api/crypto/generate-keypair?wallet_address=${encodeURIComponent(walletAddress)}`, {
            method: "POST",
        });
        document.getElementById("publicKeyDisplay").value = result.public_key;
        document.getElementById("privateKeyDisplay").value = result.private_key;
        document.getElementById("keypairResult").classList.remove("hidden");
        alert(result.message);
    } catch (e) {
        alert(`Loi: ${e.message}`);
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

export async function loadDIDInfo() {
    const address = document.getElementById("checkAddress").value.trim();
    if (!address) return;

    try {
        const result = await apiFetch(`/api/did/record/${address}`);
        document.getElementById("didValue").textContent = result.did || "Chua co";
        const statusEl = document.getElementById("didStatus");
        statusEl.textContent = result.status;
        statusEl.className = `status-badge ${result.status}`;
        document.getElementById("didCid").textContent = result.ipfs_cid || "Chua co";
        document.getElementById("didInfo").classList.remove("hidden");
    } catch (e) {
        alert(`Loi: ${e.message}`);
    }
}

export async function checkNFT() {
    const address = document.getElementById("nftAddress").value.trim();
    if (!address) return;

    try {
        const result = await apiFetch(`/api/nft/status/${address}`);
        document.getElementById("hasToken").textContent = result.has_valid_token ? "Co" : "Khong";
        document.getElementById("tokenId").textContent = result.token_id ?? "N/A";
        document.getElementById("metadataUri").textContent = result.metadata_uri ?? "N/A";
        document.getElementById("nftInfo").classList.remove("hidden");
    } catch (e) {
        alert(`Loi: ${e.message}`);
    }
}

export async function loadPendingConsents() {
    const did = document.getElementById("consentDid").value.trim();
    if (!did) return;

    try {
        const consents = await apiFetch(`/api/consent/pending/${encodeURIComponent(did)}`);
        const list = document.getElementById("consentList");
        list.innerHTML = "";

        if (consents.length === 0) {
            list.innerHTML = "<p>Khong co yeu cau nao dang cho.</p>";
            return;
        }

        consents.forEach(c => {
            const div = document.createElement("div");
            div.className = "consent-item";
            div.innerHTML = `
                <p>Tu: ${c.requester_address}</p>
                <p>Loai du lieu: ${c.data_type}</p>
                <p>Thoi gian: ${c.requested_at}</p>
                <button onclick="respondConsent(${c.id}, '${did}', 'approved')">Dong y</button>
                <button onclick="respondConsent(${c.id}, '${did}', 'rejected')">Tu choi</button>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        alert(`Loi: ${e.message}`);
    }
}

export async function respondConsent(consentId, ownerDid, decision) {
    try {
        await apiFetch("/api/consent/respond", {
            method: "POST",
            body: JSON.stringify({ consent_id: consentId, owner_did: ownerDid, decision }),
        });
        alert(`Da ${decision === "approved" ? "dong y" : "tu choi"} yeu cau.`);
        loadPendingConsents();
    } catch (e) {
        alert(`Loi: ${e.message}`);
    }
}

window.generateKeypair = generateKeypair;
window.downloadPrivateKey = downloadPrivateKey;
window.loadDIDInfo = loadDIDInfo;
window.checkNFT = checkNFT;
window.loadPendingConsents = loadPendingConsents;
window.respondConsent = respondConsent;

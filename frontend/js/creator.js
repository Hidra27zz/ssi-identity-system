/**
 * Logic cho Creator Dashboard.
 * Nguoi phu trach: Phuc
 */
import { apiFetch, apiUpload } from "./api.js";
import { BLOCK_EXPLORER_URL } from "../../shared/constants.js";

let portraitCid = "";
let documentCid = "";
let docHash = "";

export async function uploadFile(type) {
    const fileInput = document.getElementById(type === "portrait" ? "portraitFile" : "documentFile");
    const did = document.getElementById("userDid").value.trim();
    const file = fileInput.files[0];

    if (!file || !did) {
        alert("Vui long chon file va nhap DID truoc.");
        return;
    }

    // Lay public key tu server (da luu khi tao keypair)
    const walletAddress = document.getElementById("userAddress").value.trim();
    let publicKey = "";
    try {
        const record = await apiFetch(`/api/did/record/${walletAddress}`);
        // Public key duoc luu trong did_cache - lay qua endpoint rieng neu can
        // Tam thoi yeu cau nguoi dung nhap public key
        publicKey = prompt("Nhap public key PEM cua nguoi dung:");
        if (!publicKey) return;
    } catch {
        publicKey = prompt("Nhap public key PEM cua nguoi dung:");
        if (!publicKey) return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("public_key", publicKey);
    formData.append("did", did);

    showStatus("Dang upload len IPFS...", "pending");

    try {
        const result = await apiUpload("/api/upload", formData);
        if (type === "portrait") {
            portraitCid = result.cid;
            document.getElementById("portraitCid").textContent = `CID: ${result.cid}`;
        } else {
            documentCid = result.cid;
            document.getElementById("documentCid").textContent = `CID: ${result.cid}`;
            docHash = result.doc_hash;
            document.getElementById("docHash").value = docHash;
            document.getElementById("ipfsCid").value = result.cid;
        }
        showStatus(`Upload thanh cong. CID: ${result.cid}`, "success");
    } catch (e) {
        showStatus(`Loi upload: ${e.message}`, "error");
    }
}

export async function storeHash() {
    const walletAddress = document.getElementById("userAddress").value.trim();
    const hash = document.getElementById("docHash").value.trim();
    const cid = document.getElementById("ipfsCid").value.trim();
    const creatorAddress = document.getElementById("creatorAddress").value.trim();

    if (!walletAddress || !hash || !cid || !creatorAddress) {
        alert("Vui long dien day du thong tin.");
        return;
    }

    showStatus("Dang gui giao dich len blockchain...", "pending");

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
            `Giao dich da gui. TX: <a href="${explorerLink}" target="_blank">${result.tx_hash}</a>`,
            "success"
        );
    } catch (e) {
        showStatus(`Loi: ${e.message}`, "error");
    }
}

function showStatus(message, type) {
    const box = document.getElementById("txStatus");
    box.innerHTML = message;
    box.className = `status-box ${type}`;
    box.classList.remove("hidden");
}

// Gan vao window de HTML onclick hoat dong
window.uploadFile = uploadFile;
window.storeHash = storeHash;

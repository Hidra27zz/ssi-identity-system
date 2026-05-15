/**
 * auth-guard.js — Bảo vệ các trang có role (Creator / Verifier).
 */

const ZERO = "0x0000000000000000000000000000000000000000";

const ROLE_ABI = [
    "function isCreator(address addr) view returns (bool)",
];

/**
 * Hiển thị banner lỗi toàn trang khi bị từ chối quyền truy cập.
 */
function showAccessDenied(message) {
    document.body.innerHTML = `
        <div style="
            min-height:100vh;display:flex;align-items:center;justify-content:center;
            background:linear-gradient(135deg,#1a0a0a,#2d0f0f);font-family:'Inter',sans-serif;
        ">
            <div style="
                background:rgba(255,255,255,0.05);border:1px solid rgba(255,80,80,0.3);
                border-radius:16px;padding:48px 40px;max-width:480px;text-align:center;
                box-shadow:0 20px 60px rgba(0,0,0,0.5);
            ">
                <div style="font-size:3rem;margin-bottom:16px;">🚫</div>
                <h2 style="color:#ff6b6b;font-size:1.4rem;margin-bottom:12px;">Truy cập bị từ chối</h2>
                <p style="color:rgba(255,255,255,0.7);font-size:.95rem;line-height:1.6;margin-bottom:28px;">${message}</p>
                <a href="login.html" style="
                    display:inline-block;padding:12px 28px;background:#f6851b;color:#fff;
                    border-radius:8px;text-decoration:none;font-weight:600;font-size:.95rem;
                ">Quay lại đăng nhập</a>
            </div>
        </div>`;
}

/**
 * Kiểm tra quyền và trả về địa chỉ account.
 * Hỗ trợ cả đăng nhập bằng MetaMask và Mật khẩu (Session Token).
 * @param {"creator"|"verifier"|"user"} requiredRole
 * @returns {Promise<string>} địa chỉ account đã xác thực (lowercase)
 */
export async function requireRole(requiredRole) {
    let currentAccount = "";
    let provider = null;
    let isMetaMask = false;

    // 1. Đọc constants trước
    let DID_REGISTRY_ADDRESS, CHAIN_ID;
    try {
        const mod = await import("/shared/constants.js");
        DID_REGISTRY_ADDRESS = mod.DID_REGISTRY_ADDRESS;
        CHAIN_ID = Number(mod.CHAIN_ID);
    } catch {
        showAccessDenied("Không tải được cấu hình hệ thống (shared/constants.js).");
        throw new Error("No constants");
    }

    if (!DID_REGISTRY_ADDRESS || DID_REGISTRY_ADDRESS === ZERO) {
        showAccessDenied("Contract chưa được deploy. Liên hệ admin.");
        throw new Error("No contract");
    }

    // 2. Kiểm tra phương thức đăng nhập
    const sessionToken = localStorage.getItem("ssi_sessionToken");

    if (sessionToken) {
        // --- LUỒNG MẬT KHẨU (Session Token) ---
        try {
            const res = await fetch(`/api/auth/session?token=${sessionToken}`);
            if (!res.ok) throw new Error("Session hết hạn");
            const data = await res.json();
            currentAccount = data.wallet_address.toLowerCase();

            // Khởi tạo RPC Provider công khai
            const rpcUrl = CHAIN_ID === 31337 ? "http://127.0.0.1:8545" : "https://ethereum-sepolia-rpc.publicnode.com";
            provider = new window.ethers.JsonRpcProvider(rpcUrl);
        } catch (e) {
            showAccessDenied("Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.");
            localStorage.removeItem("ssi_sessionToken");
            throw e;
        }
    } else {
        // --- LUỒNG METAMASK ---
        isMetaMask = true;
        if (!window.ethereum) {
            showAccessDenied("Vui lòng cài đặt MetaMask hoặc đăng nhập bằng Mật khẩu.");
            throw new Error("No MetaMask");
        }

        const accounts = await window.ethereum.request({ method: "eth_accounts" });
        if (!accounts || accounts.length === 0) {
            showAccessDenied(
                "Bạn chưa đăng nhập. Vui lòng kết nối MetaMask tại trang <a href='login.html' style='color:#f6851b'>Login</a> trước khi vào trang này."
            );
            throw new Error("Not connected");
        }
        currentAccount = accounts[0].toLowerCase();

        provider = new window.ethers.BrowserProvider(window.ethereum);
        const net = await provider.getNetwork();
        const connectedChain = Number(net.chainId);
        if (connectedChain !== CHAIN_ID) {
            showAccessDenied(
                `Sai mạng blockchain. Đang ở chainId <strong>${connectedChain}</strong>, cần <strong>${CHAIN_ID}</strong>.<br>
                 Hãy chuyển mạng trong MetaMask rồi đăng nhập lại.`
            );
            throw new Error("Wrong chain");
        }

        // Lắng nghe đổi account
        window.ethereum.on("accountsChanged", () => {
            if (!localStorage.getItem("ssi_sessionToken")) {
                sessionStorage.removeItem("ssi_connectedAccount");
                sessionStorage.removeItem("ssi_role");
                window.location.href = "login.html";
            }
        });
    }

    // 3. Kiểm tra role theo loại
    if (requiredRole === "creator") {
        const registry = new window.ethers.Contract(DID_REGISTRY_ADDRESS, ROLE_ABI, provider);
        let hasCreatorRole = false;
        try {
            hasCreatorRole = await registry.isCreator(currentAccount);
        } catch (e) {
            showAccessDenied("Lỗi khi đọc smart contract: " + e.message);
            throw e;
        }

        if (!hasCreatorRole) {
            showAccessDenied(
                `Tài khoản <code style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px;font-size:.85em;">
                ${currentAccount.slice(0, 8)}…${currentAccount.slice(-6)}</code>
                không có quyền <strong>Identity Creator</strong> trên smart contract.<br><br>
                Nếu bạn là Creator, hãy chắc chắn đã chọn đúng tài khoản.
                Liên hệ admin để được cấp quyền qua <code>grantCreatorRole()</code>.`
            );
            throw new Error("Access denied: not creator");
        }
    }

    // 4. Đồng bộ storage
    try {
        sessionStorage.setItem("ssi_connectedAccount", currentAccount);
        sessionStorage.setItem("ssi_role", requiredRole);
        localStorage.setItem("ssi_walletAddress", currentAccount);
    } catch {}

    return currentAccount;
}


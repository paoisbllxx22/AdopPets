// ============================
// Estado global simple
// ============================
let currentUser = null;            // { id, name, avatar }
let currentChatUser = null;        // { id, name, avatar }
let chatSocket = null;


// ============================
// Cargar datos del usuario
// ============================
async function loadUser() {
    try {
        const res = await fetch("/users/me", {
            credentials: "include"  // usa cookie access_token
        });

        if (res.status === 401 || res.status === 403) {
            window.location.href = "/login";
            return;
        }

        const data = await res.json();

        currentUser = {
            id: data.id,
            name: data.name,
            avatar: data.profile_image || "/static/img/default-avatar.png"
        };

        document.getElementById("username").textContent = currentUser.name;
        document.getElementById("profile-pic").src = currentUser.avatar;

    } catch (error) {
        console.error("Error cargando usuario:", error);
        window.location.href = "/login";
    }
}


// ============================
// Cargar feed de publicaciones
// ============================
async function loadFeed() {
    try {
        const res = await fetch("/posts/feed/all");
        if (!res.ok) {
            console.error("Error cargando feed");
            return;
        }

        const posts = await res.json();
        const container = document.getElementById("feed-container");
        container.innerHTML = "";

        posts.forEach(p => {
            const postUserAvatar =
                p.user_profile_image || "/static/img/default-avatar.png";

            const isMine = currentUser && p.user_id === currentUser.id;

            container.innerHTML += `
                <div class="post-card">
                    <div class="post-header">
                        <div class="post-user">
                            <img
                                src="${postUserAvatar}"
                                class="post-avatar"
                            >
                            <span class="post-username">${p.user_name || "Usuario"}</span>
                        </div>
                        ${
                            isMine
                                ? ""
                                : `<button
                                        class="post-message-btn"
                                        data-user-id="${p.user_id}"
                                        data-user-name="${p.user_name || 'Usuario'}"
                                        data-user-avatar="${postUserAvatar}"
                                    >
                                        Enviar mensaje
                                   </button>`
                        }
                    </div>

                    ${
                        p.image_url
                            ? `<img src="${p.image_url}" class="post-image">`
                            : ""
                    }

                    <div class="post-content">
                        <h3>${p.title}</h3>
                        <p>${p.description}</p>
                    </div>
                </div>
            `;
        });

        // Después de renderizar, enganchar los botones de mensaje
        attachMessageButtons();

    } catch (error) {
        console.error("Error cargando publicaciones:", error);
    }
}


// ============================
// Enganchar botones "Enviar mensaje"
// ============================
function attachMessageButtons() {
    const buttons = document.querySelectorAll(".post-message-btn");

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            const otherUserId = btn.dataset.userId;
            const otherUserName = btn.dataset.userName;
            const otherUserAvatar = btn.dataset.userAvatar;

            if (!currentUser || otherUserId === currentUser.id) {
                // No tiene sentido enviarse mensaje a sí misma
                return;
            }

            openChatPopup({
                id: otherUserId,
                name: otherUserName,
                avatar: otherUserAvatar
            });
        });
    });
}


// ============================
// Popup de chat
// ============================
function openChatPopup(otherUser) {
    currentChatUser = otherUser;

    // Mostrar overlay + modal
    document.getElementById("chat-overlay").classList.remove("hidden");
    document.getElementById("chat-modal").classList.remove("hidden");

    // Datos en el header
    document.getElementById("chat-user-name").textContent = otherUser.name;
    document.getElementById("chat-user-avatar").src = otherUser.avatar;

    // Limpiar mensajes previos
    const list = document.getElementById("chat-messages");
    list.innerHTML = "";

    // Cerrar socket anterior si existe
    if (chatSocket) {
        chatSocket.close();
        chatSocket = null;
    }

    // 1) Cargar historial por HTTP
    loadChatHistory(otherUser.id);

    // 2) Abrir WebSocket
    openChatSocket(otherUser.id);
}

function closeChatPopup() {
    document.getElementById("chat-overlay").classList.add("hidden");
    document.getElementById("chat-modal").classList.add("hidden");

    if (chatSocket) {
        chatSocket.close();
        chatSocket = null;
    }
}


// ============================
// Historial HTTP
// ============================
async function loadChatHistory(otherUserId) {
    try {
        const res = await fetch(`/chat/messages/${otherUserId}`, {
            credentials: "include"
        });

        if (!res.ok) {
            console.warn("No se pudo cargar el historial de chat");
            return;
        }

        const messages = await res.json();
        const list = document.getElementById("chat-messages");
        list.innerHTML = "";

        messages.forEach(msg => {
            appendMessageBubble(msg);
        });

        // Scroll al final
        list.scrollTop = list.scrollHeight;

    } catch (err) {
        console.error("Error cargando historial de chat:", err);
    }
}


// ============================
// WebSocket
// ============================
function openChatSocket(otherUserId) {
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${location.host}/chat/ws/${otherUserId}`;

    const list = document.getElementById("chat-messages");

    chatSocket = new WebSocket(wsUrl);

    chatSocket.onopen = () => {
        console.log("WebSocket de chat conectado");
    };

    chatSocket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            appendMessageBubble(msg);
            list.scrollTop = list.scrollHeight;
        } catch (e) {
            console.error("Error parseando mensaje de WS:", e);
        }
    };

    chatSocket.onclose = () => {
        console.log("WebSocket de chat cerrado");
    };

    chatSocket.onerror = (e) => {
        console.error("Error en WebSocket:", e);
    };
}


// Crea una burbujita en el popup
function appendMessageBubble(msg) {
    if (!currentUser) return;

    const list = document.getElementById("chat-messages");

    const div = document.createElement("div");
    div.classList.add("chat-message");

    const isMine = msg.sender_id === currentUser.id;
    div.classList.add(isMine ? "me" : "them");

    div.textContent = msg.content;

    list.appendChild(div);
}


// ============================
// Envío de mensaje desde el form del popup
// ============================
function setupChatForm() {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;

        const text = input.value.trim();
        if (!text) return;

        chatSocket.send(text);
        input.value = "";
    });
}


// ============================
// Chat sidebar (futuro)
// ============================
// Aquí luego podemos enganchar “Mis chats” + puntito rojo


// ============================
// Inicializar Home
// ============================
document.addEventListener("DOMContentLoaded", () => {
    loadUser().then(() => {
        loadFeed();
    });

    // Botón cerrar popup
    document.getElementById("chat-close-btn")
        .addEventListener("click", closeChatPopup);

    document.getElementById("chat-overlay")
        .addEventListener("click", closeChatPopup);

    setupChatForm();
});

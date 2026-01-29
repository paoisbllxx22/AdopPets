/* ==================================================
   Cargar datos del usuario (avatar + nombre)
================================================== */
async function loadProfileUser() {
    try {
        const res = await fetch("/users/me", {
            credentials: "include"
        });

        if (!res.ok) {
            console.error("Error cargando usuario");
            return;
        }

        const user = await res.json();

        // Nombre
        const nameEl = document.getElementById("profile-name");
        if (nameEl) {
            nameEl.textContent = user.name;
        }

        // Avatar
        const avatarEl = document.getElementById("profile-avatar");
        if (avatarEl) {
            avatarEl.src =
                user.profile_image || "/static/img/default-avatar.svg";
        }

    } catch (err) {
        console.error("Error cargando perfil:", err);
    }
}





/* ==================================================
   PROFILE.JS
   Lógica del perfil tipo Instagram (AdopPet)
   ================================================== */

document.addEventListener("DOMContentLoaded", () => {
    loadProfileUser();
    loadMyPosts();
});

/* ==================================================
   Cargar publicaciones del usuario autenticado
   (NO usamos USER_ID)
================================================== */
async function loadMyPosts() {
    try {
        const res = await fetch("/posts/user/me", {
            credentials: "include"
        });

        if (!res.ok) {
            console.error("Error cargando publicaciones");
            return;
        }

        const posts = await res.json();

        const container = document.getElementById("profile-posts");
        container.innerHTML = "";

        if (!posts || posts.length === 0) {
            container.innerHTML =
                "<p style='color:black; margin-top:20px;'>No tienes publicaciones todavía.</p>";
            return;
        }

        posts.forEach(post => {
            container.appendChild(renderPost(post));
        });

    } catch (err) {
        console.error("Error cargando posts:", err);
    }
}

/* ==================================================
   Render de cada post (card + overlay)
================================================== */
function renderPost(post) {
    const wrapper = document.createElement("div");
    wrapper.className = "profile-post";

    /* Imagen */
    const img = document.createElement("img");
    img.src = post.image_url || "/static/img/default-avatar.svg";
    img.alt = post.title || "Publicación";

    /* Overlay */
    const overlay = document.createElement("div");
    overlay.className = "post-overlay";

    const editBtn = document.createElement("button");
    editBtn.className = "edit-btn";
    editBtn.innerText = "✏️";
    editBtn.onclick = () =>
        openEditModal(
            post.id,
            post.title || "",
            post.description || "",
            post.details || ""
        );

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-btn";
    deleteBtn.innerText = "🗑";
    deleteBtn.onclick = () => deletePost(post.id);

    overlay.appendChild(editBtn);
    overlay.appendChild(deleteBtn);

    /* Info debajo (tipo tarjeta) */
    const info = document.createElement("div");
    info.className = "profile-post-info";

    const title = document.createElement("h4");
    title.textContent = post.title || "Sin título";

    const desc = document.createElement("p");
    desc.textContent = post.description || "";

    info.appendChild(title);
    info.appendChild(desc);

    /* Ensamblar */
    wrapper.appendChild(img);
    wrapper.appendChild(overlay);
    wrapper.appendChild(info);

    return wrapper;
}


/* ==================================================
   Eliminar publicación
================================================== */
async function deletePost(postId) {
    const confirmDelete = confirm("¿Seguro que deseas eliminar esta publicación?");
    if (!confirmDelete) return;

    try {
        const res = await fetch(`/posts/${postId}`, {
            method: "DELETE",
            credentials: "include"
        });

        if (!res.ok) {
            alert("No se pudo eliminar la publicación");
            return;
        }

        loadMyPosts();

    } catch (err) {
        console.error("Error eliminando post:", err);
    }
}

/* ==================================================
   Modal editar
================================================== */
function openEditModal(id, title, description, details) {
    document.getElementById("edit-post-id").value = id;
    document.getElementById("edit-title").value = title;
    document.getElementById("edit-description").value = description;
    document.getElementById("edit-details").value = details;

    document.getElementById("edit-modal").classList.remove("hidden");
}

function closeEditModal() {
    document.getElementById("edit-modal").classList.add("hidden");
}

/* ==================================================
   Guardar cambios (UPDATE)
================================================== */
const editForm = document.getElementById("edit-form");

if (editForm) {
    editForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const postId = document.getElementById("edit-post-id").value;

        const formData = new FormData();
        formData.append("title", document.getElementById("edit-title").value);
        formData.append("description", document.getElementById("edit-description").value);
        formData.append("details", document.getElementById("edit-details").value);

        try {
            const res = await fetch(`/posts/${postId}`, {
                method: "PUT",
                body: formData,
                credentials: "include"
            });

            if (!res.ok) {
                alert("Error actualizando publicación");
                return;
            }

            closeEditModal();
            loadMyPosts();

        } catch (err) {
            console.error("Error actualizando post:", err);
        }
    });
}

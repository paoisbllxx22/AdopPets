# Guía de Automatización con GitHub Actions

Para que el despliegue funcione automáticamente cuando subes cambios a GitHub, necesitas configurar algunas cosas de seguridad.

## 1. Preparar el Servidor para Git (IMPORTANTE)
El comando automático hará un `git pull`. Para que esto funcione, la carpeta en el servidor **TIENE QUE SER** un repositorio de Git conectado a tu GitHub.

Si solo copiaste los archivos con `scp`, esto fallará. Tienes dos opciones en el servidor VPS:

### Opción A (Recomendada): Clonar de cero
Borra la carpeta actual y clona tu repositorio (te pedirá tu usuario/token de github):
```bash
# En el VPS
cd ~
rm -rf AdopPets
git clone https://github.com/TU_USUARIO/TU_REPO.git AdopPets
cd AdopPets
```

### Opción B: Conectar la carpeta existente (Si ya subiste archivos manual)
```bash
# En el VPS
cd ~/AdopPets
git init
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git fetch --all
git reset --hard origin/main
git branch -u origin/main main
```

---

## 2. Configurar Llaves SSH (Para que GitHub entre al VPS)
GitHub Actions necesita una "llave" para entrar a tu servidor sin escribir contraseña.

### En tu PC Local (Generar Llave):
Genera una nueva par de llaves **sin contraseña** (dale Enter a todo):
```bash
ssh-keygen -t rsa -b 4096 -f gh_action_key -C "github-actions"
```

Esto creará dos archivos: `gh_action_key` (privada) y `gh_action_key.pub` (pública).

### En el VPS (Autorizar Llave):
Copia el contenido de `gh_action_key.pub` y agrégalo al archivo de llaves autorizadas en el servidor:
```bash
# En el servidor
echo "PEGA_AQUI_EL_CONTENIDO_DE_LA_PUB" >> ~/.ssh/authorized_keys
```

---

## 3. Configurar Secretos en GitHub
Para no exponer tus contraseñas, configuramos "Secretos" en el repositorio.

1.  Ve a tu repositorio en GitHub -> **Settings** -> **Secrets and variables** -> **Actions**.
2.  Crea los siguientes secretos (New repository secret):

| Nombre | Valor |
| :--- | :--- |
| **VPS_HOST** | `34.51.71.65` |
| **VPS_USER** | Tu nombre de usuario en el servidor (ej: `root`, `ubuntu`, `paola`) |
| **SSH_PRIVATE_KEY** | Copia y pega TODO el contenido del archivo `gh_action_key` (el que no tiene extensión .pub) |

---

## ¡Listo!
Ahora, cada vez que hagas un `git push` a la rama `main`, GitHub:
1.  Se conectará a tu VPS.
2.  Bajará los últimos cambios (`git pull`).
3.  Reconstruirá las imágenes Docker.
4.  Actualizará Kubernetes automáticamente.

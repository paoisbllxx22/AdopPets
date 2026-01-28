# Guía de Despliegue en VPS (IP: 34.51.71.65)

Esta guía asume que estás utilizando un servidor Linux (Ubuntu/Debian) en **Google Cloud Platform (GCP)** y que deseas desplegar la aplicación AdopPets utilizando Kubernetes (K3s).

## PASO 0: Configurar Firewall de Google Cloud (CRÍTICO)
Por defecto, Google Cloud bloquea el tráfico en puertos como el 8000. Debes permitir el tráfico para ver tu aplicación.

1.  Ve a la consola de Google Cloud -> VPC Network -> Firewall.
2.  Crea una regla de firewall:
    *   **Nombre**: `allow-adoppets-8000`
    *   **Targets**: `All instances in the network` (o usa los tags de tu instancia).
    *   **Source filter**: `IPv4 ranges`
    *   **Source IP ranges**: `0.0.0.0/0` (Permite acceso desde cualquier lugar)
    *   **Protocols and ports**: `tcp:8000`
3.  Guarda la regla. Sin esto, no podrás acceder a la web aunque todo esté funcionando.

---

## Prerrequisitos en tu PC Local
Asegúrate de tener acceso SSH al servidor (archivo .pem o contraseña).

---

## PASO 1: Preparar el VPS (Ejecutar en el VPS)

Conéctate a tu VPS:
`ssh tu_usuario@34.51.71.65`

### 1.1 Instalar Docker
Docker es necesario para "construir" las imágenes de tus aplicaciones.

```bash
# Actualizar paquetes
sudo apt-get update

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Dar permisos al usuario actual (para no usar sudo con docker siempre)
sudo usermod -aG docker $USER
newgrp docker
```

### 1.2 Instalar K3s (Kubernetes Ligero)
K3s es una distribución de Kubernetes certificada, muy liviana, perfecta para un solo servidor.

```bash
# Instalar K3s
curl -sfL https://get.k3s.io | sh -

# Configurar permisos para poder usar el comando `kubectl`
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
echo "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml" >> ~/.bashrc
source ~/.bashrc

# Verificar instalación
kubectl get nodes
# Deberías ver tu nodo en estado "Ready"
```

---

## PASO 2: Subir el Código (Ejecutar desde tu PC Local)

Necesitamos copiar la carpeta de tu proyecto al servidor. Abre una terminal (PowerShell o CMD) en tu computadora, NO en el VPS.

Asegúrate de estar en la carpeta *padre* de `AdopPets` (o ajusta la ruta).

```powershell
# Comando de ejemplo (reemplaza 'usuario' con tu usuario del VPS, ej: root o ubuntu)
scp -r "c:\Users\anjag\Downloads\Proyecto pao\AdopPets" usuario@34.51.71.65:~/AdopPets
```

*Nota: Te pedirá la contraseña del VPS si no usas claves SSH.*

---

## PASO 3: Construir e Importar Imágenes (Ejecutar en el VPS)

Vuelve a tu terminal del VPS. Ahora vamos a convertir tu código en "Imágenes Docker" y decírselo a Kubernetes.

```bash
cd ~/AdopPets

# 1. Construir Backend
# (Asegúrate de que estás en la carpeta correcta donde está el Dockerfile del Backend)
docker build -t backend-service:latest ./Backend

# 2. Construir Auth Service
docker build -t auth-service:latest ./auth_service

# 3. Importar imágenes a K3s
# K3s no ve automáticamente las imágenes de Docker, hay que importarlas manualmente si no usas Docker Hub.
docker save backend-service:latest | sudo k3s ctr images import -
docker save auth-service:latest | sudo k3s ctr images import -
```

---

## PASO 4: Desplegar en Kubernetes (Ejecutar en el VPS)

Finalmente, aplicamos los archivos de configuración que creamos en la carpeta `k8s`.

```bash
# Aplicar configuraciones
kubectl apply -f k8s/

# Verificar estado
kubectl get pods
```

Deberías ver 3 pods (mongo, auth-service, backend-service) cambiando de estado `ContainerCreating` a `Running`.

### Acceder a la aplicación
El servicio `backend-service` está configurado como `LoadBalancer`. En K3s, esto usará la IP pública de tu VPS automáticamente (gracias a Klipper LB).

Prueba acceder en tu navegador:
`http://34.51.71.65:8000`

---

## Comandos Útiles para depuración

*   **Ver logs de un pod**: `kubectl logs <nombre-del-pod>`
*   **Ver detalles de error**: `kubectl describe pod <nombre-del-pod>`
*   **Reiniciar todo**: `kubectl delete -f k8s/ && kubectl apply -f k8s/`

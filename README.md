# Knowmad Writer - Bot de Telegram para Gestión de Contenido Web

## 📋 Descripción

Knowmad Writer es un bot de Telegram diseñado para gestionar el contenido de sitios web a través de una interfaz conversacional intuitiva. Permite a los usuarios subir contenido HTML, procesar imágenes y publicarlos en sus propios servidores web mediante SFTP, todo ello desde la comodidad de Telegram.

## 🌟 Características principales

- **🔐 Sistema de usuarios** con roles y permisos (administrador/usuario)
- **🌐 Configuración de sitios web** con nombre y dominio
- **📤 Conexión SFTP** para publicación directa en servidores
  - Prueba de conexión para verificar credenciales
  - Explorador de directorios para seleccionar carpetas
  - Subida automática de archivos a tu servidor web
- **📋 Plantillas HTML personalizables** con sistema de placeholders
- **🏷️ Gestión de categorías y etiquetas** para organizar el contenido
- **📝 Creación y edición de posts** con soporte para HTML enriquecido
- **🖼️ Gestión de imágenes** para contenido visual
- **🤖 Interfaz conversacional** mediante botones interactivos
- **📊 Gestión automática de JSON**: Actualización de archivos JSON para listados y estadísticas

## 🗄️ Estructura de datos JSON

El sistema mantiene tres archivos JSON principales por cliente:

1. **posts.json**: Mini listado con información de cada post (id, título, slug, descripción, categoría, etiquetas, fecha)
2. **categories.json**: Información de categorías con contadores automáticos (nombre, color, contador)
3. **tags.json**: Información de etiquetas con contadores automáticos (nombre, contador)

## 🛠️ Instalación y configuración

### Requisitos previos

- Python 3.8+
- Cuenta de Telegram
- Bot de Telegram creado a través de @BotFather
- Servidor con soporte SFTP para alojar el contenido

### Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/idtla/knowmadwriter.git
   cd knowmadwriter
   ```

2. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno:
   - Crear un archivo `.env` en la carpeta raíz con el siguiente contenido:
     ```
     TELEGRAM_BOT_TOKEN=tu_token_de_telegram
     ADMIN_USER_ID=tu_id_de_telegram_aquí
     DATABASE_PATH=./database/knomad.db
     ENCRYPTION_KEY=clave_secreta_para_cifrar_contraseñas_sftp
     DEBUG=True
     LOG_LEVEL=INFO
     LOG_DIR=./logs
     ```

4. Iniciar el bot:
   ```
   cd telegram_bot
   python app.py
   ```

## 🤖 Uso del bot

### Comandos principales

- `/start` - Iniciar el bot y mostrar menú principal
- `/register` - Registrarse como usuario (requiere autorización)
- `/newpost` - Crear un nuevo post
- `/categories` - Gestionar categorías
- `/tags` - Gestionar etiquetas
- `/settings` - Configurar opciones del sitio y SFTP
- `/help` - Mostrar ayuda y comandos disponibles

### Flujo de trabajo básico

1. **Registro**: Los usuarios deben ser pre-registrados por un administrador y luego completar su registro
2. **Configuración**: Configurar el sitio web (nombre, dominio) y conexión SFTP
3. **Plantilla**: 
   - Subir una plantilla HTML personalizada con los placeholders correspondientes
   - Los placeholders no reconocidos se configuran como campos personalizados (texto, número, URL o desplegable)
   - El sistema almacena la configuración de placeholders personalizados para cada sitio
4. **Creación de contenido**: 
   - Crear posts utilizando HTML e imágenes
   - Completar campos estándar y personalizados específicos de la plantilla
5. **Publicación**: 
   - El contenido se sube automáticamente al servidor configurado
   - Se actualizan los archivos JSON para listados y estadísticas

## 📄 Sistema de plantillas

### Placeholders

El sistema utiliza plantillas HTML con placeholders que se reemplazan con contenido dinámico.

#### Obligatorios:
- `{{TITLE}}` - Título del post
- `{{SITE_NAME}}` - Nombre del sitio
- `{{META_DESCRIPTION}}` - Meta descripción
- `{{FEATURE_IMAGE}}` - Imagen principal
- `{{PUBLISHED_TIME}}` - Fecha de publicación
- `{{CATEGORY}}` - Categoría
- `{{SITE_URL}}` - URL del sitio
- `{{ARTICLE_URL}}` - URL del artículo
- `{{CONTENT}}` - Contenido HTML

#### Generados automáticamente:
- `{{SITE_NAME}}` - Nombre del sitio (de la configuración)
- `{{SLUG}}` - URL amigable (generado a partir del título)

#### Opcionales:
- `{{LAST_MODIFIED}}` - Última modificación
- `{{FEATURE_IMAGE_ALT}}` - Texto alternativo de imagen
- `{{READING_TIME}}` - Tiempo estimado de lectura
- `{{SOURCE_LIST}}` - Lista de fuentes


#### Personalizados:
El sistema permite definir placeholders personalizados para adaptarse a las necesidades específicas:
- **Detección**: Al subir una plantilla, se detectan automáticamente placeholders no reconocidos
- **Configuración**: Para cada placeholder personalizado, se define:
  - Nombre para mostrar en formularios
  - Tipo de dato (texto, número, URL, desplegable)
  - Opciones disponibles (para tipo desplegable)
- **Validación**: Los valores se validan según el tipo de dato configurado
- **Almacenamiento**: La configuración se guarda asociada al sitio específico
- **Compatibilidad**: Mantiene compatibilidad con posts existentes si cambia la configuración

### Ejemplo de plantilla básica

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}} - {{SITE_NAME}}</title>
    <meta name="description" content="{{META_DESCRIPTION}}">
    <meta property="og:image" content="{{FEATURE_IMAGE}}">
    <meta property="og:published_time" content="{{PUBLISHED_TIME}}">
</head>
<body>
    <header>
        <h1>{{TITLE}}</h1>
        <div class="category">{{CATEGORY}}</div>
    </header>
    <main>
        <article>
            {{CONTENT}}
        </article>
    </main>
</body>
</html>
```

## 📂 Estructura del proyecto

```
knowmadwriter/
├── telegram_bot/
│   ├── app.py                  # Punto de entrada principal
│   ├── core/                   # Funcionalidad central
│   │   ├── handlers.py         # Manejadores principales
│   │   └── states.py           # Gestión de estados de conversación
│   ├── database/               # Conexión a base de datos
│   ├── models/                 # Modelos de datos
│   ├── modules/                # Módulos funcionales
│   │   ├── auth/               # Autenticación
│   │   ├── content/            # Gestión de contenido
│   │   ├── sftp/               # Conexión SFTP
│   │   ├── categories/         # Gestión de categorías
│   │   └── tags/               # Gestión de etiquetas
│   └── utils/                  # Utilidades
└── data/                       # Datos persistentes
    └── templates/              # Plantillas predefinidas
```

## 🧠 Referencia de Handlers

Esta sección describe los principales manejadores (handlers) del bot y su función en el sistema.

### Handlers de Navegación

- **`send_main_menu`**: Muestra el menú principal con botones interactivos adaptados al rol del usuario.
- **`send_settings_menu`**: Muestra el menú de configuración con opciones para sitio web, SFTP y plantillas.
- **`callback_handler`**: Procesa todas las interacciones con botones, dirigiendo a las funciones específicas según la acción seleccionada.

### Handlers de Comandos

- **`start_command`**: Inicia el bot, muestra el logo y verifica si el usuario está registrado.
- **`help_command`**: Muestra la lista de comandos disponibles y ayuda general.
- **`whoami_command`**: Muestra información del usuario actual (ID, nombre, rol, estado).
- **`admin_command`**: Proporciona acceso al panel de administración (solo para administradores).

### Handlers de Mensajes

- **`message_handler`**: Procesa todos los mensajes de texto según el estado actual del usuario.
- **`auth_message_handler`**: Maneja los mensajes durante el proceso de registro/autenticación.
- **`content_message_handler`**: Procesa mensajes durante la creación o edición de contenido.
- **`sftp_message_handler`**: Gestiona mensajes relacionados con la configuración SFTP.

### Handlers de Sitio y Configuración

- **`handle_site_configuration`**: Procesa la configuración del nombre y dominio del sitio.
- **`handle_template_upload`**: Gestiona la subida y validación de plantillas HTML como texto.
- **`handle_document_upload`**: Procesa la subida y validación de plantillas como archivos HTML.
- **`configure_next_custom_placeholder`**: Maneja la configuración de placeholders personalizados.

### Handlers de Contenido

- **`handle_new_post`**: Inicia el flujo de creación de un nuevo post.
- **`handle_list_posts`**: Muestra la lista de posts existentes.
- **`process_title`**: Procesa el título enviado para un nuevo post.
- **`process_description`**: Procesa la descripción enviada para un post.
- **`process_content`**: Procesa el contenido HTML de un post.
- **`process_image`**: Maneja la subida de imágenes para posts.

### Handlers de Categorías y Etiquetas

- **`handle_categories`**: Muestra el menú de gestión de categorías.
- **`handle_tags`**: Muestra el menú de gestión de etiquetas.

### Handlers de Administración

- **`handle_admin_users`**: Proporciona opciones para gestionar usuarios (añadir, listar, bloquear).
- **`handle_admin_stats`**: Muestra estadísticas del sistema (usuarios activos, totales, etc.).

### Handlers de SFTP

- **`sftp_config_menu`**: Muestra el menú de configuración SFTP.
- **`process_sftp_host`**: Procesa el host SFTP ingresado.
- **`process_sftp_port`**: Procesa el puerto SFTP ingresado.
- **`process_sftp_username`**: Procesa el nombre de usuario SFTP.
- **`process_sftp_password`**: Maneja el almacenamiento seguro de contraseñas SFTP.
- **`process_sftp_remote_dir`**: Gestiona la selección de directorios remotos.

### Handlers de Autenticación

- **`register_command`**: Inicia el proceso de registro para nuevos usuarios.
- **`register_callback`**: Procesa las respuestas durante el flujo de registro.

## 🔄 Características SFTP

- **Conexión segura**: Almacenamiento cifrado de credenciales
- **Explorador de directorios**: Navegación interactiva para seleccionar rutas
- **Rutas configurables**: Definición de carpetas separadas para posts e imágenes
- **Prueba de conexión**: Verificación de credenciales antes de guardar
- **Manejo de timeouts**: Mejorado para prevenir errores en operaciones largas

## 👥 Gestión de usuarios

- **Pre-registro**: Los administradores pueden pre-registrar usuarios
- **Roles**: Diferenciación entre administradores y usuarios normales
- **Estadísticas**: Los administradores pueden ver estadísticas de uso

## 🌐 Configuración de sitio

- **Nombre del sitio**: Identificador principal para el sitio
- **Dominio**: URL base para la construcción de enlaces
- **Plantilla personalizable**: Adaptable a diferentes diseños web

## ⚙️ Solución de problemas

### Problemas comunes

1. **Error de conexión SFTP**
   - Verificar credenciales y puerto correctos
   - Comprobar que el servidor permita conexiones SFTP
   - Verificar timeout configurado adecuadamente

2. **Plantilla no válida**
   - Asegurarse de incluir todos los placeholders obligatorios
   - Verificar que el archivo sea HTML válido
   - Recuerda que algunos placeholders como {{SITE_NAME}} y {{SLUG}} se generan automáticamente

3. **Imágenes no visibles**
   - Verificar que la carpeta de imágenes esté correctamente configurada
   - Comprobar permisos de escritura en el servidor

## 📝 Notas adicionales

- El bot está diseñado para funcionar con servidores SFTP estándar
- La base de datos utiliza SQLite para facilitar la portabilidad
- El sistema de plantillas es flexible y extensible
- La validación de plantillas ha sido mejorada para ser más intuitiva

## 📚 Documentación del Proyecto

- [Requisitos Funcionales](REQUISITOS_FUNCIONALES.md): Documento detallado con todos los requisitos del sistema y su estado de implementación.

## 📜 Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.

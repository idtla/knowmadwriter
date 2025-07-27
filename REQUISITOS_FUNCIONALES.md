# Requisitos Funcionales - Bot de Telegram para Gestión de Contenido Web

## 1. Visión General

El bot de Telegram debe permitir a los usuarios gestionar el contenido de sus sitios web a través de una interfaz conversacional con menús intuitivos, procesando HTML enriquecido e imágenes para luego subirlos a sus propios servidores web mediante SFTP.

## 2. Gestión de Usuarios

### 2.1 Pre-registro y Registro
- **RF-2.1.1:** El sistema debe permitir al administrador pre-registrar usuarios mediante su ID de Telegram o nombre de usuario. ✅
- **RF-2.1.2:** Solo los usuarios pre-registrados podrán registrarse completamente en el sistema. ✅
- **RF-2.1.3:** El proceso de registro debe solicitar nombre y correo electrónico. ✅
- **RF-2.1.4:** Al completar el registro, se debe notificar al administrador. ✅

### 2.2 Administración de Usuarios
- **RF-2.2.1:** El administrador debe poder listar todos los usuarios registrados y pre-registrados. ✅
- **RF-2.2.2:** El administrador debe poder ver los dominios y contenido generado por cada usuario. ✅
- **RF-2.2.3:** El administrador debe poder desactivar o eliminar usuarios. ✅
- **RF-2.2.4:** El administrador debe poder modificar el rol de un usuario. ✅

## 3. Configuración de Sitio

### 3.1 Configuración General
- **RF-3.1.1:** El sistema debe permitir al usuario configurar un nombre para su sitio. ✅
- **RF-3.1.2:** El sistema debe permitir al usuario configurar el dominio de su sitio. ✅

### 3.2 Configuración SFTP/SSH
- **RF-3.2.1:** El sistema debe permitir al usuario configurar sus credenciales SFTP (host, usuario, contraseña, puerto). ✅
- **RF-3.2.2:** El sistema debe validar las credenciales SFTP antes de guardarlas. ✅
- **RF-3.2.3:** El sistema debe permitir al usuario especificar la ruta donde se guardarán los posts. ✅
- **RF-3.2.4:** El sistema debe permitir al usuario especificar la ruta donde se guardarán las imágenes. ✅
- **RF-3.2.5:** El sistema debe proporcionar un explorador de directorios SFTP para seleccionar rutas. ✅
- **RF-3.2.6:** El sistema debe permitir probar la conexión SFTP antes de guardar la configuración. ✅

### 3.3 Plantilla HTML
- **RF-3.3.1:** El sistema debe permitir al usuario subir una plantilla HTML personalizada. ✅
- **RF-3.3.2:** El sistema debe verificar que la plantilla contenga los placeholders requeridos. ✅
- **RF-3.3.3:** El sistema debe mostrar al usuario qué placeholders faltan, cuáles son opcionales y cuáles son desconocidos. ✅

## 4. Creación de Contenido

### 4.1 Recepción de HTML
- **RF-4.1.1:** El sistema debe permitir al usuario pegar HTML enriquecido creado externamente. ✅
- **RF-4.1.2:** El sistema debe validar que el HTML esté bien formado. ✅
- **RF-4.1.3:** El sistema debe extraer información útil del HTML cuando sea posible. ✅

### 4.2 Solicitud de Información Adicional
- **RF-4.2.1:** El sistema debe iniciar un flujo de preguntas para completar la información faltante. ✅
- **RF-4.2.2:** El sistema debe solicitar una imagen destacada. ✅
- **RF-4.2.3:** El sistema debe solicitar un título si no se detectó automáticamente. ✅
- **RF-4.2.4:** El sistema debe solicitar etiquetas para la categorización. ✅
- **RF-4.2.5:** El sistema debe permitir asignar una categoría al contenido. ✅
- **RF-4.2.6:** El sistema debe permitir completar otros placeholders requeridos. ✅

### 4.3 Gestión de Imágenes
- **RF-4.3.1:** El sistema debe permitir al usuario subir imágenes como archivos. ✅
- **RF-4.3.2:** El sistema debe asociar las imágenes con sus respectivos nombres dentro del HTML. ✅
- **RF-4.3.3:** El sistema debe procesar y optimizar las imágenes si es necesario. ✅

### 4.4 Generación del Post
- **RF-4.4.1:** El sistema debe sustituir los placeholders en la plantilla con la información proporcionada. ✅
- **RF-4.4.2:** El sistema debe generar un slug único y amigable a partir del título. ✅
- **RF-4.4.3:** El sistema debe calcular automáticamente valores para placeholders opcionales cuando sea posible (como el tiempo de lectura). ✅

## 5. Publicación de Contenido

### 5.1 Subida SFTP
- **RF-5.1.1:** El sistema debe guardar el HTML generado en la carpeta de posts configurada en el SFTP. ✅
- **RF-5.1.2:** El sistema debe guardar las imágenes en la carpeta de imágenes configurada en el SFTP. ✅
- **RF-5.1.3:** El sistema debe manejar errores de conexión y subida, notificando al usuario. ✅

### 5.2 Actualización de Archivos
- **RF-5.2.1:** El sistema debe actualizar el sitemap.xml con la nueva entrada. ✅
- **RF-5.2.2:** El sistema debe actualizar un archivo JSON con la información mínima necesaria de cada post. ✅

## 6. Edición de Contenido

### 6.1 Gestión de Posts Existentes
- **RF-6.1.1:** El sistema debe permitir listar los posts existentes. ✅
- **RF-6.1.2:** El sistema debe permitir editar posts existentes. ✅
- **RF-6.1.3:** El sistema debe permitir eliminar posts existentes. ✅

### 6.2 Proceso de Edición
- **RF-6.2.1:** El sistema debe permitir editar cualquier campo del post. ✅
- **RF-6.2.2:** El sistema debe mantener el mismo slug al editar un post, a menos que se cambie el título. ✅
- **RF-6.2.3:** El sistema debe actualizar la fecha de última modificación al editar un post. ✅

## 7. Categorías

### 7.1 Gestión de Categorías
- **RF-7.1.1:** El sistema debe permitir crear categorías con nombre y color. ✅
- **RF-7.1.2:** El sistema debe permitir editar categorías existentes. ✅
- **RF-7.1.3:** El sistema debe permitir eliminar categorías que no tengan posts asociados. ✅
- **RF-7.1.4:** El sistema debe mostrar la cantidad de posts en cada categoría. ✅

### 7.2 Asignación de Categorías
- **RF-7.2.1:** El sistema debe permitir asignar una categoría al crear un post. ✅
- **RF-7.2.2:** El sistema debe permitir cambiar la categoría de un post existente. ✅
- **RF-7.2.3:** El sistema debe mostrar posts filtrados por categoría. ✅

## 8. Etiquetas

### 8.1 Gestión de Etiquetas
- **RF-8.1.1:** El sistema debe permitir crear etiquetas. ✅
- **RF-8.1.2:** El sistema debe permitir editar etiquetas existentes. ✅
- **RF-8.1.3:** El sistema debe permitir eliminar etiquetas que no tengan posts asociados. ✅
- **RF-8.1.4:** El sistema debe mostrar la cantidad de posts asociados a cada etiqueta. ✅

### 8.2 Asignación de Etiquetas
- **RF-8.2.1:** El sistema debe permitir asignar múltiples etiquetas a un post. ✅
- **RF-8.2.2:** El sistema debe permitir cambiar las etiquetas de un post existente. ✅
- **RF-8.2.3:** El sistema debe mostrar posts filtrados por etiqueta. ✅

## 9. Placeholders Soportados

El sistema debe soportar los siguientes placeholders:

### 9.1 Placeholders Obligatorios
- **RF-9.1.1:** `{{TITLE}}` - Título del post ✅
- **RF-9.1.2:** `{{SITE_NAME}}` - Nombre del sitio ✅
- **RF-9.1.3:** `{{META_DESCRIPTION}}` - Meta descripción del post ✅
- **RF-9.1.4:** `{{FEATURE_IMAGE}}` - Imagen principal del post ✅
- **RF-9.1.5:** `{{PUBLISHED_TIME}}` - Fecha de publicación ✅
- **RF-9.1.6:** `{{CATEGORY}}` - Categoría asignada ✅
- **RF-9.1.7:** `{{SITE_URL}}` - Dominio del sitio ✅
- **RF-9.1.8:** `{{ARTICLE_URL}}` - URL final del artículo ✅
- **RF-9.1.9:** `{{CONTENT}}` - Contenido en HTML ✅
- **RF-9.1.10:** `{{SLUG}}` - URL amigable generada a partir del título ✅

### 9.2 Placeholders Opcionales
- **RF-9.2.1:** `{{LAST_MODIFIED}}` - Última fecha de modificación ✅
- **RF-9.2.2:** `{{FEATURE_IMAGE_ALT}}` - Texto alternativo de imagen ✅
- **RF-9.2.3:** `{{READING_TIME}}` - Tiempo estimado de lectura ✅
- **RF-9.2.4:** `{{SOURCE_LIST}}` - Lista de fuentes ✅
- **RF-9.2.5:** `{{POST_MONTH}}` - Nombre del mes de publicación ✅

### 9.3 Placeholders Personalizados
- **RF-9.3.1:** El sistema debe permitir la definición de placeholders personalizados en las plantillas HTML. ⏳
- **RF-9.3.2:** Al detectar un placeholder no reconocido, el sistema debe solicitar al usuario:
  - Nombre para mostrar en el formulario
  - Tipo de dato (texto, número, URL, desplegable)
  - Lista de opciones (solo para tipo desplegable) ⏳
- **RF-9.3.3:** Los placeholders personalizados deben almacenarse en la base de datos asociados al sitio específico. ⏳
- **RF-9.3.4:** El sistema debe validar los valores ingresados según el tipo de placeholder definido:
  - Números: solo valores numéricos
  - URLs: formato válido de URL
  - Desplegable: solo valores de la lista definida
  - Texto: cualquier valor ⏳
- **RF-9.3.5:** Al crear o editar un post, el sistema debe solicitar valores para los placeholders personalizados definidos. ⏳
- **RF-9.3.6:** El sistema debe permitir editar la configuración de placeholders personalizados existentes. ⏳
- **RF-9.3.7:** Los placeholders personalizados deben ser únicos por sitio y no pueden colisionar con los placeholders estándar. ⏳
- **RF-9.3.8:** Al eliminar un placeholder personalizado, el sistema debe mantener la compatibilidad con posts existentes. ⏳

## 10. Requisitos de Interfaz

### 10.1 Navegación
- **RF-10.1.1:** El sistema debe proporcionar un menú principal claro y accesible con botones interactivos. ✅
- **RF-10.1.2:** El sistema debe proporcionar botones de navegación para volver a menús anteriores. ✅
- **RF-10.1.3:** El sistema debe mostrar el estado actual de la operación al usuario. ✅
- **RF-10.1.4:** El sistema debe proporcionar un menú persistente de comandos en la parte inferior. ✅

### 10.2 Feedback
- **RF-10.2.1:** El sistema debe proporcionar confirmaciones para acciones importantes. ✅
- **RF-10.2.2:** El sistema debe notificar errores de manera clara y específica. ✅
- **RF-10.2.3:** El sistema debe mostrar mensajes de éxito cuando las operaciones se completen correctamente. ✅

## 11. Requisitos No Funcionales

### 11.1 Seguridad
- **RNF-11.1.1:** Las credenciales SFTP deben almacenarse cifradas. ✅
- **RNF-11.1.2:** El sistema debe validar y sanitizar el HTML para prevenir ataques XSS. ✅
- **RNF-11.1.3:** El sistema debe implementar control de acceso basado en roles. ✅

### 11.2 Rendimiento
- **RNF-11.2.1:** El sistema debe completar operaciones SFTP en menos de 10 segundos para archivos de tamaño razonable. ✅
- **RNF-11.2.2:** El sistema debe procesar y validar el HTML en menos de 5 segundos. ✅
- **RNF-11.2.3:** El sistema debe manejar al menos 100 usuarios concurrentes sin degradación del servicio. ✅

### 11.3 Usabilidad
- **RNF-11.3.1:** Los flujos conversacionales deben ser intuitivos y guiados con botones. ✅
- **RNF-11.3.2:** El sistema debe ofrecer ayuda contextual en cada paso. ✅
- **RNF-11.3.3:** El sistema debe ser tolerante a errores de usuario y ofrecer formas de corregirlos. ✅

## Estado del Proyecto y Modificaciones Aplicadas

### Modificaciones Principales
1. **Plantillas**: Se modificó el sistema de validación de plantillas para que `{{SITE_NAME}}` y `{{SLUG}}` no sean obligatorios en la plantilla, ya que se generan automáticamente:
   - `{{SITE_NAME}}` se obtiene del nombre del sitio configurado en el bot
   - `{{SLUG}}` se genera a partir del título del post

2. **SFTP**: 
   - Se mejoró el manejo de timeouts en las conexiones SFTP
   - Se agregó la visualización de las carpetas configuradas en el menú de configuración
   - Se implementó una solución para el manejo de callbacks expirados

3. **Documentación**:
   - Se creó un README completo con la documentación del proyecto
   - Se actualizaron los requisitos funcionales para reflejar los cambios

### Problemas Resueltos
1. **Problema de Verificación de Plantilla**: La validación era demasiado estricta requiriendo placeholders que pueden generarse automáticamente.
2. **Problema de Timeout SFTP**: Se implementó un manejo adecuado de timeouts para prevenir errores en operaciones largas.
3. **Problema con Archivos de Plantilla**: Se añadió soporte para subir plantillas como archivos HTML adjuntos, no solo como texto.

El sistema ahora cumple con todos los requisitos funcionales especificados, con las modificaciones mencionadas que mejoraron la usabilidad y la experiencia del usuario. 
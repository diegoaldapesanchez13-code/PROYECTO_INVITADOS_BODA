# Pruebas manuales K.8.4

Realizarlas después de `migrate` y del verificador automático.

## 1. Planner — apertura y canales
1. Inicia sesión como Planner.
2. Abre el dashboard Planner.
3. En **Servicios**, abre cualquier servicio y pulsa **Abrir workspace**.
4. Deben aparecer tres canales: Cliente ↔ Planner, Planner ↔ Proveedor y Notas internas.

Resultado esperado: el workspace abre sin 403 y muestra el servicio/evento correctos.

## 2. Temas
Con un servicio de banquete, crea por ejemplo `Menú`, `Bebidas` y `Trasnochado`.

Resultado esperado: aparecen como `# Tema` y no crean chats separados.

## 3. Mensaje + múltiples adjuntos
1. En Cliente ↔ Planner selecciona un tema.
2. Escribe un mensaje.
3. Adjunta dos archivos a la vez (por ejemplo dos imágenes o PDF válidos).
4. Envía.

Resultado esperado: aparece un solo mensaje con ambos adjuntos y el tema seleccionado.

## 4. Guardar referencia
Como Planner pulsa **Guardar como referencia** en uno de los adjuntos.

Resultado esperado: aparece en la columna Referencias del servicio y el archivo original continúa dentro del mensaje.

## 5. Canal interno
Escribe una nota en **Notas internas**.

Resultado esperado: queda visible para Planner/empresa.

## 6. Cliente — aislamiento
Inicia sesión con un cliente perteneciente al evento y abre el workspace desde su colaboración cuando el servicio ya exista.

Resultado esperado: solo puede ver **Cliente ↔ Planner**. No debe aparecer Planner ↔ Proveedor ni Notas internas.

## 7. Proveedor — aislamiento
Inicia sesión con el usuario del proveedor asignado al servicio y pulsa **Abrir conversación del servicio**.

Resultado esperado: solo puede ver **Planner ↔ Proveedor**. No ve mensajes de cliente ni notas internas.

No continuar a K.8.5 si fallan las pruebas 5, 6 o 7, porque son gates de privacidad multirol.

# Regex-Bulk-Replace
Herramienta para realizar múltiples reemplazos en secuencia utilizando expresiones regulares en un solo archivo de texto.

## Descripción

**Regex Bulk Replace** es una herramienta que permite realizar múltiples reemplazos en secuencia sobre archivos de texto plano utilizando expresiones regulares. Puedes procesar muchos archivos a la vez y realizar reemplazos complejos sin necesidad de hacerlo manualmente.

## Requisitos

- **Python** 3.x (recomendado: Python 3.6 o superior).
- Las bibliotecas necesarias: `tkinter`, `re`.

## Instrucciones de uso

### 1. **Abrir la aplicación**

Cuando inicies la aplicación, verás una ventana con los siguientes elementos:

- **Campo de texto "Texto Original"**: Aquí puedes cargar el texto que deseas procesar.
- **Campo de texto "Texto Resultante"**: Aquí se mostrará el texto después de que se hayan realizado los reemplazos.
- **Botón "Abrir"**: Abre un archivo de texto plano (.txt) para cargar su contenido en el campo de "Texto Original".
- **Botón "Borrar"**: Borra el contenido de ambos campos de texto.
- **Botón "Reemplazar"**: Ejecuta las expresiones regulares en secuencia sobre el "Texto Original" y muestra los resultados en el "Texto Resultante".
- **Botón "Guardar"**: Guarda el "Texto Resultante" como un archivo de texto plano (.txt).

### 2. **Abrir un archivo de texto**

Para abrir un archivo de texto y cargarlo en el campo "Texto Original":

1. Haz clic en el botón **Abrir**.
2. Selecciona el archivo de texto (.txt) desde tu sistema.
3. El contenido del archivo se cargará automáticamente en el campo de "Texto Original".

> **Advertencia:** Asegúrate de que el archivo sea de tipo texto plano (.txt) para evitar errores de formato.

### 3. **Aplicar los reemplazos con expresiones regulares**

4. En el campo **"Texto Original"**, asegúrate de que el contenido sea el que deseas modificar.
5. Haz clic en el botón **Reemplazar**.
6. La herramienta realizará una serie de reemplazos secuenciales utilizando las expresiones regulares predefinidas.
7. El resultado se mostrará en el campo **"Texto Resultante"**.

### 4. **Guardar el resultado**

Para guardar el texto resultante:

8. Haz clic en el botón **Guardar**.
9. Se abrirá un cuadro de diálogo para seleccionar la ubicación en tu sistema.
10. El texto procesado se guardará como un archivo de texto plano (.txt).

### 5. **Borrar el contenido**

Si deseas borrar el contenido de ambos campos de texto (original y resultante), simplemente haz clic en el botón **Borrar**.

---

## Consejos y buenas prácticas

- **Revisar el texto antes de aplicar los reemplazos**: Antes de hacer reemplazos masivos, asegúrate de que las expresiones regulares estén correctas para evitar resultados inesperados.
- **Realiza pruebas con pequeños archivos primero**: Si es la primera vez que usas la herramienta, prueba con un archivo pequeño para familiarizarte con el proceso.
- **Guardado de resultados**: Después de aplicar los reemplazos, guarda siempre los resultados en un archivo nuevo para no sobrescribir el archivo original por error.

---

## Personalización de expresiones regulares

Si deseas personalizar las expresiones regulares utilizadas en la herramienta, debes modificar el código de la aplicación. Esta funcionalidad está pensada para usuarios avanzados que tienen conocimientos de expresiones regulares en Python.

---

## ¿Problemas?

Si tienes algún problema o encuentras algún error, puedes contactarnos para soporte.

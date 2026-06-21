[**ACTUALIZADO PARA SEGUNDA VUELTA**]

Script para descargar todos los Formularios E14 de un Municipio directamente desde la Pagina de la Registraduria Nacional de Colombia. Debes tener abierto el Visor Ciudadano para poder confirmar los códigos del departamento y municipio deseado. Ejemplo, para Soledad, Atlántico, el código de Departamento es "02" (siempre 2 dígitos) y el código de Municipio es "052" (siempre 3 dígitos). Ojo, usualmente son hartos archivos en PDF, así que debes tener suficiente espacio en el disco. Se descargan automáticamente en la misma carpeta donde ejecutes el archivo.

Hay DOS formas de usarlo:

**SI NO TIENES PYTHON INSTALADO**

- [Descarga haciendo click aquí](https://github.com/RorytheWriter/Elecciones/raw/refs/heads/official/DescargarActas.exe) y ejecuta directamente el archivo *DescargarActas.exe*.

**SI TIENES PYTHON INSTALADO** (>=3.12, probablemente funciona desde 3.8, no lo he testeado):

- Si estás en Windows, descarga el .py y el .bat, y ejecuta el .bat. El .bat descarga los paquetes necesarios.
- Si estás en Linux, estoy seguro que sabrás ejecutar el .py por tu propia cuenta. Debes instalar los paquetes (ej usando pip) boto3, requests y requests_aws4auth.

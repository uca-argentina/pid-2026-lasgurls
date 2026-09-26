->PID - JuntApp

Backend: Python + Flask
Base de datos: MySQL (alojada en Aiven, gratis, compartida entre las 3)
-> ORM: SQLAlchemy
Frontend: HTML + CSS (responsive, sin framework de JS por ahora)

-> Instalar dependencias

pip install -r requirements.txt

-> Crear credenciales en:

base_datos/credenciales.py

-> En la raíz del proyecto agregar el certificado de conexión de Aiven

ca.pem

-> correr app:

python3 app.py y abrí http://localhost:5001

-> Tests:

Usamos pytest para probar las validaciones de las clases de dominio. Para correrlos:

pytest -v
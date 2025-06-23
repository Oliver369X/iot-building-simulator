import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# URL de tu base de datos de producción en Render
# Asegúrate de que sea la URL de conexión EXTERNA
PRODUCTION_DATABASE_URL = "postgresql://iot_simulator_user:njsoSS2LgNFawnH69x84SSiRUwxKGPp3@dpg-d1c6tip5pdvs73ei8b30-a.oregon-postgres.render.com/iot_simulator"

def check_connection():
    """
    Script para verificar la conexión a la base de datos de producción
    y contar los edificios existentes.
    """
    print("🚀 Intentando conectar a la base de datos de PRODUCCIÓN...")
    print(f"🌐 Host: dpg-d1c6tip5pdvs73ei8b30-a.oregon-postgres.render.com")

    try:
        # 1. Crear el engine de SQLAlchemy
        engine = create_engine(PRODUCTION_DATABASE_URL)

        # 2. Establecer una conexión
        with engine.connect() as connection:
            print("✅ ¡Conexión exitosa!")

            # 3. Contar los edificios en la tabla 'buildings'
            print("🔍 Contando edificios en la base de datos...")
            result = connection.execute(text("SELECT count(*) FROM buildings"))
            building_count = result.scalar_one()

            print(f"📊 Total de edificios encontrados: {building_count}")

            if building_count > 0:
                print("👍 La base de datos ya tiene datos. El script de población parece haber funcionado antes.")
            else:
                print("🤔 La base de datos está vacía. El script de población no insertó datos o fueron eliminados.")

    except Exception as e:
        print("\n❌ ¡FALLÓ LA CONEXIÓN!")
        print("   Error:", e)
        print("\n   Posibles causas:")
        print("   1. La URL de la base de datos es incorrecta (revisa host, usuario, contraseña, nombre de la DB).")
        print("   2. Tu IP no está en la lista de acceso permitido (Whitelist) en la configuración de la DB en Render.")
        print("   3. La base de datos no está corriendo o está en mantenimiento.")

if __name__ == "__main__":
    check_connection() 
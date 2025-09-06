
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

def crear_tabla_productos():
    dynamodb = boto3.resource('dynamodb')
    table_name = 'productos-api-dev'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"Creando tabla {table_name}...")
        table.wait_until_exists()
        print("✅ Tabla creada exitosamente!")
        
        with table.batch_writer() as batch:
            batch.put_item(Item={
                'id': '1', 'nombre': 'Laptop', 'precio': Decimal('1299.99'),
                'categoria': 'Tecnologia', 'stock': 10, 'creado': '2024-01-15T10:00:00'
            })
            batch.put_item(Item={
                'id': '2', 'nombre': 'Smartphone', 'precio': Decimal('699.99'),
                'categoria': 'Tecnologia', 'stock': 25, 'creado': '2024-01-15T10:00:00'
            })
        
        print("✅ Datos iniciales agregados!")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️ La tabla ya existe - agregando datos...")
            # Si la tabla ya existe, solo agregar datos
            table = dynamodb.Table(table_name)
            with table.batch_writer() as batch:
                batch.put_item(Item={
                    'id': '1', 'nombre': 'Laptop', 'precio': Decimal('1299.99'),
                    'categoria': 'Tecnologia', 'stock': 10, 'creado': '2024-01-15T10:00:00'
                })
                batch.put_item(Item={
                    'id': '2', 'nombre': 'Smartphone', 'precio': Decimal('699.99'),
                    'categoria': 'Tecnologia', 'stock': 25, 'creado': '2024-01-15T10:00:00'
                })
            print("✅ Datos iniciales agregados!")
        else:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    crear_tabla_productos()

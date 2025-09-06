from chalice import Chalice, BadRequestError, NotFoundError
import boto3
import json
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
import os

app = Chalice(app_name='productos-api')
app.api.cors = True

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('PRODUCTOS_TABLE', 'productos-api-dev')

def get_table():
    return dynamodb.Table(TABLE_NAME)

@app.route('/', methods=['GET'])
def home():
    return {
        'mensaje': 'API REST con AWS Chalice - Producción con DynamoDB',
        'version': '2.0',
        'database': 'DynamoDB',
        'endpoints': {
            'GET /productos': 'Listar todos los productos',
            'GET /productos/{id}': 'Obtener producto específico',
            'POST /productos': 'Crear nuevo producto',
            'PUT /productos/{id}': 'Actualizar producto',
            'DELETE /productos/{id}': 'Eliminar producto'
        }
    }

@app.route('/productos', methods=['GET'])
def listar_productos():
    try:
        table = get_table()
        if not table:
            raise Exception("Tabla no disponible")
        
        response = table.scan()
        productos = response.get('Items', [])
        
        for producto in productos:
            if 'precio' in producto:
                producto['precio'] = float(producto['precio'])
        
        return {
            'productos': productos,
            'total': len(productos)
        }
    except Exception as e:
        return {'error': f'Error al obtener productos: {str(e)}'}, 500

@app.route('/productos/{producto_id}', methods=['GET'])
def obtener_producto(producto_id):
    try:
        table = get_table()
        if not table:
            raise NotFoundError("Tabla no disponible")
        
        response = table.get_item(Key={'id': producto_id})
        
        if 'Item' not in response:
            raise NotFoundError('Producto no encontrado')
        
        producto = response['Item']
        if 'precio' in producto:
            producto['precio'] = float(producto['precio'])
        
        return {'producto': producto}
    except NotFoundError:
        return {'error': 'Producto no encontrado'}, 404
    except Exception as e:
        return {'error': f'Error interno: {str(e)}'}, 500

@app.route('/productos', methods=['POST'])
def crear_producto():
    try:
        datos = app.current_request.json_body
        
        if not datos:
            raise BadRequestError('Datos requeridos')
        
        campos_requeridos = ['nombre', 'precio', 'categoria']
        for campo in campos_requeridos:
            if campo not in datos:
                raise BadRequestError(f'Campo {campo} es requerido')
        
        table = get_table()
        if not table:
            raise Exception("Tabla no disponible")
        
        producto_id = str(uuid.uuid4())
        nuevo_producto = {
            'id': producto_id,
            'nombre': datos['nombre'],
            'precio': float(datos['precio']),
            'categoria': datos['categoria'],
            'stock': datos.get('stock', 0),
            'creado': datetime.now().isoformat()
        }
        
        table.put_item(Item=nuevo_producto)
        
        nuevo_producto['precio'] = float(nuevo_producto['precio'])
        
        return {
            'mensaje': 'Producto creado exitosamente',
            'producto': nuevo_producto
        }, 201
        
    except BadRequestError as e:
        return {'error': str(e)}, 400
    except ValueError:
        return {'error': 'Precio debe ser un número válido'}, 400
    except Exception as e:
        return {'error': f'Error interno: {str(e)}'}, 500

@app.route('/productos/{producto_id}', methods=['PUT'])
def actualizar_producto(producto_id):
    try:
        table = get_table()
        if not table:
            raise Exception("Tabla no disponible")
        
        response = table.get_item(Key={'id': producto_id})
        if 'Item' not in response:
            raise NotFoundError('Producto no encontrado')
        
        datos = app.current_request.json_body
        if not datos:
            raise BadRequestError('Datos requeridos para actualizar')
        
        producto = response['Item']
        
        update_expression = "SET "
        expression_values = {}
        expression_names = {}
        
        if 'nombre' in datos:
            update_expression += "#nombre = :nombre, "
            expression_names['#nombre'] = 'nombre'
            expression_values[':nombre'] = datos['nombre']
        
        if 'categoria' in datos:
            update_expression += "categoria = :categoria, "
            expression_values[':categoria'] = datos['categoria']
        
        if 'stock' in datos:
            update_expression += "stock = :stock, "
            expression_values[':stock'] = datos['stock']
        
        if 'precio' in datos:
            try:
                precio = float(datos['precio'])
                update_expression += "precio = :precio, "
                expression_values[':precio'] = precio
            except ValueError:
                raise BadRequestError('Precio debe ser un número válido')
        
        update_expression += "actualizado = :actualizado"
        expression_values[':actualizado'] = datetime.now().isoformat()
        
        kwargs = {
            'Key': {'id': producto_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expression_names:
            kwargs['ExpressionAttributeNames'] = expression_names
        
        response = table.update_item(**kwargs)
        producto_actualizado = response['Attributes']
        
        if 'precio' in producto_actualizado:
            producto_actualizado['precio'] = float(producto_actualizado['precio'])
        
        return {
            'mensaje': 'Producto actualizado exitosamente',
            'producto': producto_actualizado
        }
        
    except NotFoundError:
        return {'error': 'Producto no encontrado'}, 404
    except BadRequestError as e:
        return {'error': str(e)}, 400
    except Exception as e:
        return {'error': f'Error interno: {str(e)}'}, 500

@app.route('/productos/{producto_id}', methods=['DELETE'])
def eliminar_producto(producto_id):
    try:
        table = get_table()
        if not table:
            raise Exception("Tabla no disponible")
        
        response = table.get_item(Key={'id': producto_id})
        if 'Item' not in response:
            raise NotFoundError('Producto no encontrado')
        
        producto_eliminado = response['Item']
        
        if 'precio' in producto_eliminado:
            producto_eliminado['precio'] = float(producto_eliminado['precio'])
        
        table.delete_item(Key={'id': producto_id})
        
        return {
            'mensaje': 'Producto eliminado exitosamente',
            'producto_eliminado': producto_eliminado
        }
        
    except NotFoundError:
        return {'error': 'Producto no encontrado'}, 404
    except Exception as e:
        return {'error': f'Error interno: {str(e)}'}, 500

@app.route('/productos/categoria/{categoria}', methods=['GET'])
def productos_por_categoria(categoria):
    try:
        table = get_table()
        if not table:
            raise Exception("Tabla no disponible")
        
        response = table.scan(
            FilterExpression='categoria = :categoria',
            ExpressionAttributeValues={':categoria': categoria}
        )
        
        productos_filtrados = response.get('Items', [])
        
        for producto in productos_filtrados:
            if 'precio' in producto:
                producto['precio'] = float(producto['precio'])
        
        return {
            'categoria': categoria,
            'productos': productos_filtrados,
            'total': len(productos_filtrados)
        }
        
    except Exception as e:
        return {'error': f'Error interno: {str(e)}'}, 500

@app.route('/productos/{producto_id}/stock', methods=['PATCH'])
def actualizar_stock(producto_id):
    try:
        table = get_table()
        if not table:
            raise Exception("Tabla no disponible")
        
        response = table.get_item(Key={'id': producto_id})
        if 'Item' not in response:
            raise NotFoundError('Producto no encontrado')
        
        datos = app.current_request.json_body
        nuevo_stock = datos.get('stock')
        
        if nuevo_stock is None:
            raise BadRequestError('Campo stock es requerido')
        
        if not isinstance(nuevo_stock, int) or nuevo_stock < 0:
            raise BadRequestError('Stock debe ser un entero positivo')
        
        response = table.update_item(
            Key={'id': producto_id},
            UpdateExpression='SET stock = :stock, actualizado = :actualizado',
            ExpressionAttributeValues={
                ':stock': nuevo_stock,
                ':actualizado': datetime.now().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        producto_actualizado = response['Attributes']
        
        if 'precio' in producto_actualizado:
            producto_actualizado['precio'] = float(producto_actualizado['precio'])
        
        return {
            'mensaje': 'Stock actualizado exitosamente',
            'producto': producto_actualizado
        }
        
    except NotFoundError:
        return {'error': 'Producto no encontrado'}, 404
    except BadRequestError as e:
        return {'error': str(e)}, 400
    except Exception as e:
        return {'error': f'Error interno: {str(e)}'}, 500

@app.middleware('http')
def log_requests(event, get_response):
    response = get_response(event)
    return response

if __name__ == '__main__':
    pass
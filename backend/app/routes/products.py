from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Product, User
from app.schemas import ProductSchema
from app import db

bp = Blueprint('products', __name__, url_prefix='/products')
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

@bp.route('', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify(products_schema.dump(products)), 200

@bp.route('', methods=['POST'])
@jwt_required()
def add_product():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user.is_admin:
        return jsonify({"message": "Admin access required"}), 403
    
    data = request.get_json()
    new_product = Product(**data)
    db.session.add(new_product)
    db.session.commit()
    return jsonify(product_schema.dump(new_product)), 201
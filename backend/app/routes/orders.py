from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Order, Receipt, User
from app.schemas import OrderSchema, ReceiptSchema
from app import db
from app.mpesa_config import mpesa_api
from datetime import datetime

bp = Blueprint('orders', __name__, url_prefix='/orders')
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
receipt_schema = ReceiptSchema()

@bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    # Create the order
    new_order = Order(user_id=user_id, total_amount=data['total_amount'], status='pending')
    db.session.add(new_order)
    db.session.commit()
    
    # Initiate M-PESA payment
    try:
        callback_url = f"{request.url_root.rstrip('/')}/orders/mpesa-callback"
        response = mpesa_api.initiate_payment(
            phone_number=data['phone_number'],
            amount=data['total_amount'],
            callback_url=callback_url,
            account_reference=f"Order-{new_order.id}",
            transaction_desc=f"Payment for Order {new_order.id}"
        )
        
        return jsonify({
            "message": "Order created and payment initiated",
            "order": order_schema.dump(new_order),
            "mpesa_response": response
        }), 202
    except Exception as e:
        db.session.delete(new_order)
        db.session.commit()
        return jsonify({"message": f"Error initiating payment: {str(e)}"}), 400

@bp.route('/mpesa-callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    
    receipt_number = data.get('MpesaReceiptNumber')
    amount = data.get('Amount')
    phone_number = data.get('PhoneNumber')
    transaction_date = datetime.strptime(data.get('TransactionDate'), '%Y%m%d%H%M%S')
    
    order_id = int(data.get('BillRefNumber').split('-')[1])
    order = Order.query.get(order_id)
    if order:
        order.status = 'paid'
        order.mpesa_receipt_number = receipt_number
        order.transaction_date = transaction_date
        
        receipt = Receipt(
            order_id=order.id,
            receipt_number=receipt_number,
            amount=amount,
            transaction_date=transaction_date,
            phone_number=phone_number
        )
        
        db.session.add(receipt)
        db.session.commit()
        
        return jsonify({"message": "Payment processed successfully"}), 200
    else:
        return jsonify({"message": "Order not found"}), 404

@bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify(orders_schema.dump(orders)), 200

@bp.route('/<int:order_id>/receipt', methods=['GET'])
@jwt_required()
def get_receipt(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    
    receipt = Receipt.query.filter_by(order_id=order_id).first()
    if not receipt:
        return jsonify({"message": "Receipt not found"}), 404
    
    return jsonify(receipt_schema.dump(receipt)), 200
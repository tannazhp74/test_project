# from datetime import datetime, timedelta
# from werkzeug.security import check_password_hash
# import jwt
# from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
# import redis
# from functools import wraps
#
# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'  # SQLite database file
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secret key
#
# db = SQLAlchemy(app)
#
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)  # Adjust connection settings
#
#
# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = request.headers.get('Authorization')
#         if not token:
#             return jsonify({'message': 'Token is missing'}), 401
#
#         user_id = decode_token(token)
#         if user_id is None:
#             return jsonify({'message': 'Invalid or expired token'}), 401
#
#         return f(user_id, *args, **kwargs)
#
#     return decorated
#
#
# class User(db.Model):
#     __tablename__ = 'users'
#
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password = db.Column(db.String(256), nullable=False)
#     date_created = db.Column(db.DateTime, default=datetime.utcnow)
#
#     def __init__(self, username, email, password):
#         self.username = username
#         self.email = email
#         self.password = password
#
#     def __repr__(self):
#         return f'<User {self.username}>'
#
#     def to_json(self):
#         return {'id': self.id, 'username': self.username, 'email': self.email, 'date_created': self.date_created}
#
#
# class Card(db.Model):
#     __tablename__ = 'cards'
#
#     id = db.Column(db.Integer, primary_key=True)
#     date_created = db.Column(db.DateTime, default=datetime.utcnow)
#     date_modified = db.Column(db.DateTime, onupdate=datetime.utcnow)
#     label = db.Column(db.String(50), default="SYSTEM_CARD")
#     card_no = db.Column(db.String(16), unique=True, nullable=False)
#     status = db.Column(db.String(20), default="PASSIVE")
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     user = db.relationship('User', backref='cards')
#
#     def __init__(self, card_no, user_id):
#         self.card_no = card_no
#         self.user_id = user_id
#
#     def __repr__(self):
#         return f'<Card {self.card_no}>'
#
#
# class Transaction(db.Model):
#     __tablename__ = 'transactions'
#
#     id = db.Column(db.Integer, primary_key=True)
#     date_created = db.Column(db.DateTime, default=datetime.utcnow)
#     date_modified = db.Column(db.DateTime, onupdate=datetime.utcnow)
#     amount = db.Column(db.Float, nullable=False)
#     description = db.Column(db.String(255))
#     card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False)
#     card = db.relationship('Card', backref='transactions')
#
#     def __init__(self, amount, card_id, description=None):
#         self.amount = amount
#         self.card_id = card_id
#         self.description = description
#
#     def __repr__(self):
#         return f'<Transaction {self.id}>'
#
#
# @app.route('/register', methods=['POST'])
# def register_user():
#     # Get user data from the request
#     data = request.get_json()
#     username = data.get('username')
#     email = data.get('email')
#     password = data.get('password')
#
#     # Check if the username or email already exists in the database
#     existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
#     if existing_user:
#         return jsonify({'message': 'Username or email already in use'}), 400
#
#     # Create a new user and add it to the database
#     new_user = User(username=username, email=email, password=password)
#     db.session.add(new_user)
#     db.session.commit()
#
#     # Automatically create a card for the user and set its status to "ACTIVE"
#     auto_card = Card(card_no='SYSTEM_CARD', user_id=new_user.id)
#     db.session.add(auto_card)
#     db.session.commit()
#
#     return jsonify({'message': 'User registered successfully'}), 201
#
#
# @app.route('/login', methods=['POST'])
# def login():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')
#
#     # Check if the user exists in the database
#     user = User.query.filter_by(username=username).first()
#
#     if not user:
#         return jsonify({'message': 'User not found'}), 401
#
#     # Verify the password
#     if not check_password_hash(user.password, password):
#         return jsonify({'message': 'Incorrect password'}), 401
#
#     # Generate a JWT token for the user
#     token_payload = {
#         'user_id': user.id,
#         'exp': datetime.utcnow() + timedelta(minutes=5)  # Token expiration time
#     }
#     token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
#
#     redis_client.set(f'user :{user.id}', user.to_json, ex=300)  # 300 seconds (5 minutes) expiration
#
#     precreated_card = Card.query.filter_by(card_no='SYSTEM_CARD', user_id=user.id).first()
#     if precreated_card and precreated_card.status != "ACTIVE":
#         precreated_card.status = "ACTIVE"
#         db.session.commit()
#
#     return jsonify({'token': token}), 200
#
#
# @app.route('/create_card', methods=['POST'])
# @token_required
# def create_card():
#     data = request.get_json()
#     card_no = data.get('card_no')
#     user_id = data.get('user_id')
#
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({'message': 'User not found'}), 404
#
#     # Create a new card and add it to the user's cards
#     new_card = Card(card_no=card_no, user_id=user.id)
#     db.session.add(new_card)
#     db.session.commit()
#
#     return jsonify({'message': 'Card created successfully'}), 201
#
#
# @app.route('/update_card/<int:card_id>', methods=['PUT'])
# @token_required
# def update_card(card_id):
#     data = request.get_json()
#     card = Card.query.get(card_id)
#
#     if not card:
#         return jsonify({'message': 'Card not found'}), 404
#
#     # Update card details (except for "SYSTEM_CARD")
#     if card.label != "SYSTEM_CARD":
#         card.card_no = data.get('card_no', card.card_no)
#         card.status = data.get('status', card.status)
#
#     db.session.commit()
#
#     return jsonify({'message': 'Card updated successfully'}), 200
#
#
# @app.route('/delete_card/<int:card_id>', methods=['DELETE'])
# @token_required
# def delete_card(card_id):
#     card = Card.query.get(card_id)
#
#     if not card:
#         return jsonify({'message': 'Card not found'}), 404
#
#     if not card.card_no == 'SYSTEM_CARD':
#         # Mark the card as "DELETED"
#         card.status = "DELETED"
#         db.session.commit()
#     else:
#         return jsonify({'message': 'This card can not be modified'}), 401
#
#     return jsonify({'message': 'Card marked as deleted'}), 200
#
#
#
#
#
# @app.route('/create_transaction', methods=['POST'])
# @token_required
# def create_transaction():
#     data = request.get_json()
#     card_id = data.get('card_id')
#     amount = data.get('amount')
#     description = data.get('description')
#
#     card = Card.query.get(card_id)
#     if not card:
#         return jsonify({'message': 'Card not found'}), 404
#
#     # Create a new transaction associated with the card
#     new_transaction = Transaction(card_id=card.id, amount=amount, description=description)
#     db.session.add(new_transaction)
#     db.session.commit()
#
#     return jsonify({'message': 'Transaction created successfully'}), 201
#
#
# @app.route('/list_transactions/<int:card_id>', methods=['POST'])
# @token_required
# def list_transactions(card_id):
#     card = Card.query.get(card_id)
#     if not card:
#         return jsonify({'message': 'Card not found'}), 404
#
#     filter_type = request.json.get('filter')  # The filter argument specifies the view type
#
#     if filter_type == 'detailed':
#         # Retrieve transactions associated with the card in a detailed view
#         transactions = Transaction.query.filter_by(card_id=card.id).all()
#         transaction_list = [
#             {
#                 'id': t.id,
#                 'amount': t.amount,
#                 'description': t.description,
#                 'date_created': t.date_created
#             }
#             for t in transactions
#         ]
#     elif filter_type == 'summary':
#         user_id = request.user_id  # Assuming you have access to the user's ID from the token
#
#         # Retrieve user's active and passive cards
#         active_cards = Card.query.filter_by(user_id=user_id, status="ACTIVE").all()
#         passive_cards = Card.query.filter_by(user_id=user_id, status="PASSIVE").all()
#
#         # Calculate the total amount spent on active and passive cards
#         active_total_amount = sum([t.amount for card in active_cards for t in card.transactions])
#         passive_total_amount = sum([t.amount for card in passive_cards for t in card.transactions])
#
#         transaction_list = {
#             'active_cards_count': len(active_cards),
#             'active_total_amount': active_total_amount,
#             'passive_total_amount': passive_total_amount
#         }
#     else:
#         return jsonify({'message': 'Invalid filter type'}), 400
#
#     return jsonify({'transactions': transaction_list}), 200
#
#
#
# @app.route('/perform_transaction', methods=['POST'])
# @token_required
# def perform_transaction():
#     data = request.get_json()
#     card_id = data.get('card_id')
#     amount = data.get('amount')
#     description = data.get('description')
#
#     card = Card.query.get(card_id)
#     if not card:
#         return jsonify({'message': 'Card not found'}), 404
#
#     # Check if the card is active
#     if card.status != "ACTIVE":
#         return jsonify({'message': 'Card is not active'}), 400
#
#     # Perform the transaction
#     new_transaction = Transaction(amount=amount, card_id=card.id, description=description)
#     db.session.add(new_transaction)
#     db.session.commit()
#
#     return jsonify({'message': 'Transaction performed successfully'}), 201
#
#
# @app.route('/list_transactions/<int:card_id>', methods=['GET'])
# @token_required
# def list_transactions(card_id):
#     card = Card.query.get(card_id)
#     if not card:
#         return jsonify({'message': 'Card not found'}), 404
#
#     # Retrieve the transactions associated with the card
#     transactions = Transaction.query.filter_by(card_id=card.id).all()
#
#     return jsonify({'transactions': [transaction.serialize() for transaction in transactions]}), 200
#
# def decode_token(token):
#     try:
#         payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
#         return payload.get('user_id')
#     except jwt.ExpiredSignatureError:
#         return None  # Token has expired
#     except jwt.DecodeError:
#         return None  # Token is invalid
#
# if __name__ == '__main__':
#     # with app.app_context():
#     #     db.create_all()
#     app.run(debug=True)

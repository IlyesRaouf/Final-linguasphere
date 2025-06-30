from linguasphere_app import create_app
from linguasphere_app.extensions import db

app = create_app()

with app.app_context():
    db.create_all()
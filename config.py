import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ma_cle_secrete_unique_131')
    
    # Chemin relatif depuis le package linguasphere_app
    BASE_DIR = Path(__file__).parent.parent
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{BASE_DIR}/instance/app.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
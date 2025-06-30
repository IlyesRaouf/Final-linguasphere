import os
import sys
from pathlib import Path

def reset_database():
    try:
        from linguasphere_app.main import create_app
        from linguasphere_app.extensions import db
    except ImportError as e:
        print(f"Erreur d'importation : {e}")
        return False

    # Chemin absolu vers le dossier du projet
    BASE_DIR = Path(__file__).parent
    INSTANCE_DIR = BASE_DIR / "linguasphere_app" / "instance"
    DB_PATH = INSTANCE_DIR / "app.db"

    # Créer le dossier instance si inexistant
    INSTANCE_DIR.mkdir(exist_ok=True, parents=True)

    # Configurer l'application
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    print(f"Chemin de la base de données : {DB_PATH}")

    with app.app_context():
        try:
            # Vérifier les permissions
            test_file = INSTANCE_DIR / "test_permissions.txt"
            test_file.write_text("test")
            test_file.unlink()
            print("Permissions OK")

            # Réinitialiser la base
            db.drop_all()
            db.create_all()
            db.session.commit()

            # Vérification finale
            if DB_PATH.exists():
                print(f"Base de données créée avec succès : {DB_PATH}")
                return True
            else:
                print("ERREUR: Le fichier n'a pas été créé")
                return False

        except Exception as e:
            print(f"ERREUR lors de la création : {str(e)}")
            return False

if __name__ == "__main__":
    if reset_database():
        sys.exit(0)
    else:
        sys.exit(1)
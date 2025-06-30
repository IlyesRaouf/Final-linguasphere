from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort, jsonify
from flask_login import login_required
from ..user import User  # Changé de ..models à ..user
from ..models import UserProgress, CompletedDialogue, Badge, UserBadge, Activity, Feedback  # Ajouté Feedback
from ..extensions import db
from datetime import datetime

main_bp = Blueprint("main_bp", __name__)

# Interactive dialogue 1: Ordering a coffee (in English)
dialogue_flow_1 = {
    "start": {
        "text": "Hello! What can I get for you today?",
        "translation_fr": "Bonjour ! Que puis-je vous servir aujourd'hui ?",
        "grammar_tip": "Use 'What can I...?' to offer a service or ask for a preference in a polite way. It's a common structure in service interactions.",
        "audio": "audio/dialogue1_start.mp3",
        "options": {
            "I'd like a coffee, please.": {"next": "order_coffee", "points": 5},
            "What are your special coffees?": {"next": "special_coffee", "points": 7},
            "I'm not sure yet.": {"next": "thinking", "points": 3}
        }
    },
    # ... (le reste de dialogue_flow_1 reste inchangé)
}

# Interactive dialogue 2: Reserving a table (in English)
dialogue_flow_2 = {
    "start": {
        "text": "Hello, welcome to our restaurant! Do you have a reservation?",
        "translation_fr": "Bonjour, bienvenue dans notre restaurant ! Avez-vous une réservation ?",
        "grammar_tip": "'Do you have...?' is a common way to inquire about possession or arrangements.",
        "audio": None,  # Remplacer par "audio/dialogue2_start.mp3" une fois le fichier créé
        "options": {
            "No, I don't. Can I make one now?": {"next": "make_reservation", "points": 5},
            "Yes, under the name Smith.": {"next": "check_reservation", "points": 5},
            "I'm just looking, thanks.": {"next": "just_looking", "points": 3}
        }
    },
    # ... (le reste de dialogue_flow_2 reste inchangé)
}

# Interactive dialogue 3: Asking for directions (in English)
dialogue_flow_3 = {
    "start": {
        "text": "Excuse me, can you help me find the train station?",
        "translation_fr": "Excusez-moi, pouvez-vous m'aider à trouver la gare ?",
        "grammar_tip": "'Can you help me...?' is a polite way to ask for assistance.",
        "audio": None,  # Remplacer par "audio/dialogue3_start.mp3" une fois le fichier créé
        "options": {
            "Sure, it's not far from here.": {"next": "give_directions", "points": 5},
            "I'm not sure, but I can check.": {"next": "check_directions", "points": 4}
        }
    },
    # ... (le reste de dialogue_flow_3 reste inchangé)
}

# Liste des dialogues disponibles
dialogues_info = [
    {
        "id": 1,
        "title": "Commander un café",
        "description": "Pratiquez une conversation dans un café pour commander une boisson.",
        "points": 20,
        "locked": False,
        "required_level": 1
    },
    {
        "id": 2,
        "title": "Réserver une table",
        "description": "Apprenez à réserver une table dans un restaurant.",
        "points": 20,
        "locked": False,
        "required_level": 1
    },
    {
        "id": 3,
        "title": "Demander des directions",
        "description": "Pratiquez comment demander des indications pour trouver un lieu.",
        "points": 20,
        "locked": False,
        "required_level": 1
    }
]

dialogue_flows = {
    1: dialogue_flow_1,
    2: dialogue_flow_2,
    3: dialogue_flow_3
}

# Route pour la page d'accueil
@main_bp.route("/")
def home():
    return render_template("home.html", title="Bienvenue sur LinguaSphere")

# Route pour soumettre un avis
@main_bp.route("/submit_feedback", methods=['POST'])
def submit_feedback():
    try:
        description = request.form['description']
        rating = request.form['rating']
        language = request.form['language']

        if not description or not rating or not language:
            return jsonify({'success': False, 'message': 'Tous les champs sont requis.'}), 400

        rating = int(rating)
        if rating < 0 or rating > 5:
            return jsonify({'success': False, 'message': 'La note doit être entre 0 et 5.'}), 400

        new_feedback = Feedback(description=description, rating=rating, language=language)
        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Fonction utilitaire pour obtenir l'utilisateur actuel
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@main_bp.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        flash("Vous devez être connecté pour accéder à cette page", "error")
        return redirect(url_for("auth.login"))
    
    if not user.progress:
        user.progress = UserProgress(points=0, level=1)
        db.session.commit()
    
    user_badges = [ub.badge_info.name for ub in user.badges]
    recent_activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.timestamp.desc()).limit(5).all()
    
    return render_template(
        "dashboard.html",
        title="Mon Parcours - LinguaSphere",
        username=user.username,
        user_points=user.progress.points,
        current_user_level=user.progress.level,
        user_badges=user_badges,
        activities=recent_activities
    )

@main_bp.route("/apprendre")
def apprendre_home():
    return render_template("apprendre_home.html", title="Apprendre - LinguaSphere")

@main_bp.route("/apprendre/dialogues")
def apprendre_dialogues():
    user = get_current_user()
    dialogues = dialogues_info.copy()
    
    if user:
        user_level = user.progress.level
        completed_dialogue_ids = [cd.dialogue_id for cd in user.completed_dialogues]
        
        for dialogue in dialogues:
            dialogue["completed"] = dialogue["id"] in completed_dialogue_ids
            if dialogue.get("locked") and dialogue.get("required_level", 99) <= user_level:
                dialogue["locked"] = False
    
    return render_template("dialogues_list.html", title="Dialogues Interactifs - LinguaSphere", dialogues=dialogues)

@main_bp.route("/apprendre/dialogues/<int:dialogue_id>", methods=['GET', 'POST'])
def dialogue_detail(dialogue_id):
    user = get_current_user()
    
    if dialogue_id not in dialogue_flows:
        flash("Ce dialogue n'existe pas.", "error")
        return redirect(url_for('main_bp.apprendre_dialogues'))
    
    dialogue_info = next((d for d in dialogues_info if d["id"] == dialogue_id), None)
    if dialogue_info and dialogue_info.get("locked", False):
        if not user or user.progress.level < dialogue_info.get("required_level", 99):
            flash("Ce dialogue est verrouillé. Atteignez le niveau requis pour le débloquer.", "error")
            return redirect(url_for('main_bp.apprendre_dialogues'))
    
    dialogue_state_key = f'dialogue_state_{dialogue_id}'
    current_dialogue_flow = dialogue_flows[dialogue_id]
    
    if request.method == 'POST':
        selected_option = request.form.get('user_choice')
        
        if dialogue_state_key not in session:
            session[dialogue_state_key] = 'start'
        
        current_state = session[dialogue_state_key]
        
        if current_state not in current_dialogue_flow:
            current_state = 'start'
            session[dialogue_state_key] = current_state
        
        current_options = current_dialogue_flow[current_state]['options']
        
        if selected_option in current_options:
            next_state = current_options[selected_option]['next']
            points_earned = current_options[selected_option]['points']
            session[dialogue_state_key] = next_state
            
            if user:
                user.progress.add_points(points_earned)
                Activity.log(
                    user_id=user.id,
                    activity_type="dialogue_step",
                    description=f"Choix dans le dialogue {dialogue_id}: {selected_option}",
                    points_earned=points_earned
                )
                db.session.commit()
                
                if next_state in current_dialogue_flow and not current_dialogue_flow[next_state]['options']:
                    record_dialogue_completion(user.id, dialogue_id)
        
        return redirect(url_for('main_bp.dialogue_detail', dialogue_id=dialogue_id))
    
    if dialogue_state_key not in session:
        session[dialogue_state_key] = 'start'
    
    current_state = session[dialogue_state_key]
    if current_state not in current_dialogue_flow:
        current_state = 'start'
        session[dialogue_state_key] = current_state
    
    current_node = current_dialogue_flow[current_state]
    
    # Calculer la progression dans le dialogue
    total_steps = len(current_dialogue_flow)
    current_step = sum(1 for state in current_dialogue_flow if state <= current_state)  # Approximation
    progress_percentage = (current_step / total_steps) * 100 if total_steps > 0 else 0
    
    return render_template(
        "dialogue_interactive.html",
        title=f"Dialogue {dialogue_id}: {dialogue_info['title']}",
        step_text=current_node['text'],
        translation_fr=current_node['translation_fr'],
        grammar_tip=current_node['grammar_tip'],
        audio=current_node['audio'],
        options=list(current_node['options'].items()) if current_node['options'] else None,
        dialogue_id=dialogue_id,
        progress_percentage=progress_percentage
    )

def record_dialogue_completion(user_id, dialogue_id):
    user = User.query.get(user_id)
    if not user:
        return
    
    existing_completion = CompletedDialogue.query.filter_by(
        user_id=user_id, dialogue_id=dialogue_id
    ).first()
    
    if not existing_completion:
        dialogue_info = next((d for d in dialogues_info if d["id"] == dialogue_id), None)
        if not dialogue_info:
            return
        
        points_earned = dialogue_info.get("points", 10)
        
        completion = CompletedDialogue(user_id=user_id, dialogue_id=dialogue_id)
        db.session.add(completion)
        
        user.progress.add_points(points_earned)
        
        Activity.log(
            user_id=user_id,
            activity_type="dialogue_completed",
            description=f"Dialogue complété : {dialogue_info['title']}",
            points_earned=points_earned
        )
        
        check_and_award_badges(user)
        
        db.session.commit()
        
        flash(f"Félicitations ! Vous avez terminé le dialogue et gagné {points_earned} points.", "success")

def check_and_award_badges(user):
    if len(user.completed_dialogues) == 1:
        award_badge(user.id, "Premier Dialogue", "Vous avez complété votre premier dialogue !")
    
    if len(user.completed_dialogues) == 3:
        award_badge(user.id, "Apprenti Linguiste", "Vous avez complété 3 dialogues !")
    
    if user.progress.level >= 2:
        award_badge(user.id, "Niveau 2 Atteint", "Vous avez atteint le niveau 2 !")
    
    if user.progress.level >= 3:
        award_badge(user.id, "Niveau 3 Atteint", "Vous avez atteint le niveau 3 !")

def award_badge(user_id, badge_name, description=None):
    badge = Badge.query.filter_by(name=badge_name).first()
    if not badge:
        badge = Badge(name=badge_name, description=description or badge_name)
        db.session.add(badge)
        db.session.flush()
    
    existing_user_badge = UserBadge.query.filter_by(
        user_id=user_id, badge_id=badge.id
    ).first()
    
    if not existing_user_badge:
        user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
        db.session.add(user_badge)
        
        Activity.log(
            user_id=user_id,
            activity_type="badge_earned",
            description=f"Badge obtenu : {badge_name}",
            points_earned=0
        )
        
        flash(f"Félicitations ! Vous avez obtenu le badge : {badge_name}", "success")

@main_bp.route("/reset_dialogue", methods=['GET', 'POST'])
def reset_dialogue():
    dialogue_id = request.args.get('dialogue_id', 1, type=int)
    dialogue_state_key = f'dialogue_state_{dialogue_id}'
    
    if dialogue_state_key in session:
        session.pop(dialogue_state_key, None)
    
    return redirect(url_for('main_bp.dialogue_detail', dialogue_id=dialogue_id))

@main_bp.route("/apprendre/contenus")
def apprendre_contenus():
    try:
        contenus = [
            {
                "id": 2,
                "title": "Video: Greetings",
                "type": "Video",
                "level": "Débutant",
                "url": "/apprendre/contenus/videos/greetings"
            },
            {
                "id": 3,
                "title": "Video: Nice to Meet You",
                "type": "Video",
                "level": "Débutant",
                "url": "/apprendre/contenus/videos/nice"
            },
            {
                "id": 4,
                "title": "Video: Simple Conversation",
                "type": "Video",
                "level": "Débutant",
                "url": "/apprendre/contenus/videos/conversation"
            },
        ]
        return render_template("contenus_list.html", title="Contenus Créatifs - LinguaSphere", contenus=contenus)
    except Exception as e:
        flash(f"Une erreur est survenue. Veuillez réessayer plus tard. ({str(e)})", "error")
        return redirect(url_for("main_bp.apprendre_home"))

@main_bp.route("/apprendre/contenus/videos/greetings")
def video_greetings():
    try:
        return render_template("video_greetings.html", title="English for Beginners - Greetings")
    except Exception as e:
        flash(f"Erreur lors du chargement de la vidéo. Veuillez réessayer. ({str(e)})", "error")
        return redirect(url_for("main_bp.apprendre_contenus"))

@main_bp.route("/apprendre/contenus/videos/nice")
def video_nice():
    try:
        return render_template("video_nice_to_meet_you.html", title="English for Beginners - Nice to Meet You")
    except Exception as e:
        flash(f"Erreur lors du chargement de la vidéo. Veuillez réessayer. ({str(e)})", "error")
        return redirect(url_for("main_bp.apprendre_contenus"))

@main_bp.route("/apprendre/contenus/videos/conversation")
def video_conversation():
    try:
        return render_template("video_conversation.html", title="English for Beginners - Simple Conversation")
    except Exception as e:
        flash(f"Erreur lors du chargement de la vidéo. Veuillez réessayer. ({str(e)})", "error")
        return redirect(url_for("main_bp.apprendre_contenus"))

@main_bp.route("/progression")
def progression():
    user = get_current_user()
    if not user:
        flash("Vous devez être connecté pour accéder à cette page", "error")
        return redirect(url_for("auth.login"))
    
    try:
        if not user.progress:
            user.progress = UserProgress(points=0, level=1)
            db.session.commit()
        
        user_badges = [ub.badge_info.name for ub in user.badges if ub.badge_info]
        
        completed_dialogues = []
        for cd in user.completed_dialogues:
            dialogue_info = next((d for d in dialogues_info if d["id"] == cd.dialogue_id), None)
            if dialogue_info:
                completed_dialogues.append({
                    "title": dialogue_info["title"],
                    "completed_at": cd.completed_at.strftime("%d/%m/%Y"),
                    "points": dialogue_info.get("points", 10)
                })
        
        next_level = user.progress.level + 1
        points_needed = 0
        level_thresholds = {
            1: 0,
            2: 100,
            3: 250,
            4: 500,
            5: 1000,
        }
        
        if next_level in level_thresholds:
            points_needed = level_thresholds[next_level] - user.progress.points
        
        recent_activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.timestamp.desc()).limit(10).all()
        
        return render_template(
            "progression.html", 
            title="Ma Progression - LinguaSphere", 
            username=user.username,
            points=user.progress.points,
            level=user.progress.level,
            next_level=next_level,
            points_needed=points_needed,
            badges=user_badges,
            completed_dialogues=completed_dialogues,
            activities=recent_activities
        )
    except Exception as e:
        flash("Une erreur est survenue. Veuillez réessayer plus tard.", "error")
        return redirect(url_for("main_bp.dashboard"))

@main_bp.route("/profil")
def profil():
    user = get_current_user()
    if not user:
        flash("Vous devez être connecté pour accéder à cette page", "error")
        return redirect(url_for("auth.login"))
    
    try:
        if not user.progress:
            user.progress = UserProgress(points=0, level=1)
            db.session.commit()
        
        return render_template(
            "profil.html",
            title="Mon Profil - LinguaSphere",
            username=user.username,
            email=user.email,
            points=user.progress.points,
            level=user.progress.level
        )
    except Exception as e:
        flash("Une erreur est survenue. Veuillez réessayer plus tard.", "error")
        return redirect(url_for("main_bp.dashboard"))

@main_bp.route("/a-propos")
def a_propos():
    return render_template("a_propos.html", title="À Propos - LinguaSphere")

@main_bp.route("/contact")
def contact():
    return render_template("contact.html", title="Contact - LinguaSphere")

@main_bp.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    try:
        # Vérifier les en-têtes
        content_type = request.headers.get('Content-Type')
        print(f"Content-Type reçu : {content_type}")  # Log

        # Récupérer le JSON
        data = request.get_json(silent=True)
        if data is None:
            print("Erreur : Aucun JSON valide reçu")  # Log
            return jsonify({"error": "Requête JSON invalide"}), 400

        user_msg = data.get("message", "").lower()
        print(f"Message reçu : {user_msg}")  # Log

        # Logique du chatbot
        if "hello" in user_msg or "hi" in user_msg:
            response = "Hi there! I'm Linguabot. How can I help you today?"
        elif "bonjour" in user_msg:
            response = "Hello! How can I help you today?"
        elif "كيف" in user_msg or "حال" in user_msg:
            response = "I'm doing great, thank you! How can I assist you?"
        elif "name" in user_msg:
            response = "My name is Linguabot. I'm here to help you practice English!"
        elif "thank" in user_msg or "merci" in user_msg or "شكرا" in user_msg:
            response = "You're welcome!"
        elif "help" in user_msg:
            response = "Sure! I can help you with English. Ask me anything."
        else:
            response = "Sorry, I didn’t understand that. Could you try asking in another way?"

        return jsonify({"response": response})
    except Exception as e:
        print(f"Erreur dans /chatbot : {str(e)}")  # Log
        return jsonify({"error": str(e)}), 500
"""
Assistant IA Commercial
Version complète : Multi-utilisateurs + Resume appel + Base de connaissances
"""

import os
import logging
import json
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

try:
    from hubspot_utils import HubSpotManager
    from ai_utils import AIAssistant
    from audio_utils import AudioProcessor
    from knowledge_base import KnowledgeBase
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Vérifie que tous les fichiers sont présents:")
    print("- hubspot_utils.py")
    print("- ai_utils.py")
    print("- audio_utils.py")
    print("- knowledge_base.py")
    exit(1)

# Configuration logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Chargement variables d'environnement
load_dotenv()

# Initialisation des modules
hubspot = HubSpotManager(os.getenv('HUBSPOT_API_KEY'))
ai_assistant = AIAssistant(os.getenv('GROQ_API_KEY'))
audio_processor = AudioProcessor(os.getenv('OPENAI_API_KEY'))
knowledge_base = KnowledgeBase()

# Contexte conversation utilisateur
user_context = {}

# Liste des utilisateurs autorisés
AUTHORIZED_USERS = {}
USERS_FILE = "authorized_users.json"


def load_authorized_users():
    """Charge la liste des utilisateurs autorisés"""
    global AUTHORIZED_USERS
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                AUTHORIZED_USERS = json.load(f)
                logger.info(f"✅ {len(AUTHORIZED_USERS)} utilisateurs chargés")
    except Exception as e:
        logger.error(f"Erreur chargement utilisateurs: {e}")


def save_authorized_users():
    """Sauvegarde la liste des utilisateurs autorisés"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(AUTHORIZED_USERS, f, indent=2, ensure_ascii=False)
        logger.info("✅ Utilisateurs sauvegardés")
    except Exception as e:
        logger.error(f"Erreur sauvegarde utilisateurs: {e}")


def is_authorized(user_id: int) -> bool:
    """Vérifie si un utilisateur est autorisé"""
    return str(user_id) in AUTHORIZED_USERS


def get_user_name(user_id: int) -> str:
    """Récupère le nom d'un utilisateur"""
    user_data = AUTHORIZED_USERS.get(str(user_id), {})
    return user_data.get('name', 'Utilisateur')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start - Accueil"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    # Si premier utilisateur, l'autoriser automatiquement
    if len(AUTHORIZED_USERS) == 0:
        AUTHORIZED_USERS[str(user_id)] = {
            "name": first_name,
            "username": username,
            "role": "Admin",
            "added_date": datetime.now().isoformat()
        }
        save_authorized_users()
        logger.info(f"🎉 Premier utilisateur: {first_name} (ID: {user_id})")

    # Vérification autorisation
    if not is_authorized(user_id):
        await update.message.reply_text(
            f"❌ Accès refusé.\n\n"
            f"Ton ID: `{user_id}`\n"
            f"Username: @{username}\n\n"
            f"Demande à un admin de t'ajouter avec:\n"
            f"`/add_user {user_id} Ton_Prénom Ton_Role`"
        )
        return

    user_name = get_user_name(user_id)

    welcome_message = f"""
👋 Bonjour {user_name} !

Je suis l'assistant IA Rupella Consulting.

🎯 **Ce que je peux faire :**
• Rédiger messages et relances
• Gérer contacts et deals HubSpot
• Résumer appels (texte ou audio)
• Répondre aux questions commerciales
• Utiliser la base de connaissances Rupella

📱 **Commandes principales :**
/resume_appel - Résumer un appel
/deals - Deals ouverts HubSpot
/contacts - Recherche contact
/docs - Base de connaissances
/stats - Statistiques
/aide - Aide complète

💡 Parle-moi naturellement !

— Ton assistant Rupella IA
    """
    await update.message.reply_text(welcome_message)


async def aide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /aide - Documentation"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    help_text = """
📚 **Guide d'utilisation**

**Commandes principales :**
/start - Bienvenue
/resume_appel - Résumer un appel
/deals - Deals HubSpot
/contacts - Recherche contact
/docs - Documents Rupella
/search_doc - Chercher dans les docs
/stats - Statistiques
/aide - Cette aide

**Multi-utilisateurs (Admin) :**
/list_users - Liste utilisateurs
/add_user [ID] [Nom] [Role]
/remove_user [ID]

**Exemples :**

💬 Rédaction :
"Rédige une relance pour M. Dupont"
"Propose un message d'accroche Tech"

📝 Résumé appel :
/resume_appel Appel M. Soubeyran - 5 min - Intéressé BTP - Budget 50K - Rappel lundi

📊 HubSpot :
"Ajoute une note sur la fiche de Jean : RDV lundi"

❓ Questions :
"Comment répondre à l'objection tarifs ?"

— Ton assistant Rupella IA
    """
    await update.message.reply_text(help_text)


async def resume_appel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /resume_appel - Résume un appel"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    if not context.args:
        await update.message.reply_text(
            "📝 **Utilisation :**\n\n"
            "`/resume_appel [Description de l'appel]`\n\n"
            "**Exemple :**\n"
            "/resume_appel Appel M. Dupont Batimo - 5 min - Intéressé recrutement 3 chefs chantier - Budget 80K - Objection délais - Rappel mardi 10h\n\n"
            "— Ton assistant Rupella IA"
        )
        return

    description = ' '.join(context.args)
    await update.message.reply_text("🎧 Analyse en cours...")

    try:
        summary = ai_assistant.generate_call_summary(description)
        response = f"✅ **Résumé de l'appel**\n\n{summary}\n\n— Ton assistant Rupella IA"
        await update.message.reply_text(response)

        user_id = update.effective_user.id
        if user_id not in user_context:
            user_context[user_id] = {}

        user_context[user_id]['last_call_summary'] = summary
        user_context[user_id]['last_call_date'] = datetime.now().isoformat()
        user_context[user_id]['calls_analyzed'] = user_context[user_id].get('calls_analyzed', 0) + 1

        await update.message.reply_text(
            "💡 Veux-tu ajouter ce résumé dans HubSpot ?\n"
            "Réponds : 'Oui, ajoute sur [Nom du contact]'"
        )

    except Exception as e:
        logger.error(f"Erreur resume_appel: {e}")
        await update.message.reply_text("❌ Erreur génération résumé.\n\n— Ton assistant Rupella IA")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /stats - Statistiques utilisateur"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    user_id = update.effective_user.id
    user_name = get_user_name(user_id)
    context_data = user_context.get(user_id, {})

    messages_count = context_data.get('messages_count', 0)
    calls_count = context_data.get('calls_analyzed', 0)
    last_activity = context_data.get('last_activity', 'Aucune')

    stats_message = f"""
📊 **Statistiques de {user_name}**

💬 Messages: {messages_count}
🎧 Appels analysés: {calls_count}
⏰ Dernière activité: {last_activity}

🔗 HubSpot: ✅
🤖 IA: ✅ (Groq gratuit)
📚 Base connaissances: ✅

— Ton assistant Rupella IA
    """
    await update.message.reply_text(stats_message)


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Liste utilisateurs (Admin)"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    user_role = AUTHORIZED_USERS.get(str(user_id), {}).get('role', '')
    if user_role != 'Admin':
        await update.message.reply_text("❌ Réservé aux admins.")
        return

    if not AUTHORIZED_USERS:
        await update.message.reply_text("📋 Aucun utilisateur.")
        return

    message = "👥 **Utilisateurs autorisés :**\n\n"
    for uid, data in AUTHORIZED_USERS.items():
        name = data.get('name', 'Inconnu')
        role = data.get('role', 'User')
        username = data.get('username', 'N/A')
        message += f"• **{name}** ({role})\n"
        message += f"  ID: `{uid}` | @{username}\n\n"

    message += "— Ton assistant Rupella IA"
    await update.message.reply_text(message)


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ajouter utilisateur (Admin)"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    user_role = AUTHORIZED_USERS.get(str(user_id), {}).get('role', '')
    if user_role != 'Admin':
        await update.message.reply_text("❌ Réservé aux admins.")
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "ℹ️ **Usage :**\n"
            "`/add_user [ID] [Nom] [Role]`\n\n"
            "**Exemple :**\n"
            "`/add_user 123456789 Sarah Commercial`"
        )
        return

    new_user_id = context.args[0]
    new_user_name = context.args[1]
    new_user_role = ' '.join(context.args[2:])

    AUTHORIZED_USERS[new_user_id] = {
        "name": new_user_name,
        "role": new_user_role,
        "added_by": user_id,
        "added_date": datetime.now().isoformat()
    }

    save_authorized_users()

    await update.message.reply_text(
        f"✅ Utilisateur ajouté !\n\n"
        f"👤 {new_user_name} ({new_user_role})\n"
        f"ID: `{new_user_id}`\n\n"
        f"— Ton assistant Rupella IA"
    )


async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retirer utilisateur (Admin)"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    user_role = AUTHORIZED_USERS.get(str(user_id), {}).get('role', '')
    if user_role != 'Admin':
        await update.message.reply_text("❌ Réservé aux admins.")
        return

    if not context.args:
        await update.message.reply_text(
            "ℹ️ **Usage :**\n"
            "`/remove_user [ID]`"
        )
        return

    remove_id = context.args[0]

    if remove_id in AUTHORIZED_USERS:
        removed_user = AUTHORIZED_USERS.pop(remove_id)
        save_authorized_users()
        await update.message.reply_text(
            f"✅ Utilisateur retiré : {removed_user.get('name', 'Inconnu')}\n\n"
            f"— Ton assistant Rupella IA"
        )
    else:
        await update.message.reply_text(f"❌ Utilisateur {remove_id} non trouvé.")


async def list_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /deals - Liste deals HubSpot"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    await update.message.reply_text("🔍 Récupération deals...")

    try:
        deals = hubspot.get_open_deals()

        if not deals:
            response = "📊 Aucun deal ouvert.\n\n— Ton assistant Rupella IA"
        else:
            response = "📊 **Deals ouverts :**\n\n"
            for deal in deals[:10]:
                name = deal.get('properties', {}).get('dealname', 'Sans nom')
                amount = deal.get('properties', {}).get('amount', '0')
                stage = deal.get('properties', {}).get('dealstage', 'Non défini')

                response += f"• **{name}**\n  {amount}€ | {stage}\n\n"

            response += "— Ton assistant Rupella IA"

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Erreur deals: {e}")
        await update.message.reply_text("❌ Erreur HubSpot.\n\n— Ton assistant Rupella IA")


async def search_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /contacts - Recherche contacts"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    if not context.args:
        await update.message.reply_text(
            "ℹ️ **Usage :** `/contacts [nom]`\n"
            "**Exemple :** `/contacts Dupont`\n\n"
            "— Ton assistant Rupella IA"
        )
        return

    search_term = ' '.join(context.args)
    await update.message.reply_text(f"🔍 Recherche '{search_term}'...")

    try:
        contacts = hubspot.search_contacts(search_term)

        if not contacts:
            response = f"❌ Aucun contact pour '{search_term}'.\n\n— Ton assistant Rupella IA"
        else:
            response = f"👥 **Contacts trouvés :**\n\n"
            for contact in contacts[:5]:
                props = contact.get('properties', {})
                firstname = props.get('firstname', '')
                lastname = props.get('lastname', '')
                email = props.get('email', 'Pas d\'email')
                company = props.get('company', '')

                response += f"• **{firstname} {lastname}**\n  📧 {email}\n"
                if company:
                    response += f"  🏢 {company}\n"
                response += "\n"

            response += "— Ton assistant Rupella IA"

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Erreur contacts: {e}")
        await update.message.reply_text("❌ Erreur HubSpot.\n\n— Ton assistant Rupella IA")


async def list_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Liste documents base de connaissances"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    docs = knowledge_base.list_documents()

    if not docs:
        await update.message.reply_text(
            "📚 Aucun document.\n\n"
            "Envoie un fichier pour l'ajouter !\n\n"
            "— Ton assistant Rupella IA"
        )
        return

    categories = {}
    for doc in docs:
        cat = doc.get('category', 'general')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(doc)

    message = "📚 **Base de connaissances Rupella**\n\n"

    for category, category_docs in categories.items():
        message += f"**{category.upper()}**\n"
        for doc in category_docs:
            filename = doc.get('filename')
            words = doc.get('word_count', 0)
            message += f"• {filename} ({words} mots)\n"
        message += "\n"

    message += f"**Total:** {len(docs)} documents\n\n— Ton assistant Rupella IA"
    await update.message.reply_text(message)


async def search_in_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recherche dans documents"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    if not context.args:
        await update.message.reply_text(
            "ℹ️ **Usage :** `/search_doc [terme]`\n"
            "**Exemple :** `/search_doc tarifs BTP`\n\n"
            "— Ton assistant Rupella IA"
        )
        return

    query = ' '.join(context.args)
    await update.message.reply_text(f"🔍 Recherche '{query}'...")

    results = knowledge_base.search_documents(query)

    if not results:
        await update.message.reply_text(
            f"❌ Aucun résultat pour '{query}'.\n\n— Ton assistant Rupella IA"
        )
        return

    message = f"🔍 **Résultats pour '{query}' :**\n\n"

    for i, result in enumerate(results[:3], 1):
        filename = result.get('filename')
        category = result.get('category')
        excerpt = result.get('excerpt', '')[:150]

        message += f"{i}. **{filename}** ({category})\n   {excerpt}...\n\n"

    message += "— Ton assistant Rupella IA"
    await update.message.reply_text(message)


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion fichiers audio"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'ta_cle_openai_ici':
        await update.message.reply_text(
            "🎧 **Audio désactivé** (nécessite OpenAI Whisper)\n\n"
            "💡 **Utilise plutôt :**\n"
            "/resume_appel [description]\n\n"
            "— Ton assistant Rupella IA"
        )
        return

    await update.message.reply_text("🎧 Analyse audio...")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion documents pour base de connaissances"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("❌ Accès refusé.")
        return

    user_role = AUTHORIZED_USERS.get(str(user_id), {}).get('role', '')
    if user_role not in ['Admin', 'Manager']:
        await update.message.reply_text("❌ Réservé aux admins/managers.")
        return

    await update.message.reply_text("📄 Réception document...")

    try:
        document = update.message.document
        file = await document.get_file()
        filename = document.file_name
        file_path = f"temp_{filename}"

        await file.download_to_drive(file_path)

        category = "general"
        description = f"Ajouté par {get_user_name(user_id)}"

        success = knowledge_base.add_document(file_path, category, description)

        if success:
            await update.message.reply_text(
                f"✅ **Document ajouté !**\n\n"
                f"📄 {filename}\n"
                f"📁 Catégorie: {category}\n\n"
                f"Le bot peut maintenant utiliser ces infos !\n\n"
                f"— Ton assistant Rupella IA"
            )
        else:
            await update.message.reply_text(
                f"❌ Erreur ajout document.\n"
                f"Formats supportés: .txt, .md, .pdf, .docx\n\n"
                f"— Ton assistant Rupella IA"
            )

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Erreur document: {e}")
        await update.message.reply_text("❌ Erreur traitement.\n\n— Ton assistant Rupella IA")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion messages texte"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("❌ Accès refusé. Utilise /start")
        return

    user_message = update.message.text
    context_data = user_context.get(user_id, {})

    if user_id not in user_context:
        user_context[user_id] = {}
    user_context[user_id]['messages_count'] = context_data.get('messages_count', 0) + 1
    user_context[user_id]['last_activity'] = datetime.now().strftime("%d/%m/%Y %H:%M")

    lower_msg = user_message.lower()

    if "ajoute une note" in lower_msg or "ajoute sur" in lower_msg:
        await handle_add_note(update, user_message)
        return

    await update.message.reply_text("💭 Je réfléchis...")

    try:
        kb_context = knowledge_base.get_context_for_query(user_message, max_words=800)
        ai_response = ai_assistant.chat(user_message, context_data, kb_context)
        response = f"{ai_response}\n\n— Ton assistant Rupella IA"
        await update.message.reply_text(response)

        user_context[user_id]['last_message'] = user_message

    except Exception as e:
        logger.error(f"Erreur IA: {e}")
        await update.message.reply_text("❌ Erreur IA.\n\n— Ton assistant Rupella IA")


async def handle_add_note(update: Update, message: str):
    """Ajout note HubSpot"""
    try:
        if "sur la fiche de" in message.lower():
            parts = message.lower().split("sur la fiche de")
            if len(parts) == 2:
                name_and_note = parts[1].split(":")
                if len(name_and_note) == 2:
                    contact_name = name_and_note[0].strip()
                    note_text = name_and_note[1].strip()

                    contacts = hubspot.search_contacts(contact_name)
                    if contacts:
                        contact_id = contacts[0]['id']
                        success = hubspot.add_note_to_contact(contact_id, note_text)

                        if success:
                            await update.message.reply_text(
                                f"✅ Note ajoutée sur {contact_name}\n\n— Ton assistant Rupella IA"
                            )
                        else:
                            await update.message.reply_text("❌ Erreur ajout note.")
                    else:
                        await update.message.reply_text(f"❌ Contact '{contact_name}' non trouvé.")
                    return

        await update.message.reply_text(
            "ℹ️ Format: 'Ajoute une note sur la fiche de [Nom] : [texte]'\n\n"
            "— Ton assistant Rupella IA"
        )

    except Exception as e:
        logger.error(f"Erreur note: {e}")
        await update.message.reply_text("❌ Erreur.")


def main():
    """Fonction principale"""
    load_authorized_users()

    required_vars = ['TELEGRAM_BOT_TOKEN', 'GROQ_API_KEY', 'HUBSPOT_API_KEY']
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"❌ Variable {var} manquante")
            return

    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("aide", aide))
    application.add_handler(CommandHandler("resume_appel", resume_appel))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("deals", list_deals))
    application.add_handler(CommandHandler("contacts", search_contacts))
    application.add_handler(CommandHandler("list_users", list_users))
    application.add_handler(CommandHandler("add_user", add_user))
    application.add_handler(CommandHandler("remove_user", remove_user))
    application.add_handler(CommandHandler("docs", list_docs))
    application.add_handler(CommandHandler("search_doc", search_in_docs))

    application.add_handler(MessageHandler(
        filters.VOICE | filters.AUDIO | filters.Document.AUDIO,
        handle_audio
    ))

    application.add_handler(MessageHandler(
        filters.Document.PDF | filters.Document.DOC | filters.Document.TXT,
        handle_document
    ))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Assistant Rupella IA (Multi-users + KB) démarré !")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

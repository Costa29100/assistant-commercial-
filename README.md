# assistant-commercial-
Assistant IA Commercial – Rupella Consulting  Un assistant intelligent pour équipes commerciales, propulsé par Python + Telegram Bot + HubSpot + IA. Ce bot aide les commerciaux à gagner du temps, résumer leurs appels, gérer leurs contacts HubSpot et accéder à une base de connaissances partagée.

🚀 Fonctionnalités principales

🤖 Assistant conversationnel IA — basé sur Groq ou OpenAI, capable de répondre à toutes les questions commerciales.

📞 Résumé d’appels automatiques — via texte ou audio, avec stockage et statistiques par utilisateur.

💼 Intégration HubSpot — gestion des deals, contacts, notes et interactions directement depuis Telegram.

🧩 Base de connaissances interne — ajout, recherche et contextualisation de documents internes (PDF, DOCX, TXT).

👥 Multi-utilisateurs & rôles — gestion d’autorisations par rôle : Admin, Manager, Commercial.

📊 Statistiques d’utilisation — suivi des activités, nombre d’appels résumés et messages envoyés.

⚙️ Technologies utilisées

Langage : Python 3.13

Framework : python-telegram-bot

Modules personnalisés :

hubspot_utils.py — gestion des appels API HubSpot

ai_utils.py — interface Groq / OpenAI

audio_utils.py — transcription et analyse audio

knowledge_base.py — gestion et recherche de documents

Autres dépendances : dotenv, logging, json, datetime

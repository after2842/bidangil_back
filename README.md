# Bidangil Backend

Bidangil Backend powers a cross-border e-commerce and community platform.  
It handles everything from user accounts and order requests to payment processing, shipping logistics, admin workflows, order history, community posts, comments, and more.  
The backend exposes REST APIs **and** real-time WebSocket channels so users and admins can automate the entire proxy-purchase process.

## Motivation & Challenges

Buying from Korean e-commerce sites is tricky for non-residents: most stores require a Korean credit card, a local phone number, and rarely offer international shipping.  
**Bidangil** streamlines that experience by orchestrating the whole journey—from the user’s initial request to final delivery at their U.S. doorstep—while hiding the complexity of payments, currency exchange, customs, and tracking.

Key challenges:

* Coordinating a **multi-step workflow** (quote → item payment → purchase → delivery fee → shipping → delivery confirmation).
* **Integrating third-party services**—Stripe for payments, carrier APIs for tracking, OpenAI for AI-generated avatars.
* Maintaining a **responsive UX** for inherently long-running tasks (shipping updates, image generation) via asynchronous workers and WebSockets.

## Highlights

* **Custom Django-admin workflow**  
  Inline models + a bespoke `save_formset` override let staff update item prices once and trigger a single Stripe session, preventing duplicate charges.
* **Asynchronous tasks & real-time push**  
  Celery handles heavy work (shipping polls, avatar generation); Django Channels pushes instant updates to the frontend when tasks finish.
* **Seamless integrations**  
  Stripe (item & delivery payments), AWS S3 (media), FedEx/EMS tracking APIs, and OpenAI (GPT-4o, image generation) are wired in behind clean service layers.
* **Robust architecture**  
  Built on Django 5.2 + Daphne (ASGI). DRF provides a clean API surface, and comprehensive models cover orders, profiles, posts, comments, and likes. MySQL backs persistent data.

## Tech Stack

| Layer | Tooling |
|-------|---------|
| **Language / Framework** | Python 3.11 ↑ · Django 5.2 · Django REST Framework |
| **Async & RT** | Celery 5.3 · Redis 7 (broker & channel layer) · Django Channels |
| **DB** | MySQL 8 |
| **Cloud & Integrations** | AWS S3 · Stripe API · FedEx/EMS APIs · OpenAI GPT-4o / image |
| **Utilities** | django-celery-beat · django-cors-headers |

## Quick Start

```bash
git clone https://github.com/your-org/bidangil_back.git
cd bidangil_back
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add DB credentials, Stripe & OpenAI keys
python manage.py migrate
python manage.py runserver

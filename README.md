# Bidangil Backend

Bidangil Backend is a Django-based web service that powers a cross-border e-commerce and community platform. It handles everything from user accounts and order requests to payment processing, shipping logistics, and community content. This backend provides RESTful APIs and real-time communication channels to support the Bidangil frontend, ensuring users can seamlessly request products, track deliveries, and engage with the community.

## Motivation & Challenges

The project was built to streamline the complex process of international personal shopping and shipping. Traditionally, arranging an overseas purchase involves multiple steps (placing requests, paying item and delivery fees, tracking shipments, etc.) and navigating various constraints like payment gateways and customs regulations. **Bidangil** was motivated by the need to automate and simplify this workflow for users and administrators alike. Key challenges included orchestrating multi-step order fulfillment (from initial request to final delivery), integrating third-party services (for payments and shipping), and maintaining a responsive user experience for processes that are inherently asynchronous or lengthy (such as waiting for items to ship or generating custom user avatars with AI).

## Highlights

- **Custom Order Workflow in Django Admin:** The backend features a tailored Django admin interface to manage orders through their entire lifecycle. It uses inline models and custom admin actions to allow staff to view and update an order’s items, payment status, shipping details, and step-by-step progress all on one screen. This reduces the need for separate tools or manual tracking and ensures consistency in the fulfillment process.
- **Asynchronous Tasks & Real-Time Updates:** Heavy-lifting operations are offloaded to Celery task queues. For example, the system periodically checks shipment status (e.g., via FedEx API) in the background and updates orders automatically. It also generates user avatars using OpenAI’s image API in a worker task. Upon completion of these tasks, the backend uses Django Channels (WebSockets) to immediately notify the frontend – for instance, informing a user in real time when their AI-generated avatar is ready to use.
- **Third-Party Integrations:** Bidangil Backend seamlessly integrates with external services. It incorporates Stripe for secure payment processing (managing item purchases and delivery fee transactions) and uses shipping carrier APIs to track packages in transit. It also leverages OpenAI GPT models to enhance user experience (such as extracting product names from URLs and creating personalized avatars), thereby blending advanced AI capabilities into the platform’s offerings.
- **Robust Architecture:** Built on a modern Django 4.2 framework:contentReference[oaicite:0]{index=0}, the backend follows a modular design with a dedicated app for user and order management. It employs Django REST Framework for clean API design and includes comprehensive models to handle profiles, posts, comments, and likes for the community features. The use of PostgreSQL (with the pgVector extension for potential vector similarity searches) ensures the system can handle structured data and future AI-driven queries efficiently.

## Tech Stack

- **Framework & Language:** Python 3, Django 4.2:contentReference[oaicite:1]{index=1}, Django REST Framework.
- **Asynchronous & Real-Time:** Celery 5 + Redis (for task queue and scheduling), Django Channels (ASGI WebSocket support):contentReference[oaicite:2]{index=2}.
- **Database:** PostgreSQL (primary relational database, via psycopg2 driver:contentReference[oaicite:3]{index=3}) and pgVector (vector search capability).
- **Cloud & Integrations:** AWS S3 (for media storage of images), Stripe API (payments), FedEx/Shipping APIs (tracking), OpenAI API (GPT-4 and image generation).
- **Other Libraries:** django-celery-beat (periodic task scheduler), django-cors-headers (CORS handling for APIs), etc.

## Setup

This project requires **Python 3.x** and **PostgreSQL**. After cloning the repo, install dependencies with:

```bash
pip install -r requirements.txt

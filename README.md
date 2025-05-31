# Bidangil Backend

Bidangil Backend is the backend of a website. The website powers a cross-border e-commerce and community platform. It handles everything from user accounts and order requests to payment processing, shipping logistics, admin pannel, user order history, community posts, community comments and other contents. This backend provides RESTful APIs and real-time communication channels to support the Bidangil frontend, ensuring both users and admins can automate the entire proxy purchase process.

## Motivation & Challenges

The project was built to solve the complex process of international personal shopping and shipping at Korean e-commerce. Traditionally, Korea has a strict policy on buying products online. Purchasing at Korean e-commerce requires Korean credit card and phone number verifications, neither doesn't offer international shippings in most cases. **Bidangil** was motivated by the need to automate and simplify this workflow for users and administrators. Key challenges included orchestrating multi-step order fulfillment (from initial request to final delivery), integrating third-party services (for payments and shipping), and maintaining a responsive user experience for processes that are inherently asynchronous or lengthy (such as waiting for items to ship or generating custom user avatars with AI).
x
## Highlights

- **Custom Order Workflow in Django Admin:** The backend features a tailored Django admin interface to manage orders through their entire lifecycle. It uses inline models and custom admin actions to allow staff to view and update an order’s items, payment status, shipping details, and step-by-step progress all on one screen. This reduces the need for separate tools or manual tracking and ensures consistency in the fulfillment process.
- **Asynchronous Tasks & Real-Time Updates:** Heavy-lifting operations are offloaded to Celery task queues. For example, the system periodically checks shipment status (e.g., via FedEx API) in the background and updates orders automatically. It also generates user avatars using OpenAI’s image API in a worker task. Upon completion of these tasks, the backend uses Django Channels (WebSockets) to immediately notify the frontend – for instance, informing a user in real time when their AI-generated avatar is ready to use.
- **Third-Party Integrations:** Bidangil Backend seamlessly integrates with external services. It incorporates Stripe for secure payment processing (managing item purchases and delivery fee transactions) and uses shipping carrier APIs to track packages in transit. It also leverages OpenAI GPT models to enhance user experience (such as extracting product names from URLs and creating personalized avatars), thereby blending advanced AI capabilities into the platform’s offerings.
- **Robust Architecture:** Built on a modern Django 4.2 framework with Daphne, the backend follows a modular design with a dedicated app for user and order management. It employs Django REST Framework for clean API design and includes comprehensive models to handle profiles, posts, comments, and likes for the community features. The use of MySQL ensures the system can handle structured data.

## Tech Stack

- **Framework & Language:** Python 3.13.3, Django 5.2, Django REST Framework.
- **Asynchronous & Real-Time:** Celery 5.5.2 Redis (for task queue and scheduling), Django Channels (ASGI WebSocket support).
- **Database:** MySQL (primary relational database).
- **Cloud & Integrations:** AWS S3 (for media storage of images), Stripe API (payments), FedEx/Shipping APIs (tracking), OpenAI API (GPT-4o-search and GPT-image-1).
- **Other Libraries:** django-celery-beat (periodic task scheduler), django-cors-headers (CORS handling for APIs), etc.

## Setup

After cloning the repo, install dependencies with:

```bash
pip install -r requirements.txt

# Bidangil Backend

Bidangil Backend powers a cross-border e-commerce (between Korea and the U.S) and community platform.  
It handles everything from user accounts and order requests to payment processing, shipping logistics, admin workflows, order history, community posts, comments, and more.  
The backend uses REST APIs **and** real-time WebSocket channels so users and admins can automate the entire proxy-purchase process.

## Motivation & Challenges

### Cross-Border Purchasing
Buying from Korean e-commerce sites is tricky for non-residents: most stores require a Korean credit card, a local phone number, and rarely offer international shipping. **Bidangil** streamlines that experience by orchestrating the whole process.

| Lane | Steps |
|------|-------|
| **User**  | 1 Request quote → 2 Pay for items → 3 Pay delivery fee → 4 Receive tracking info → 5 Package delivered |
| **Admin** | 1 Approve quote (screen restricted items) → 2 Confirm item prices → 3 Confirm delivery fee → 4 Enter courier & tracking |

*Automation glue* — at each milestone a Django signal  
&nbsp;&nbsp;• creates/updates a **Stripe Checkout session**  
&nbsp;&nbsp;• fires SMS + email to the right party (e.g. “Payment received”, “Delivery fee ready”)  
&nbsp;&nbsp;• launches Celery jobs that **poll U.S. courier APIs** until the parcel is marked *delivered*.

### Community Module
While managing a pet shop I learned a simple truth: **the longer people linger, the more they spend**.  
My target users—Korean immigrants and K-culture fans—already share interests, so I embedded a lightweight social space as both a *playground* and a *soft funnel* back into purchases.

| Community Features | Why it matters |
|--------------------|----------------|
| **Location reveal** (state / county badges) | Sparks local meet-ups & offline trades. |
| **Avatar generator** (fun personality quiz → GPT image) | Adds “wow” factor & personal identity; increases return visits. |
| **Per-avatar & per-post likes** | Simple feedback loop; users can see who liked them. |
| **Merged Reviews page** | Store reviews live inside the community feed, exposing newcomers to social proof. |

#### Extra technical hurdles
| Challenge | Solution |
|-----------|----------|
| GPT image creation takes ~30sec (too long for a request thread) | Off-load to **Celery**; push the result over **WebSocket (Django Channels)** so the avatar pops in UI the moment it’s ready. |
| Deep reply chains (comment → reply → reply…) | Custom **recursive serializer** with pre-cached `replies_cache` list; loads N comments in **O(N)** with only two DB queries. |


These additions turn Bidangil into more than a checkout page—they create stickiness, community, and ultimately higher conversion.




## Highlights

* **Custom Django-admin workflow**  
  Inline models + a bespoke `save_formset` override let staff update item prices once and trigger a single Stripe session, preventing duplicate charges.
* **Asynchronous tasks & real-time push**  
  Celery handles heavy work (shipping polls, avatar generation); Django Channels pushes instant updates to the frontend when tasks finish.
* **API integrations**  
  Stripe (item & delivery payments), AWS S3 (boto 3), FedEx/EMS tracking APIs, and OpenAI (GPT-4o, image generation) are wired in behind clean service layers.
* **Robust architecture**  
  Built on Django 5.2 + Daphne (ASGI). DRF provides a clean API surface, and comprehensive models cover orders, profiles, posts, comments, and likes. MySQL backs persistent data.

## Tech Stack

| Layer | Tooling |
|-------|---------|
| **Language / Framework** | Python 3.13 · Django 5.2 · Django REST Framework |
| **Async & RT** | Celery 5.5 · Redis 7 (broker & channel layer) · Django Channels |
| **DB** | MySQL |
| **Cloud & Integrations** | AWS S3 · Stripe API · FedEx/EMS APIs · OpenAI GPT-4o-search / image-1 |
| **Utilities** | django-celery-beat |

## Quick Start

```bash
git clone https://github.com/your-org/bidangil_back.git
cd bidangil_back
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

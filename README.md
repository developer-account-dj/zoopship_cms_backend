
# zoopship_cms_backend

A Django + Django REST Framework backend for a lightweight CMS that manages **Pages**, **Sections**, and polymorphic **Section Items** (via `GenericForeignKey`) such as banners, blog posts, FAQs, etc.

This README focuses on what you already have in code and how to run, extend, and test it quickly.

---

## ✨ Features

- Pages ↔ Sections linkage with ordering via `PageSection`
- Polymorphic section items via `SectionItem (GenericForeignKey)`
- Create Sections with nested Items (supports `multipart/form-data` for images)
- Full nested validation **before** any DB write (atomic transactions)
- Filter Sections by page: `?page=<page-slug>`
- Retrieve a Section by slug, optionally constrained to page
- Rich serializer output:
  - `items` include a nested `content_object` resolved by `CONTENT_SERIALIZER_MAP`
  - `pages` shows all pages linked to a section

---

## 🧱 Core Models (simplified)

```py
class Section(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(blank=True, unique=True)
    is_active = models.BooleanField(default=True)

class SectionItem(BaseModel):
    section = models.ForeignKey(Section, related_name="items", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=50)
    content_object = GenericForeignKey("content_type", "object_id")

class PageSection(BaseModel):
    id = models.CharField(max_length=8, primary_key=True, editable=False, unique=True)
    page = models.ForeignKey(Page, related_name="page_sections", on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name="section_pages", on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

---

## 🔌 Endpoints (high level)

Base: `/api/content/`

- `GET  /sections/?page=<page-slug>` — list sections for a page (active only)
- `GET  /sections/<section-slug>/?page=<page-slug>` — retrieve a section (optionally constrained to page)
- `POST /sections/` — create a section with nested items and link to a page

> Admin: `/admin/` for managing content models directly.

---

## 📦 Example: Create a Section with Items (multipart)

Supports flat keys like `items[0][content_type]`, `items[0][title]`, etc — great for forms with files.

```bash
curl -X POST http://localhost:8000/api/content/sections/   -H "Authorization: Bearer <token>"   -H "Content-Type: multipart/form-data"   -F "title=Hero Section"   -F "page_slug=home"   -F "items[0][content_type]=banner"   -F "items[0][title]=Main Banner"   -F "items[0][heading]=Welcome to site!"   -F "items[0][subheading]=zoopship"   -F "items[0][image]=@/path/to/banner.webp"
```

If any item fails validation (e.g., missing required fields), the API returns `400` and **no Section is created**.

---

## 📄 Example: Response (retrieve)

```json
{
  "success": true,
  "message": "Section retrieved successfully",
  "data": {
    "id": "SECT7089",
    "title": "Hero Section",
    "slug": "hero-section",
    "is_active": true,
    "items": [
      {
        "id": "SEIT1234",
        "object_id": "BANN4851",
        "content_object": {
          "id": "BANN4851",
          "title": "Main Banner",
          "heading": "Welcome to site!",
          "image": "http://localhost:8000/media/..."
        }
      }
    ],
    "pages": [
      { "id": "PAGE1234", "title": "Home", "slug": "home" }
    ]
  }
}
```

---

## ⚙️ Serializer Highlights

**`SectionSerializer`**

- Validates all nested items **before** creating the `Section` (no orphan sections)
- Wraps all writes in `transaction.atomic()`
- Emits `pages` via a `SerializerMethodField`

**`SectionItemSerializer`**

- Uses `CONTENT_SERIALIZER_MAP` to route to the correct concrete serializer (e.g., `BannerSerializer`, `BlogPostSerializer`)
- Exposes a nested `content_object` for read operations

Make sure `CONTENT_SERIALIZER_MAP` includes all your item models:
```py
CONTENT_SERIALIZER_MAP = {
    "faq": FAQSerializer,
    "blogpost": BlogPostSerializer,
    "banner": BannerSerializer,
    "howitworks": HowItWorksSerializer,
    "impression": ImpressionSerializer,
    "feature": FeatureSerializer,
    "contactinfo": ContactInfoSerializer,
    "sliderbanner": SliderBannerSerializer,
}
```

---

## 🚀 Quickstart

1. **Clone & install**
   ```bash
   git clone <repo-url>
   cd zoopship_cms_backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment**
   Create `.env` with your settings (example):
   ```env
   DEBUG=True
   SECRET_KEY=change-me
   ALLOWED_HOSTS=*
   DATABASE_URL=sqlite:///db.sqlite3
   MEDIA_URL=/media/
   MEDIA_ROOT=./media
   ```

3. **Migrate & superuser**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Run**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

5. **Admin**
   Visit `http://localhost:8000/admin/`

---

## 🧪 Testing

```bash
pytest -q
# or Django's test runner
python manage.py test
```

---

## ✅ Common Gotchas

- **`Cannot resolve keyword 'pagesection'`**: use the correct reverse name: `section_pages__page__slug=...` (because `PageSection.section` has `related_name="section_pages"`).
- **Anonymous user on `BlogPost.author`**: ensure your `BlogPostSerializer.create()` sets `author` only if `request.user.is_authenticated` or mark it `read_only`.
- **`Page.DoesNotExist` on create**: return a 400 with a clear error (your serializer should catch this and raise `ValidationError({"page_slug": "Page with slug 'X' does not exist."})`).
- **Orphan `Section` after failed item**: use pre-validation + `transaction.atomic()` (already implemented).

---

## 🔧 Project Structure (suggested)

```
cms_backend/
  content/
    models.py
    serializers.py
    views.py
    urls.py
    admin.py
    utils.py        # e.g., parse_items_from_request
  cms_backend/
    settings.py
    urls.py
  manage.py
```

---

## 📥 Example JSON create (non-multipart)

```json
{
  "title": "Hero Section",
  "page_slug": "home",
  "items": [
    {
      "content_type": "banner",
      "title": "Main Banner",
      "heading": "Welcome!",
      "subheading": "zoopship"
    },
    {
      "content_type": "blogpost",
      "title": "Blog 1",
      "summary": "Short intro",
      "content": "Full content here"
    }
  ]
}
```

---

## 🛠 Extending

- Add new item type? Create its model + serializer and register it in `CONTENT_SERIALIZER_MAP`.
- Need multiple pages on create? Accept `page_slugs: [..]` and bulk-create `PageSection` rows after validating all pages exist.
- Need per-page item filtering? In `retrieve`, use the incoming `?page=` to optionally filter the `items` queryset.

---

## 📄 License

MIT (or your company policy).

---

Happy shipping! 🚀

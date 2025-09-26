# E-commerce API

A Django REST Framework-based **E-commerce API** that supports user
authentication, product and category management, and advanced query
features such as filtering, sorting, and pagination. Includes
comprehensive API documentation.

------------------------------------------------------------------------

## 🚀 Features

### 1. CRUD Operations

-   **Products**: Create, read, update, and delete products.
-   **Categories**: Manage product categories with full CRUD support.
-   **Users**: Authentication and user management using **JWT**.

### 2. API Features

-   **Filtering and Sorting**:
    -   Filter products by category.\
    -   Sort products by price and other attributes.
-   **Pagination**: Paginated responses for large product datasets
    (customizable).

### 3. API Documentation

-   Integrated **Swagger** (via drf-yasg) for interactive API docs.\
-   Can also be tested with **Postman** collection.

### 4. Security

-   JWT authentication for secure access.\
-   Follows best practices for sensitive data management.

------------------------------------------------------------------------

## 🛠️ Tech Stack

-   **Backend**: Django, Django REST Framework\
-   **Database**: PostgreSQL (or MySQL, configurable)\
-   **Authentication**: JWT (using `djangorestframework-simplejwt`)\
-   **Documentation**: Swagger (drf-yasg)

------------------------------------------------------------------------

## ⚡ Installation

1.  Clone the repository:

    ``` bash
    git clone https://github.com/your-username/ecommerce-api.git
    cd ecommerce-api
    ```

2.  Create and activate virtual environment:

    ``` bash
    python -m venv venv
    source venv/bin/activate   # On Linux/Mac
    venv\Scripts\activate    # On Windows
    ```

3.  Install dependencies:

    ``` bash
    pip install -r requirements.txt
    ```

4.  Configure environment variables in `.env`:

    ``` env
    DEBUG=True
    SECRET_KEY=your-secret-key
    DATABASE_URL=postgres://username:password@localhost:5432/ecommerce_db
    ```

5.  Run migrations:

    ``` bash
    python manage.py migrate
    ```

6.  Start server:

    ``` bash
    python manage.py runserver
    ```

------------------------------------------------------------------------

## 📑 Example API Usage

### Authentication (JWT)

``` http
POST /api/token/
{
  "username": "testuser",
  "password": "password123"
}
```

### Get Products with Filtering & Sorting

``` http
GET /api/products/?category=electronics&ordering=price
```

### Paginated Products

``` http
GET /api/products/?page=2&page_size=20
```

------------------------------------------------------------------------

## 📘 API Documentation

Once the server is running, visit:

    http://127.0.0.1:8000/swagger/

------------------------------------------------------------------------

## 📝 Git Commit Workflow

-   `feat: set up Django project with PostgreSQL`\
-   `feat: implement user authentication with JWT`\
-   `feat: add product APIs with filtering and pagination`\
-   `feat: integrate Swagger documentation for API endpoints`\
-   `perf: optimize database queries with indexing`\
-   `docs: add API usage instructions in Swagger`

------------------------------------------------------------------------

## 📂 Project Structure

    ecommerce-api/
    ├── products/          # Product and Category app
    ├── users/             # Authentication and User app
    ├── ecommerce/         # Project settings
    ├── requirements.txt
    ├── manage.py
    └── README.md

------------------------------------------------------------------------

## 📜 License

This project is licensed under the MIT License.
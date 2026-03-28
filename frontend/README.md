# Fashion AI Stylist Frontend

React + Vite frontend for Fashion AI Stylist application.

## Features

- ✅ User authentication (register/login/profile)
- ✅ Product catalog with filtering
- ✅ AI outfit generator interface
- ✅ Outfit history
- ✅ Admin panel (products/categories/users/stats)
- ✅ Responsive modern UI
- ✅ Full backend endpoint integration

## API Endpoints Integrated

### Authentication
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/profile`

### Products
- `GET /products/`
- `GET /products/{product_id}`

### Categories
- `GET /categories/`

### Outfits
- `POST /outfit/generate`
- `GET /outfit/history`

### Admin - Products
- `GET /admin/products/`
- `GET /admin/products/{product_id}`
- `POST /admin/products/`
- `PUT /admin/products/{product_id}`
- `DELETE /admin/products/{product_id}`
- `POST /admin/products/{product_id}/image`
- `PATCH /admin/products/{product_id}/stock`

### Admin - Categories
- `GET /admin/categories/`
- `GET /admin/categories/{category_id}`
- `POST /admin/categories/`
- `PUT /admin/categories/{category_id}`
- `DELETE /admin/categories/{category_id}`

### Admin - Users
- `GET /admin/users/`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}/role`
- `DELETE /admin/users/{user_id}`

### Admin - Stats
- `GET /admin/stats/`

### System
- `GET /health`

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
```

3. Start development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── Layout.jsx
│   ├── hooks/
│   │   └── index.js
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Auth.jsx
│   │   ├── Products.jsx
│   │   ├── Outfit.jsx
│   │   └── Admin.jsx
│   ├── services/
│   │   └── api.js
│   ├── styles/
│   │   ├── global.css
│   │   ├── layout.css
│   │   └── home.css
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── vite.config.js
└── package.json
```

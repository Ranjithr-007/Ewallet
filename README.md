# Ewallet - Backend (Django REST Framework + Docker)

A backend service for a Digital Wallet System built using Django REST Framework, fully containerized with Docker.
Supports wallet creation, add/spend money, transfers, transaction history, and financial reports.

## Features

- User registration (`/api/register/`)

- Wallet creation (`/api/login/`)

- Create New Wallet  (`/api/create-wallet/`)

- Add money to wallet (`/api/wallet/add/`)

- Spend money with insufficient balance protection (`/api/wallet/spend/`)

- Atomic wallet-to-wallet transfers (`/api/wallet/transfer/`)

- Immutable transaction logs (`/api/wallet/<str:wallet_id>/transactions/`)

- Wallet balance & summary APIs (`/api/wallet/<str:wallet_id>/summary/`)

- Monthly & yearly financial reports (`/api/wallet/<str:wallet_id>/monthly-report/<int:year>/`)

---

## Clone the Repository

```bash
git clone https://github.com/Ranjithr-007/Ewallet.git
cd WalletAPI
```

## Build Docker images

```bash
docker-compose build
```
## Run the containers

```bash
docker-compose up
```

## Apply migrations

```bash
docker-compose exec web python manage.py migrate
```


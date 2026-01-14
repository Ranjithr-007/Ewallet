import datetime
from django.db.models import Sum
from decimal import Decimal
from calendar import monthrange
from datetime import datetime, timedelta
from collections import OrderedDict
from django.db.models.functions import TruncMonth
from decimal import Decimal, InvalidOperation
from django.contrib.auth import authenticate, login
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from django.db import transaction
from app.models import User
from app.serializers import *


@api_view(('GET',))
@authentication_classes([BasicAuthentication])
def api_transaction_history(request):
    """
    get: Retrieves the transaction history in reverse
    chronological order
    """
    transactions = Transaction.objects.all()
    serializer = TransactionSerializer(transactions, many=True,
                                       context={'request': request})
    return Response(data=serializer.data)


@api_view(('POST',))
@authentication_classes([BasicAuthentication])
def api_fund_wallet(request):
    """
    post: Deposit funds into specified wallet.
    """
    data = JSONParser().parse(request)
    amount = Decimal(data['amount'])
    try:
        wallet_id = str(data['wallet_id'])
        wallet = Wallet.objects.get(id=wallet_id)
        wallet.deposit(amount)
        wallet.save()
        return Response(status=200, data={
            'success': f'Wallet with ID {wallet_id} was successfully funded with {amount}'})
    except Wallet.DoesNotExist:
        return Response(status=404,
                        data={'error': f'Wallet with matching ID not found'})


@api_view(('POST',))
@authentication_classes([BasicAuthentication])
def api_create_account(request):
    """
    post: Create user account with specified details.
    """
    data = JSONParser().parse(request)
    email = data['email']
    password = data['password']
    user = User.objects.create_user(email, password)
    user.save()
    return Response(status=201,
                    data={'success', 'Account created successfully!'})


@api_view(('POST',))
@authentication_classes([BasicAuthentication])
def api_login(request):
    """
    post: Log in user with specified details.
    """
    data = JSONParser().parse(request)
    email = data['email']
    password = data['password']
    user = authenticate(request, email=email, password=password)
    if user is not None:
        login(request, user)
        return Response(status=200,
                        data={'success', f'User {email} logged in.'})
    else:
        return Response(status=404,
                        data={'error', f'User {email} not found.'})


@api_view(('POST',))
@authentication_classes([BasicAuthentication])
def api_create_wallet(request):
    """
    post: Create a wallet with the given name and return the new wallet's ID.
    """
    data = JSONParser().parse(request)
    name = data['name']
    wallet_id = f'{int(datetime.datetime.utcnow().timestamp())}'
    wallet = Wallet.objects.create(name=name, id=wallet_id)
    wallet.save()
    return Response(status=201, data={'success': f'Wallet created ({name}). '
                                                 f'Wallet ID  is '
                                                 f'{wallet_id}.'})


@api_view(('POST',))
@authentication_classes([BasicAuthentication])
def api_transfer_funds(request):
    """
    post: Transfers funds from one wallet to the other and creates the
    related transaction logs.
    """
    data = JSONParser().parse(request)
    from_wallet_id = data['from_wallet']
    to_wallet_id = data['to_wallet']
    amount = Decimal(data['amount'])
    try:
        from_wallet = Wallet.objects.get(id=from_wallet_id)
        to_wallet = Wallet.objects.get(id=to_wallet_id)
        from_wallet.withdraw(amount)
        to_wallet.deposit(amount)
        from_wallet.save()
        to_wallet.save()
        return Response(status=200, data={'success': 'Transfer successful!'})
    except Wallet.DoesNotExist:
        return Response(status=404,
                        data={'error': f'Wallet with matching ID not found'})

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
def add_money(request):
    """
    post: Add money to wallet
    """
    try:
        data = JSONParser().parse(request)
        wallet_id = data.get('wallet_id')
        amount = Decimal(data.get('amount'))

        if amount <= 0:
            return Response(
                {"error": "Amount must be greater than zero"},
                status=400
            )

        wallet = Wallet.objects.get(id=wallet_id)
        wallet.deposit(amount)

        return Response(
            {
                "message": "Money added successfully",
                "wallet_id": wallet_id,
                "new_balance": str(wallet.balance)
            },
            status=200
        )

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)

    except (InvalidOperation, TypeError):
        return Response({"error": "Invalid amount"}, status=400)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
def spend_money(request):
    """
    post: Spend money from wallet
    """
    try:
        data = JSONParser().parse(request)
        wallet_id = data.get('wallet_id')
        amount = Decimal(data.get('amount'))

        if amount <= 0:
            return Response(
                {"error": "Amount must be greater than zero"},
                status=400
            )

        wallet = Wallet.objects.get(id=wallet_id)

      
        if wallet.balance < amount:
            return Response(
                {
                    "error": "Insufficient balance",
                    "current_balance": str(wallet.balance)
                },
                status=400
            )

        wallet.withdraw(amount)

        return Response(
            {
                "message": "Money spent successfully",
                "wallet_id": wallet_id,
                "remaining_balance": str(wallet.balance)
            },
            status=200
        )

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)

    except (InvalidOperation, TypeError):
        return Response({"error": "Invalid amount"}, status=400)

@api_view(['GET'])
@authentication_classes([BasicAuthentication])
def wallet_balance(request, wallet_id):
    """
    get: Retrieve wallet balance
    """
    try:
        wallet = Wallet.objects.get(id=wallet_id)
        return Response(
            {
                "wallet_id": wallet_id,
                "balance": str(wallet.balance)
            },
            status=200
        )
    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
def transfer_money(request):
    """
    post: Transfer money between wallets atomically
    """
    try:
        from_wallet_id = request.data.get('from_wallet')
        to_wallet_id = request.data.get('to_wallet')
        amount = Decimal(request.data.get('amount'))

        if amount <= 0:
            return Response(
                {"error": "Transfer amount must be greater than zero"},
                status=400
            )

        if from_wallet_id == to_wallet_id:
            return Response(
                {"error": "Cannot transfer to the same wallet"},
                status=400
            )

        with transaction.atomic():

            wallets = (
                Wallet.objects
                .select_for_update()
                .filter(id__in=[from_wallet_id, to_wallet_id])
            )

            if wallets.count() != 2:
                return Response(
                    {"error": "One or both wallets not found"},
                    status=404
                )

            from_wallet = next(w for w in wallets if w.id == from_wallet_id)
            to_wallet = next(w for w in wallets if w.id == to_wallet_id)

            if from_wallet.balance < amount:
                return Response(
                    {
                        "error": "Insufficient balance",
                        "current_balance": str(from_wallet.balance)
                    },
                    status=400
                )

            from_wallet.withdraw(amount)
            to_wallet.deposit(amount)

    
        return Response(
            {
                "message": "Transfer successful",
                "from_wallet": {
                    "id": from_wallet_id,
                    "available_balance": str(from_wallet.balance)
                },
                "to_wallet": {
                    "id": to_wallet_id,
                    "available_balance": str(to_wallet.balance)
                },
                "transferred_amount": str(amount)
            },
            status=200
        )

    except (InvalidOperation, TypeError):
        return Response({"error": "Invalid amount"}, status=400)


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
def wallet_transactions(request, wallet_id):
    """
    get: Show wallet transaction history and balance derivation
    """
    try:
        wallet = Wallet.objects.get(id=wallet_id)

        transactions = Transaction.objects.filter(wallet=wallet).order_by('created_at')

        deposits = transactions.filter(type='D').aggregate(
            total=Sum('value')
        )['total'] or 0

        withdrawals = transactions.filter(type='W').aggregate(
            total=Sum('value')
        )['total'] or 0

        derived_balance = deposits - withdrawals

        data = {
            "wallet_id": wallet_id,
            "derived_balance": str(derived_balance),
            "stored_balance": str(wallet.balance),
            "transactions": [
                {
                    "transaction_id": tx.id,
                    "type": "Deposit" if tx.type == "D" else "Withdraw",
                    "amount": str(tx.value),
                    "created_at": tx.created_at
                }
                for tx in transactions
            ]
        }

        return Response(data, status=200)

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
def add_money(request):
    """
    post: Add money to wallet (recorded as immutable transaction)
    """
    try:
        wallet_id = request.data.get('wallet_id')
        amount = Decimal(request.data.get('amount'))

        if amount <= 0:
            return Response({"error": "Amount must be greater than zero"}, status=400)

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(id=wallet_id)
            wallet.deposit(amount)

        return Response(
            {
                "message": "Deposit successful",
                "wallet_id": wallet_id,
                "new_balance": str(wallet.balance)
            },
            status=200
        )

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)

    except (InvalidOperation, TypeError):
        return Response({"error": "Invalid amount"}, status=400)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
def spend_money(request):
    """
    post: Spend money from wallet (recorded as immutable transaction)
    """
    try:
        wallet_id = request.data.get('wallet_id')
        amount = Decimal(request.data.get('amount'))

        if amount <= 0:
            return Response({"error": "Amount must be greater than zero"}, status=400)

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(id=wallet_id)

            if wallet.balance < amount:
                return Response(
                    {
                        "error": "Insufficient balance",
                        "current_balance": str(wallet.balance)
                    },
                    status=400
                )

            wallet.withdraw(amount)

        return Response(
            {
                "message": "Spend successful",
                "remaining_balance": str(wallet.balance)
            },
            status=200
        )

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)

    except (InvalidOperation, TypeError):
        return Response({"error": "Invalid amount"}, status=400)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
def transfer_money(request):
    """
    post: Atomic transfer with immutable transaction logs
    """
    try:
        from_wallet_id = request.data.get('from_wallet')
        to_wallet_id = request.data.get('to_wallet')
        amount = Decimal(request.data.get('amount'))

        if amount <= 0:
            return Response({"error": "Invalid amount"}, status=400)

        with transaction.atomic():
            wallets = (
                Wallet.objects
                .select_for_update()
                .filter(id__in=[from_wallet_id, to_wallet_id])
            )

            if wallets.count() != 2:
                return Response({"error": "Wallet not found"}, status=404)

            from_wallet = next(w for w in wallets if w.id == from_wallet_id)
            to_wallet = next(w for w in wallets if w.id == to_wallet_id)

            if from_wallet.balance < amount:
                return Response(
                    {"error": "Insufficient balance"},
                    status=400
                )

          
            from_wallet.withdraw(amount)
            to_wallet.deposit(amount)

      
        return Response(
            {
                "message": "Transfer successful",
                "transfer_details": {
                    "amount_transferred": str(amount),
                    "from_wallet": {
                        "id": from_wallet_id,
                        "remaining_balance": str(from_wallet.balance)
                    },
                    "to_wallet": {
                        "id": to_wallet_id,
                        "credited_amount": str(amount),
                        "available_balance": str(to_wallet.balance)
                    }
                }
            },
            status=200
        )

    except (InvalidOperation, TypeError):
        return Response({"error": "Invalid amount"}, status=400)

@api_view(['GET'])
@authentication_classes([BasicAuthentication])
def wallet_summary(request, wallet_id):
    """
    get: Return current balance, total money added, and total money spent
    """
    try:
        wallet = Wallet.objects.get(id=wallet_id)

        transactions = Transaction.objects.filter(wallet=wallet)

        total_added = transactions.filter(type='D').aggregate(total=Sum('value'))['total'] or Decimal('0.00')
        total_spent = transactions.filter(type='W').aggregate(total=Sum('value'))['total'] or Decimal('0.00')

        return Response({
            "wallet_id": wallet_id,
            "current_balance": str(wallet.balance),
            "total_added": str(total_added),
            "total_spent": str(total_spent)
        }, status=200)

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)

@api_view(['GET'])
@authentication_classes([BasicAuthentication])
def wallet_monthly_report(request, wallet_id, year: int):
    """
    get: Generate month-wise financial report for a wallet
    """
    try:
        wallet = Wallet.objects.get(id=wallet_id)

        # Get all transactions of this wallet for the year
        transactions = Transaction.objects.filter(
            wallet=wallet,
            created_at__year=year
        )

        # Aggregate deposits and withdrawals per month
        monthly_data = transactions.annotate(month=TruncMonth('created_at')) \
            .values('month', 'type') \
            .annotate(total=Sum('value')) \
            .order_by('month')

        # Initialize month-wise report dictionary (Jan → Dec)
        report = OrderedDict()
        for m in range(1, 13):
            report[m] = {
                "month": m,
                "month_name": datetime(year, m, 1).strftime("%B"),
                "opening_balance": Decimal('0.00'),
                "total_added": Decimal('0.00'),
                "total_spent": Decimal('0.00'),
                "closing_balance": Decimal('0.00')
            }

        # Fill month-wise totals from transaction aggregation
        for entry in monthly_data:
            month_number = entry['month'].month
            if entry['type'] == 'D':
                report[month_number]["total_added"] = entry['total'] or Decimal('0.00')
            elif entry['type'] == 'W':
                report[month_number]["total_spent"] = entry['total'] or Decimal('0.00')

        # Compute opening and closing balances
        # Opening balance for Jan = previous year balance (or 0)
        # We'll calculate previous balance by summing all transactions before this year
        prev_transactions = Transaction.objects.filter(
            wallet=wallet,
            created_at__lt=datetime(year, 1, 1)
        )

        prev_balance = (
            prev_transactions.filter(type='D').aggregate(total=Sum('value'))['total'] or Decimal('0.00')
        ) - (
            prev_transactions.filter(type='W').aggregate(total=Sum('value'))['total'] or Decimal('0.00')
        )

        # Fill balances month by month
        running_balance = prev_balance
        for m in range(1, 13):
            month_entry = report[m]
            month_entry["opening_balance"] = running_balance
            month_entry["closing_balance"] = running_balance + month_entry["total_added"] - month_entry["total_spent"]
            running_balance = month_entry["closing_balance"]

            # Convert all Decimals to string for JSON
            month_entry["opening_balance"] = str(month_entry["opening_balance"])
            month_entry["closing_balance"] = str(month_entry["closing_balance"])
            month_entry["total_added"] = str(month_entry["total_added"])
            month_entry["total_spent"] = str(month_entry["total_spent"])

        return Response({
            "wallet_id": wallet_id,
            "year": year,
            "monthly_report": list(report.values())
        }, status=200)

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"}, status=404)

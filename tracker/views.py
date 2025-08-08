from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import Transaction, BudgetGoal
from .forms import TransactionForm, BudgetGoalForm, RegisterForm
from datetime import date, datetime
from django.db.models.functions import TruncMonth

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'tracker/register.html', {'form': form})

@login_required(login_url='/login/') 
def dashboard(request):
    # Get current month's transactions
    today = date.today()
    transactions = Transaction.objects.filter(
        user=request.user,
        date__year=today.year,
        date__month=today.month
    )
    
    # Calculate totals
    total_income = transactions.filter(transaction_type='IN').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(transaction_type='EX').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses
    
    # Get budget goals
    budget_goals = BudgetGoal.objects.filter(
        user=request.user,
        month__year=today.year,
        month__month=today.month
    )
    
    # Check for exceeded budgets
    exceeded_budgets = []
    for goal in budget_goals:
        category_expenses = transactions.filter(
            transaction_type='EX',
            category=goal.category
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        if category_expenses > goal.amount:
            exceeded_budgets.append({
                'category': goal.get_category_display(),
                'budget': goal.amount,
                'spent': category_expenses,
                'over': category_expenses - goal.amount
            })
    
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'exceeded_budgets': exceeded_budgets,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'tracker/transaction_list.html', {'transactions': transactions})

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'tracker/transaction_form.html', {'form': form})

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'tracker/transaction_form.html', {'form': form})

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('transaction_list')
    return render(request, 'tracker/transaction_confirm_delete.html', {'transaction': transaction})

@login_required
def budget_goals(request):
    if request.method == 'POST':
        form = BudgetGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Budget goal set successfully!')
            return redirect('budget_goals')
    else:
        form = BudgetGoalForm()
    
    today = date.today()
    goals = BudgetGoal.objects.filter(
        user=request.user,
        month__year=today.year,
        month__month=today.month
    )
    
    return render(request, 'tracker/budget_goals.html', {'form': form, 'goals': goals})

@login_required
def reports(request):
    # Get all expense transactions grouped by category
    expenses_by_category = Transaction.objects.filter(
        user=request.user,
        transaction_type='EX'
    ).values('category').annotate(total=Sum('amount')).order_by('-total')
    
    # Fix for monthly spending - use TruncMonth for SQLite compatibility
    monthly_spending = Transaction.objects.filter(
        user=request.user,
        transaction_type='EX'
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total=Sum('amount')).order_by('month')
    
    return render(request, 'tracker/reports.html', {
        'expenses_by_category': expenses_by_category,
        'monthly_spending': monthly_spending,
    })
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.views.generic import CreateView, ListView, View
from .models import TransactionsModel
from .forms import DepositForm, WithdrawForm, LoanRequestForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_email_to_user(subject, user, amount, template):
    subject = subject
    message = render_to_string(template, {"user": user, "amount": amount})
    send_email = EmailMultiAlternatives(subject, message, to=[user.email])
    send_email.attach_alternative(message, "text/html")
    send_email.send()


# Create your views here.
class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    model = TransactionsModel
    success_url = reverse_lazy("home")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"account": self.request.user.account})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class DepositMoneyView(TransactionCreateMixin):
    template_name = "transactions/deposit_form.html"
    form_class = DepositForm

    def get_initial(self):
        initial = {"transaction_type": 1}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get("amount")
        account = self.request.user.account
        account.balance += amount
        account.save(update_fields=["balance"])

        messages.success(
            self.request, f"{amount}$ is deposited to your account successfully"
        )
        send_email_to_user(
            subject="Deposit Message",
            user=self.request.user,
            amount=amount,
            template="transactions/deposit_mail.html"
        )
        
        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    template_name = "transactions/withdraw_form.html"
    form_class = WithdrawForm

    def get_initial(self):
        initial = {"transaction_type": 2}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get("amount")
        account = self.request.user.account
        account.balance -= amount
        account.save(update_fields=["balance"])

        messages.success(self.request, f"{amount}$ withdrawn successfully")
        
        send_email_to_user(
            subject="Withdrawal Message",
            user=self.request.user,
            amount=amount,
            template="transactions/withdraw_mail.html"
        )
        
        return super().form_valid(form)


class LoanRequestView(TransactionCreateMixin):
    template_name = "transactions/loan_request_form.html"
    form_class = LoanRequestForm

    def get_initial(self):
        initial = {"transaction_type": 3}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get("amount")
        current_loan_count = TransactionsModel.objects.filter(
            account=self.request.user.account, transaction_type=3, loan_approve=True
        ).count()
        if current_loan_count >= 3:
            return HttpResponse("You Have crossed you loan limits")
        messages.success(self.request, f"Loan Request for {amount}$ successfully")
        
        send_email_to_user(
            subject="Loan Request Message",
            user=self.request.user,
            amount=amount,
            template="transactions/loan_request_mail.html"
        )
        
        return super().form_valid(form)


class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = "transactions/transaction_report.html"
    model = TransactionsModel

    def get_queryset(self):
        queryset = super().get_queryset().filter(account=self.request.user.account)

        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            queryset = queryset.filter(
                timestamps__date__gte=start_date, timestamps__date__lte=end_date
            )

            self.balance = TransactionsModel.objects.filter(
                timestamps__date__gte=start_date, timestamps__date__lte=end_date
            ).aggregate(Sum("amount"))

        else:
            self.balance = self.request.user.account.balance

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"amount": self.request.user.account})
        return context


class LoanListView(LoginRequiredMixin, ListView):
    model = TransactionsModel
    template_name = "transactions/loan_request_list.html"
    context_object_name = "loans"

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = TransactionsModel.objects.filter(
            account=user_account, transaction_type=3
        )
        return queryset


class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(TransactionsModel, id=loan_id)
        if loan.loan_approve:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transactions = user_account.balance
                user_account.save()
                loan.loan_approve = True
                loan.transaction_type = 4
                loan.save()
                return redirect("loan_list")
            else:
                messages.error(f"Loan amount is greater than account balance")
        return redirect("loan_list")

"""
Dashboard statistics endpoint for the admin panel.
GET /api/v1/admin/dashboard/stats/
"""
from datetime import date, timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.common.permissions import IsAdminUser, get_user_org_ids
from apps.payments.enums import PaymentStatus
from apps.payments.models import Payment
from apps.providers.models import ProviderProfile
from apps.users.enums import UserRoles
from apps.users.models import User


class DashboardStatsView(APIView):
    """
    Returns aggregate stats for the admin dashboard.
    Scoped by organization for org_admin / staff; global for super_admin / superuser.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        org_id = request.query_params.get("org_id")

        # ── Appointment queryset ──
        appt_qs = Appointment.objects.all()
        payment_qs = Payment.objects.all()
        provider_qs = ProviderProfile.objects.all()
        user_qs = User.objects.all()

        # ── Scope isolation ──
        allowed_orgs = get_user_org_ids(request.user)
        if allowed_orgs is not None:
            # Enforce that org_admin/staff can only query their own orgs
            if org_id:
                if str(org_id) not in [str(o) for o in allowed_orgs]:
                    org_id = None # Force it to show nothing or their own. Actually, let's just use allowed_orgs.
                    appt_qs = appt_qs.filter(organization_id__in=allowed_orgs)
                    payment_qs = payment_qs.filter(appointment__organization_id__in=allowed_orgs)
                    provider_qs = provider_qs.filter(organization_id__in=allowed_orgs)
                    user_qs = user_qs.filter(customer_appointments__organization_id__in=allowed_orgs).distinct()
                else:
                    appt_qs = appt_qs.filter(organization_id=org_id)
                    payment_qs = payment_qs.filter(appointment__organization_id=org_id)
                    provider_qs = provider_qs.filter(organization_id=org_id)
                    user_qs = user_qs.filter(customer_appointments__organization_id=org_id).distinct()
            else:
                appt_qs = appt_qs.filter(organization_id__in=allowed_orgs)
                payment_qs = payment_qs.filter(appointment__organization_id__in=allowed_orgs)
                provider_qs = provider_qs.filter(organization_id__in=allowed_orgs)
                user_qs = user_qs.filter(customer_appointments__organization_id__in=allowed_orgs).distinct()
        else:
            if org_id:
                appt_qs = appt_qs.filter(organization_id=org_id)
                payment_qs = payment_qs.filter(appointment__organization_id=org_id)
                provider_qs = provider_qs.filter(organization_id=org_id)
                user_qs = user_qs.filter(customer_appointments__organization_id=org_id).distinct()

        # ── Counts ──
        appointments_today = appt_qs.filter(
            start_at__gte=today_start, start_at__lt=today_end
        ).count()

        appointments_this_month = appt_qs.filter(start_at__gte=month_start).count()

        appointments_by_status = dict(
            appt_qs.values("status").annotate(count=Count("id")).values_list("status", "count")
        )

        # ── Revenue ──
        revenue_this_month = (
            payment_qs.filter(
                status=PaymentStatus.PAID, paid_at__gte=month_start
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        revenue_total = (
            payment_qs.filter(status=PaymentStatus.PAID).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        # ── Providers ──
        active_providers = provider_qs.filter(is_active=True).count()

        # ── New patients this month ──
        new_patients_this_month = user_qs.filter(
            role=UserRoles.CUSTOMER, created_at__gte=month_start
        ).count()

        total_users = user_qs.count()

        # ── Recent appointments (5) ──
        recent_appointments = list(
            appt_qs.select_related(
                "customer", "provider__user", "organization"
            )
            .order_by("-created_at")[:5]
            .values(
                "id",
                "status",
                "start_at",
                "customer__email",
                "customer__first_name",
                "customer__last_name",
                "provider__user__email",
                "provider__user__first_name",
                "provider__user__last_name",
                "organization__name",
            )
        )

        # ── Payment summary ──
        payment_summary = dict(
            payment_qs.values("status").annotate(count=Count("id")).values_list("status", "count")
        )

        return Response(
            {
                "appointments": {
                    "today": appointments_today,
                    "this_month": appointments_this_month,
                    "by_status": appointments_by_status,
                },
                "revenue": {
                    "this_month": float(revenue_this_month),
                    "total": float(revenue_total),
                },
                "providers": {
                    "active": active_providers,
                },
                "users": {
                    "total": total_users,
                    "new_patients_this_month": new_patients_this_month,
                },
                "recent_appointments": recent_appointments,
                "payments": {
                    "by_status": payment_summary,
                },
            }
        )

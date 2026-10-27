from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.appointments.enums import AppointmentStatus
from apps.appointments.models import Appointment
from apps.availability.models import Holiday, TimeOff, Weekday, WorkingHour
from apps.categories.models import Category
from apps.chat.enums import MessageType
from apps.chat.models import Conversation, Message
from apps.offerings.enums import VisitMode
from apps.offerings.models import Offering
from apps.organizations.models import Branch, Organization
from apps.payments.enums import PaymentMethod, PaymentStatus
from apps.payments.models import Payment
from apps.providers.models import ProviderProfile
from apps.users.enums import UserRoles
from apps.users.models import User


class Command(BaseCommand):
    help = "Seeds the database with sample data for testing appointments, slots, payments, and chat."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("⏳ در حال ساخت دیتای تستی..."))

        # ۱. تکمیل اطلاعات یوزرهای موجود شما یا ساخت آن‌ها در صورت نبودن
        users = self._seed_users()

        # ۲. ساخت تخصص‌ها (Categories)
        categories = self._seed_categories()

        # ۳. ساخت سازمان‌ها و شعب (Organizations & Branches)
        orgs, branches = self._seed_organizations_and_branches(users)

        # ۴. ساخت پروفایل پزشکان (ProviderProfiles)
        providers = self._seed_providers(users, orgs, branches, categories)

        # ۵. ساخت خدمات (Offerings: حضوری و چت آنلاین)
        offerings = self._seed_offerings(providers)

        # ۶. ساخت ساعات کاری تمام روزهای هفته، مرخصی و تعطیلات (Availability)
        self._seed_availability(providers, orgs)

        # ۷. ساخت نوبت‌های تستی (فعال برای چت، آینده، در انتظار تایید، تکمیل شده) + پرداخت و پیام‌های چت
        self._seed_appointments_payments_and_chat(users, providers, offerings)

        # پاک کردن کش ردیس برای به‌روزرسانی سریع اسلات‌ها و دسته‌بندی‌ها
        try:
            cache.clear()
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS("✅ دیتای تستی با موفقیت ساخته شد!"))
        self._print_summary(users, providers, offerings)

    def _seed_users(self):
        user_specs = [
            {
                "email": "admin@clinic.com",
                "first_name": "مدیر",
                "last_name": "کل سیستم",
                "phone_number": "09120000001",
                "role": UserRoles.SUPER_ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_verified": True,
            },
            {
                "email": "orgadmin@gmail.com",
                "first_name": "امیر",
                "last_name": "مدیری (ادمین کلینیک ۱)",
                "phone_number": "09120000002",
                "role": UserRoles.ORG_ADMIN,
                "is_verified": True,
            },
            {
                "email": "orgadmin2@gmail.com",
                "first_name": "سارا",
                "last_name": "کریمی (ادمین کلینیک ۲)",
                "phone_number": "09120000003",
                "role": UserRoles.ORG_ADMIN,
                "is_verified": True,
            },
            {
                "email": "provider@gmail.com",
                "first_name": "سعید",
                "last_name": "علوی",
                "phone_number": "09120000004",
                "role": UserRoles.PROVIDER,
                "is_verified": True,
            },
            {
                "email": "dr.rezaei@clinic.com",
                "first_name": "مریم",
                "last_name": "رضایی",
                "phone_number": "09120000005",
                "role": UserRoles.PROVIDER,
                "is_verified": True,
            },
            {
                "email": "customer@gmail.com",
                "first_name": "علی",
                "last_name": "احمدی",
                "phone_number": "09120000006",
                "role": UserRoles.CUSTOMER,
                "is_verified": True,
            },
            {
                "email": "a@gmail.com",
                "first_name": "test",
                "last_name": "testy",
                "phone_number": "333333333336",
                "role": UserRoles.CUSTOMER,
                "is_verified": True,
            },
            {
                "email": "test_api_agent10@example.com",
                "first_name": "Test",
                "last_name": "Agent",
                "phone_number": "09123456789",
                "role": UserRoles.CUSTOMER,
                "is_verified": True,
            },
        ]

        users = {}
        for spec in user_specs:
            email = spec["email"]
            user = User.objects.filter(email__iexact=email).first()
            if user:
                # فقط فیلدهایی که خالی هستند را پر می‌کنیم تا رمز عبور قبلی شما تغییر نکند
                updated = False
                if not user.first_name:
                    user.first_name = spec["first_name"]
                    updated = True
                if not user.last_name:
                    user.last_name = spec["last_name"]
                    updated = True
                if not user.phone_number:
                    user.phone_number = spec["phone_number"]
                    updated = True
                if not user.is_verified:
                    user.is_verified = True
                    updated = True
                if updated:
                    user.save()
            else:
                user = User.objects.create_user(
                    email=email,
                    password="aaaa0000",
                    first_name=spec["first_name"],
                    last_name=spec["last_name"],
                    phone_number=spec["phone_number"],
                    role=spec["role"],
                    is_staff=spec.get("is_staff", False),
                    is_superuser=spec.get("is_superuser", False),
                    is_verified=spec.get("is_verified", True),
                )
            users[email] = user

        return users

    def _seed_categories(self):
        cat_specs = [
            ("پزشکی عمومی", "general-medicine", "چکاپ کامل، سرماخوردگی و مشاوره پزشکی عمومی"),
            ("قلب و عروق", "cardiology", "بررسی نوار قلب، فشار خون و بیماری‌های قلبی"),
            ("پوست، مو و زیبایی", "dermatology", "درمان مشکلات پوستی، ریزش مو و مشاوره زیبایی"),
            ("روانپزشکی و سلامت روان", "psychiatry", "مشاوره آنلاین و حضوری اضطراب، افسردگی و خواب"),
            ("داخلی و گوارش", "internal-medicine", "بیماری‌های گوارشی، غدد، تیروئید و دیابت"),
        ]
        categories = {}
        for name, slug, desc in cat_specs:
            cat, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": desc,
                    "is_active": True,
                },
            )
            categories[slug] = cat
        return categories

    def _seed_organizations_and_branches(self, users):
        org1, _ = Organization.objects.update_or_create(
            slug="tehran-health-clinic",
            defaults={
                "owner": users["orgadmin@gmail.com"],
                "name": "کلینیک تخصصی سلامت تهران",
                "description": "مرکز جامع نوبت‌دهی حضوری و مشاوره آنلاین پزشکی",
                "phone_number": "02188776655",
                "email": "info@tehranclinic.com",
                "website": "https://tehranclinic.com",
                "timezone": "Asia/Tehran",
                "is_active": True,
            },
        )

        org2, _ = Organization.objects.update_or_create(
            slug="niavaran-medical-center",
            defaults={
                "owner": users["orgadmin2@gmail.com"],
                "name": "مرکز پزشکی نیاوران",
                "description": "کلینیک فوق تخصصی قلب و پوست",
                "phone_number": "02122334455",
                "email": "info@niavaranclinic.com",
                "website": "https://niavaranclinic.com",
                "timezone": "Asia/Tehran",
                "is_active": True,
            },
        )

        branch1, _ = Branch.objects.update_or_create(
            organization=org1,
            name="شعبه مرکزی (ونک)",
            defaults={
                "address": "تهران، میدان ونک، خیابان ملاصدرا، پلاک ۱۲۰",
                "phone_number": "02188776655",
                "latitude": Decimal("35.757500"),
                "longitude": Decimal("51.410000"),
                "is_active": True,
            },
        )

        branch2, _ = Branch.objects.update_or_create(
            organization=org1,
            name="شعبه غرب (شهرک غرب)",
            defaults={
                "address": "تهران، شهرک غرب، بلوار دادمان، پلاک ۴۵",
                "phone_number": "02188009988",
                "latitude": Decimal("35.758900"),
                "longitude": Decimal("51.362100"),
                "is_active": True,
            },
        )

        branch3, _ = Branch.objects.update_or_create(
            organization=org2,
            name="شعبه نیاوران",
            defaults={
                "address": "تهران، خیابان باهنر (نیاوران)، جنب پارک نیاوران",
                "phone_number": "02122334455",
                "latitude": Decimal("35.816500"),
                "longitude": Decimal("51.470500"),
                "is_active": True,
            },
        )

        return {"org1": org1, "org2": org2}, {"b1": branch1, "b2": branch2, "b3": branch3}

    def _seed_providers(self, users, orgs, branches, categories):
        # پزشک اصلی شما: provider@gmail.com
        p1, _ = ProviderProfile.objects.update_or_create(
            user=users["provider@gmail.com"],
            organization=orgs["org1"],
            defaults={
                "branch": branches["b1"],
                "title": "دکتر",
                "bio": "متخصص داخلی و قلب با بیش از ۱۰ سال سابقه طبابت و مشاوره آنلاین.",
                "default_slot_duration_minutes": 30,
                "is_active": True,
            },
        )
        p1.specialties.set([
            categories["general-medicine"],
            categories["cardiology"],
            categories["internal-medicine"],
        ])

        # پزشک دوم برای تست لیست‌ها و فیلتر تخصص‌ها
        p2, _ = ProviderProfile.objects.update_or_create(
            user=users["dr.rezaei@clinic.com"],
            organization=orgs["org1"],
            defaults={
                "branch": branches["b2"],
                "title": "دکتر",
                "bio": "متخصص پوست، مو و زیبایی و مشاور سلامت روان.",
                "default_slot_duration_minutes": 30,
                "is_active": True,
            },
        )
        p2.specialties.set([
            categories["dermatology"],
            categories["psychiatry"],
        ])

        return {"p1": p1, "p2": p2}

    def _seed_offerings(self, providers):
        p1 = providers["p1"]
        p2 = providers["p2"]

        # خدمات دکتر اول (provider@gmail.com)
        off1_in_person, _ = Offering.objects.update_or_create(
            provider=p1,
            title="ویزیت حضوری و چکاپ کامل",
            defaults={
                "organization": p1.organization,
                "description": "معاینه حضوری در مطب، بررسی فشار خون و تجویز نسخه",
                "visit_mode": VisitMode.IN_PERSON,
                "duration_minutes": 30,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 0,
                "price": Decimal("250000.00"),
                "requires_approval": False,
                "is_active": True,
            },
        )

        off1_online, _ = Offering.objects.update_or_create(
            provider=p1,
            title="مشاوره آنلاین متنی و بررسی آزمایش",
            defaults={
                "organization": p1.organization,
                "description": "گفتگوی مستقیم در اتاق چت با پزشک و ارسال تصویر آزمایش‌ها",
                "visit_mode": VisitMode.ONLINE_CHAT,
                "duration_minutes": 30,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 0,
                "price": Decimal("180000.00"),
                "requires_approval": False,
                "is_active": True,
            },
        )

        off1_approval, _ = Offering.objects.update_or_create(
            provider=p1,
            title="چکاپ تخصصی قلب (نیازمند تأیید پزشک)",
            defaults={
                "organization": p1.organization,
                "description": "نوبت پس از بررسی اولیه توسط پزشک تأیید نهایی می‌شود",
                "visit_mode": VisitMode.IN_PERSON,
                "duration_minutes": 45,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 15,
                "price": Decimal("450000.00"),
                "requires_approval": True,
                "is_active": True,
            },
        )

        # خدمات دکتر دوم (dr.rezaei@clinic.com)
        off2_in_person, _ = Offering.objects.update_or_create(
            provider=p2,
            title="ویزیت حضوری پوست و مو",
            defaults={
                "organization": p2.organization,
                "description": "بررسی تخصصی پوست و مو در کلینیک",
                "visit_mode": VisitMode.IN_PERSON,
                "duration_minutes": 30,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 0,
                "price": Decimal("300000.00"),
                "requires_approval": False,
                "is_active": True,
            },
        )

        off2_online, _ = Offering.objects.update_or_create(
            provider=p2,
            title="مشاوره آنلاین پوست و روان‌درمانی",
            defaults={
                "organization": p2.organization,
                "description": "ارسال عکس ضایعه پوستی یا مشاوره در چت آنلاین",
                "visit_mode": VisitMode.ONLINE_CHAT,
                "duration_minutes": 30,
                "buffer_before_minutes": 0,
                "buffer_after_minutes": 0,
                "price": Decimal("200000.00"),
                "requires_approval": False,
                "is_active": True,
            },
        )

        return {
            "p1_in_person": off1_in_person,
            "p1_online": off1_online,
            "p1_approval": off1_approval,
            "p2_in_person": off2_in_person,
            "p2_online": off2_online,
        }

    def _seed_availability(self, providers, orgs):
        # تعریف ساعات کاری برای تمام روزهای هفته (دوشنبه=0 تا یکشنبه=6) از ساعت 08:00 تا 22:00
        # تا در هر روزی که تست می‌کنید اسلات خالی وجود داشته باشد
        for provider in providers.values():
            for weekday in Weekday.values:
                WorkingHour.objects.update_or_create(
                    provider=provider,
                    weekday=weekday,
                    defaults={
                        "start_time": time(8, 0),
                        "end_time": time(22, 0),
                        "is_active": True,
                    },
                )

        # یک تعطیلی نمونه برای ۳۰ روز آینده (تا جلوی رزرو فردا و هفته جاری را نگیرد)
        future_holiday_date = date.today() + timedelta(days=30)
        Holiday.objects.update_or_create(
            organization=orgs["org1"],
            date=future_holiday_date,
            defaults={
                "title": "تعطیلی رسمی آزمایشی",
                "is_active": True,
            },
        )

    def _seed_appointments_payments_and_chat(self, users, providers, offerings):
        p1 = providers["p1"]
        customer1 = users["customer@gmail.com"]
        customer2 = users["a@gmail.com"]

        now = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
        current_tz = timezone.get_current_timezone()

        # ساخت یا دریافت مکالمه بین customer@gmail.com و provider@gmail.com
        conv1, _ = Conversation.objects.get_or_create(
            customer=customer1,
            provider=p1.user,
        )

        # ۱. نوبت آنلاین «در حال برگزاری همین الان» (برای تست فوری چت آنلاین توسط بیمار و پزشک!)
        active_start = now - timedelta(minutes=10)
        active_end = now + timedelta(minutes=50)
        appt_active_online, created = Appointment.objects.update_or_create(
            customer=customer1,
            provider=p1,
            notes="نوبت تست فعال آنلاین (برای تست اتاق چت)",
            defaults={
                "organization": p1.organization,
                "branch": p1.branch,
                "offering": offerings["p1_online"],
                "conversation": conv1,
                "visit_mode": VisitMode.ONLINE_CHAT,
                "start_at": active_start,
                "end_at": active_end,
                "blocked_start_at": active_start,
                "blocked_end_at": active_end,
                "status": AppointmentStatus.CONFIRMED,
                "price": offerings["p1_online"].price,
                "created_by": customer1,
            },
        )
        Payment.objects.update_or_create(
            appointment=appt_active_online,
            defaults={
                "amount": appt_active_online.price,
                "method": PaymentMethod.ONLINE,
                "status": PaymentStatus.PAID,
                "paid_at": now - timedelta(minutes=15),
                "gateway_reference": "mock-seed-active-online",
            },
        )

        # افزودن چند پیام تستی داخل چت اگر قبلاً پیامی نداشته است
        if not Message.objects.filter(conversation=conv1).exists():
            msg1 = Message.objects.create(
                conversation=conv1,
                sender=customer1,
                type=MessageType.TEXT,
                content="سلام آقای دکتر وقتتون بخیر، جواب آزمایشم رو آماده کردم.",
            )
            msg2 = Message.objects.create(
                conversation=conv1,
                sender=p1.user,
                type=MessageType.TEXT,
                content="سلام علیکم، وقت بخیر. لطفاً تصویر آزمایش و علائمتون رو بفرستید.",
            )
            conv1.last_message = msg2
            conv1.patient_last_read_message = msg1
            conv1.doctor_last_read_message = msg2
            conv1.save(
                update_fields=[
                    "last_message",
                    "patient_last_read_message",
                    "doctor_last_read_message",
                    "updated_at",
                ]
            )

        # ۲. نوبت حضوری تأیید شده برای فردا ساعت ۱۰:۰۰ صبح (برای تست لغو یا مشاهده جزئیات)
        tomorrow = now.date() + timedelta(days=1)
        tomorrow_10am = timezone.make_aware(datetime.combine(tomorrow, time(10, 0)), current_tz)
        tomorrow_1030am = tomorrow_10am + timedelta(minutes=30)

        appt_tomorrow, _ = Appointment.objects.update_or_create(
            customer=customer1,
            provider=p1,
            notes="نوبت حضوری فردا صبح",
            defaults={
                "organization": p1.organization,
                "branch": p1.branch,
                "offering": offerings["p1_in_person"],
                "visit_mode": VisitMode.IN_PERSON,
                "start_at": tomorrow_10am,
                "end_at": tomorrow_1030am,
                "blocked_start_at": tomorrow_10am,
                "blocked_end_at": tomorrow_1030am,
                "status": AppointmentStatus.CONFIRMED,
                "price": offerings["p1_in_person"].price,
                "created_by": customer1,
            },
        )
        Payment.objects.update_or_create(
            appointment=appt_tomorrow,
            defaults={
                "amount": appt_tomorrow.price,
                "method": PaymentMethod.IN_PERSON,
                "status": PaymentStatus.PENDING,
            },
        )

        # ۳. نوبت در وضعیت PENDING برای پس‌فردا ساعت ۱۱:۰۰ (برای تست دکمه «تأیید نوبت» توسط پزشک/ادمین)
        day_after = now.date() + timedelta(days=2)
        day_after_11am = timezone.make_aware(datetime.combine(day_after, time(11, 0)), current_tz)
        day_after_1145am = day_after_11am + timedelta(minutes=45)

        appt_pending, _ = Appointment.objects.update_or_create(
            customer=customer2,
            provider=p1,
            notes="نوبت در انتظار تأیید پزشک",
            defaults={
                "organization": p1.organization,
                "branch": p1.branch,
                "offering": offerings["p1_approval"],
                "visit_mode": VisitMode.IN_PERSON,
                "start_at": day_after_11am,
                "end_at": day_after_1145am,
                "blocked_start_at": day_after_11am,
                "blocked_end_at": day_after_1145am + timedelta(minutes=15),
                "status": AppointmentStatus.PENDING,
                "price": offerings["p1_approval"].price,
                "created_by": customer2,
            },
        )
        Payment.objects.update_or_create(
            appointment=appt_pending,
            defaults={
                "amount": appt_pending.price,
                "method": PaymentMethod.IN_PERSON,
                "status": PaymentStatus.PENDING,
            },
        )

        # ۴. نوبت تکمیل‌شده در گذشته (دیروز ساعت ۱۶:۰۰)
        yesterday = now.date() - timedelta(days=1)
        yesterday_4pm = timezone.make_aware(datetime.combine(yesterday, time(16, 0)), current_tz)
        yesterday_430pm = yesterday_4pm + timedelta(minutes=30)

        appt_completed, _ = Appointment.objects.update_or_create(
            customer=customer2,
            provider=p1,
            notes="نوبت تکمیل‌شده دیروز",
            defaults={
                "organization": p1.organization,
                "branch": p1.branch,
                "offering": offerings["p1_in_person"],
                "visit_mode": VisitMode.IN_PERSON,
                "start_at": yesterday_4pm,
                "end_at": yesterday_430pm,
                "blocked_start_at": yesterday_4pm,
                "blocked_end_at": yesterday_430pm,
                "status": AppointmentStatus.COMPLETED,
                "completed_at": yesterday_430pm,
                "price": offerings["p1_in_person"].price,
                "created_by": customer2,
            },
        )
        Payment.objects.update_or_create(
            appointment=appt_completed,
            defaults={
                "amount": appt_completed.price,
                "method": PaymentMethod.ONLINE,
                "status": PaymentStatus.PAID,
                "paid_at": yesterday_4pm - timedelta(hours=2),
                "gateway_reference": "mock-seed-completed",
            },
        )

    def _print_summary(self, users, providers, offerings):
        p1 = providers["p1"]
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📋 اطلاعات کلیدی برای تست API و اپلیکیشن:")
        self.stdout.write("=" * 60)
        self.stdout.write(f"👨‍⚕️ پزشک اصلی (provider@gmail.com):")
        self.stdout.write(f"   - Provider Profile ID : {p1.id}")
        self.stdout.write(f"   - خدمت حضوری (Offering): {offerings['p1_in_person'].id}")
        self.stdout.write(f"   - خدمت آنلاین (Offering): {offerings['p1_online'].id}")
        self.stdout.write("-" * 60)
        self.stdout.write("🧑‍💼 مشتریان آماده تست:")
        self.stdout.write("   - customer@gmail.com (دارای ۱ نوبت آنلاینِ در حال برگزاری با اتاق چت فعال + ۱ نوبت حضوری فردا)")
        self.stdout.write("   - a@gmail.com        (دارای ۱ نوبت در انتظار تأیید + ۱ نوبت تکمیل‌شده)")
        self.stdout.write("=" * 60 + "\n")
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from docx import Document
from django.urls import reverse

import io
from django.contrib.auth import authenticate, login, logout
from .forms import ApplicationForm, ScienceForm, GroupForm
from django.contrib import messages
from .models import Applications, Edutype, Sciences, Groups, Comissions, CustomUser, ExamResult   
from openpyxl import Workbook
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import calendar
from datetime import datetime
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.views import LoginView
import uuid
import requests
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

import json
import logging
import random
import string
# Log yozish uchun loggerni yaratish
logger = logging.getLogger(__name__)
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
# Create your views here.
# Login View


def LoginView(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home' if user.is_superuser else 'applications')
        else:
            return HttpResponse("Invalid login credentials", status=400)

    if request.GET.get("oneid_login"):
        # Avvalgi sessiyadagi state qiymatini tozalash
        if 'oauth_state' in request.session:
    	    del request.session['oauth_state']  # Avvalgi sessiya ma'lumotlarini o'chirish
    
        # Yangi state yaratish
        state = str(uuid.uuid4())
        request.session['oauth_state'] = state  # Yangi qiymatni sessiyaga saqlash

        query_params = urlencode({
            'client_id': settings.ONEID_CLIENT_ID,
            'response_type': 'one_code',
            'redirect_uri': settings.ONEID_REDIRECT_URI,
            'scope': 'nuu_uz',
            'state': state  # `state`ni URLga qo'shish
        })
        oneid_url = f"{settings.ONEID_AUTH_URL}?{query_params}"
        return redirect(oneid_url)

    return render(request, 'login.html')


def logout(request):
    logout(request)  # Foydalanuvchini tizimdan chiqaradi
    
    return redirect('login')



def generate_new_pin(length=6):
    """Yangi pin yaratish uchun funksiya."""
    return ''.join(random.choices(string.digits, k=length))


def callback(request):
    # URL'dan code va state qiymatini olish
    code = request.GET.get('code')
    if not code:
        return HttpResponse("Authorization code missing", status=400)

    # Token olish uchun OneID API'ga so'rov yuborish
    token_url = "https://sso.egov.uz/sso/oauth/Authorization.do"
    data = {
        'grant_type': 'one_authorization_code',
        'client_id': settings.ONEID_CLIENT_ID,
        'client_secret': settings.ONEID_CLIENT_SECRET,
        'code': code,
        'redirect_uri': settings.ONEID_REDIRECT_URI,
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return HttpResponse(f"Error fetching access token: {response.text}", status=400)

    token_data = response.json()
    access_token = token_data.get('access_token')
    
    if not access_token:
        return HttpResponse(f"Access token not found in response: {token_data}", status=400)

    # Foydalanuvchi haqida ma'lumot olish
    user_info_url = "https://sso.egov.uz/sso/oauth/Authorization.do"
    user_info_data = {
        'grant_type': 'one_access_token_identify',
        'client_id': settings.ONEID_CLIENT_ID,
        'client_secret': settings.ONEID_CLIENT_SECRET,
        'access_token': access_token,
        'scope': 'myportal',
    }

    user_info_response = requests.post(user_info_url, data=user_info_data)

    if user_info_response.status_code == 200:
        user_info = user_info_response.json()
        # OneID'dan username yo'q, lekin user_id va pin mavjud
        user_id = user_info.get('user_id', '')
        pin = user_info.get('pin', '')

        # Pin orqali username yaratish
        username = pin  # 'pin' ni username sifatida ishlatish

        # Agar foydalanuvchi tizimga kirayotgan bo'lsa, avvalgi pinni o'chirib, yangisini saqlash
        if pin:
            # Foydalanuvchi topilib, pinni yangilash
            user = CustomUser.objects.filter(pin=pin).first()
            if user:
                user.pin = generate_new_pin()  # Yangi pin yaratish yoki saqlash
                user.save()

        user, created = CustomUser.objects.update_or_create(
            username=username,  # Pin-ni username sifatida ishlatamiz
            defaults={
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('sur_name', ''),
                'mid_name': user_info.get('mid_name', ''),
                'pin': pin,
            }
        )

        if not created:  # Agar foydalanuvchi mavjud bo'lsa, ularni yangilash
            user.first_name = user_info.get('first_name', '')
            user.last_name = user_info.get('sur_name', '')
            user.mid_name = user_info.get('mid_name', '')

        user.oneid_login_time = timezone.now()  # Hozirgi vaqtni saqlash
        user.save()

        login(request, user)  # Foydalanuvchini tizimga kiriting

        # 'next' parametri mavjud bo'lsa, unga o'tish, bo'lmasa 'applications'ga yo'naltirish
        next_url = request.GET.get('next', reverse('applications', kwargs={'user': request.user.pin}))
        return redirect(next_url)
    else:
        return HttpResponse(f"Error fetching user info: {user_info_response.text}", status=400)




@login_required
def HomeView(request):
    status_counts = {}
    for status, _ in Applications.STATUS_CHOICES:
        status_counts[status] = Applications.objects.filter(status=status).count()

    context = {
        'status_counts': status_counts,
        'user': request.user,
    }

    return render(request, 'home.html', context,)

def SciencesView(request):
    status_counts = {}
    for status, _ in Applications.STATUS_CHOICES:
        status_counts[status] = Applications.objects.filter(status=status).count()

    selected_name = request.GET.get('name')  # Fan nomi
    selected_directions = request.GET.get('directions')  # Yo'nalish nomi

    # Barcha fanlarni olish
    sciences = Sciences.objects.order_by('-id')

    # POST so'rovi bilan kelgan ma'lumotni saqlash
    if request.method == 'POST':
        form = ScienceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('sciences')  # Fan ro'yxat sahifasiga qaytish
    else:
        form = ScienceForm()

    # Filtrlash
    if selected_name:
        sciences = sciences.filter(name__icontains=selected_name)
    if selected_directions:
        sciences = sciences.filter(directions__icontains=selected_directions)

    # Foydalanuvchi ko'rishi uchun mavjud nomlar va yo'nalishlar
    all_names = Sciences.objects.values_list('name', flat=True).distinct()
    all_directions = Groups.objects.all()


    context = {
        'sciences': sciences,
        'all_names': all_names,
        'all_directions': all_directions,
        'selected_name': selected_name,
        'selected_directions': selected_directions,
        'form': form,
        'status_counts': status_counts,
    }
    return render(request, 'sciences.html', context)



def GroupsView(request):
    status_counts = {}
    for status, _ in Applications.STATUS_CHOICES:
        status_counts[status] = Applications.objects.filter(status=status).count()
    # user = request.user  # Hozirgi foydalanuvchi

    # GET so'rovidan qiymatlarni olish
    selected_sciences = request.GET.get('sciences')
    selected_comission = request.GET.get('comission')

    groups = Groups.objects.order_by('-id')

    # POST so'rovi uchun forma bilan ishlash
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('groups')
    else:
        form = GroupForm()

    # Filtrlash
    if selected_sciences:
        groups = groups.filter(sciences__id=selected_sciences)
    if selected_comission:
        groups = groups.filter(comission__id=selected_comission)

    # Ma'lumotlar ro'yxatini olish
    all_sciences = Sciences.objects.all()
    all_comission = Comissions.objects.all()  # Comissions yozuvlari

    context = {
        'groups': groups,
        'all_sciences': all_sciences,
        'all_comission': all_comission,
        'selected_sciences': selected_sciences,
        'selected_comission': selected_comission,
        'form': form,
        'status_counts': status_counts,
    }

    return render(request, 'groups.html', context)


def export_excelgroup(request):
    # Excel faylini yaratish
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'datetime'

    # Ustun nomlarini yozish (header)
    sheet['A1'] = 'ID'
    sheet['B1'] = 'SANA'
    sheet['C1'] = 'FAN NOMI'

    # Ma'lumotlar bazasidan fanlarni olish
    groups = Groups.objects.all()  # Barcha fanlar

    # Agar fanlar mavjud bo'lsa
    if groups.exists():
        # Har bir fanlar uchun yangi satr qo'shish
        row = 2  # 1-chi qatorda ustun nomlari bor, shuning uchun 2-qatorni boshlaymiz
        for group in groups:
            # Har bir talabgor haqida ma'lumotlar
            sheet[f'A{row}'] = group.id
            sheet[f'B{row}'] = group.datetime
            sheet[f'C{row}'] = str(group.sciences)  # 'groups' o'rniga 'sciences'

            row += 1  # Har bir fan uchun yangi satr

    # Django response yaratish
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="science_datetime.xlsx"'

    # Excel faylini response ga saqlash
    workbook.save(response)

    return response


def admin_applicationfilter_user(request, user):
    # URL parametridan foydalanuvchi (pin) ma'lumotlarini olish
    user_instance = get_object_or_404(CustomUser, pin=user)
    
    # Foydalanuvchi uchun arizalar
    applications = Applications.objects.filter(user=user_instance).order_by('-created_at')

   
    # Tanlangan direction (ixtisoslik) bo'yicha fanlarni filtrlash
    direction_id = request.GET.get('direction_id')
    if direction_id:
        sciences = Sciences.objects.filter(directions_id=direction_id)
    else:
        sciences = Sciences.objects.all()

    science_list = [{'id': science.id, 'name': science.name} for science in sciences]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'sciences': science_list})

    type_edu = Edutype.objects.all()
    directions = Groups.objects.all()
    # POST so'rovini tekshirish
    if request.method == 'POST':
        # Foydalanuvchi ma'lumotlarini avtomatik olish
        first_name = request.POST.get('first_name', request.user.first_name)
        last_name = request.POST.get('last_name', request.user.last_name)
        mid_name = request.POST.get('mid_name', request.user.mid_name)
        
        directions_obj = get_object_or_404(Groups, id=request.POST.get("directions"))
        sciences_obj = get_object_or_404(Sciences, id=request.POST.get("sciences"))
        type_edu_obj = get_object_or_404(Edutype, id=request.POST.get("type_edu"))

        # Talabgor tomonidan tanlangan fandan ariza yuborilganligini tekshirish
        existing_application = Applications.objects.filter(
            user__id=request.user.id,
            sciences=sciences_obj
        ).exists()

        if existing_application:
            messages.error(request, "Siz ushbu fandan allaqachon ariza yuborgansiz!")
            return render(request, "applications.html", locals())

        application_file = request.FILES.get("applications")
        if application_file and application_file.size > 5 * 1024 * 1024:
            messages.error(request, "Ariza hajmi 5MB dan oshmasligi kerak!")
            return render(request, "applications.html", locals())

        organization_name = None
        if request.POST.get("chb_milliy") == "UZMU":
            organization_name = "UZMU"
        elif request.POST.get("chb_boshqa") == "other":
            organization_name = request.POST.get("organization_name")

        phone_number = request.POST.get("phone_number", "").replace(' ', '').replace('-', '').strip()
        
        # Obyekt yaratish
        Applications.objects.create(
            user=CustomUser.objects.get(id=request.user.id),
            first_name=first_name,
            last_name=last_name,
            mid_name=mid_name,
            directions=directions_obj,
            sciences=sciences_obj,
            type_edu=type_edu_obj,
            organization=organization_name,
            number=phone_number,
            oak_decision=request.FILES.get("oak_decision"),
            work_order=request.FILES.get("work_order"),
            reference_letter=request.FILES.get("reference_letter"),
            application=application_file,
        )

        messages.success(request, "Ariza muvaffaqiyatli yuborildi!")
        return redirect(reverse('applications', kwargs={'user': request.user.pin}))
   
    context = {
        'applications': applications,
        'sciences': science_list,
        'type_edu': type_edu,
        'directions': directions,
	'selected_direction_id': direction_id,  # Tanlangan direction ID'si
    }

    return render(request, 'applications.html', context)


# Admin uchun arizalarni filtrlash
@login_required
def admin_applicationfilter_admin(request):
    # Status bo'yicha statistik ma'lumotlarni yig'ish
    status_counts = {status: Applications.objects.filter(status=status).count() for status, _ in Applications.STATUS_CHOICES}

    selected_science = request.GET.get('science')  # Fan nomi
    selected_status = request.GET.get('status')  # Ariza holati

    if not request.user.is_authenticated:
        return redirect('login')  # Foydalanuvchini login sahifasiga yo'naltirish

    if request.user.is_staff:
        applications = Applications.objects.all().order_by('-created_at')
    else:
        applications = Applications.objects.filter(user=request.user).order_by('-created_at')

    # Tanlangan direction (ixtisoslik) bo'yicha fanlarni filtrlash
    direction_id = request.GET.get('direction_id')
    if direction_id:
        sciences = Sciences.objects.filter(directions_id=direction_id)
    else:
        sciences = Sciences.objects.all()

    science_list = [{'id': science.id, 'name': science.name} for science in sciences]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'sciences': science_list})

    type_edu = Edutype.objects.all()
    directions = Groups.objects.all()
    statuses = Applications.STATUS_CHOICES

    # Arizalarni filtrlash
    if selected_science:
        applications = applications.filter(sciences__id=selected_science)
    if selected_status:
        applications = applications.filter(status=selected_status)

    # POST so'rovini tekshirish
    if request.method == 'POST':
        # Foydalanuvchi ma'lumotlarini avtomatik olish
        first_name = request.POST.get('first_name', request.user.first_name)
        last_name = request.POST.get('last_name', request.user.last_name)
        mid_name = request.POST.get('mid_name', request.user.mid_name)
        
        directions_obj = get_object_or_404(Groups, id=request.POST.get("directions"))
        sciences_obj = get_object_or_404(Sciences, id=request.POST.get("sciences"))
        type_edu_obj = get_object_or_404(Edutype, id=request.POST.get("type_edu"))

        # Talabgor tomonidan tanlangan fandan ariza yuborilganligini tekshirish
        existing_application = Applications.objects.filter(
            user__id=request.user.id,
            sciences=sciences_obj
        ).exists()

        if existing_application:
            messages.error(request, "Siz ushbu fandan allaqachon ariza yuborgansiz!")
            return render(request, "applications.html", locals())

        application_file = request.FILES.get("applications")
        if application_file and application_file.size > 5 * 1024 * 1024:
            messages.error(request, "Ariza hajmi 5MB dan oshmasligi kerak!")
            return render(request, "applications.html", locals())

       	# Telefon raqamining to'g'ri kiritilganligini tekshirish
        phone_number = request.POST.get("phone_number", "").replace(' ', '').replace('-', '').strip()
	
        organization_name = None
        if request.POST.get("chb_milliy") == "UZMU":
            organization_name = "UZMU"
        elif request.POST.get("chb_boshqa") == "other":
            organization_name = request.POST.get("organization_name")
        

        # Obyekt yaratish
        Applications.objects.create(
            user=CustomUser.objects.get(id=request.user.id),
            first_name=first_name,
            last_name=last_name,
            mid_name=mid_name,
            directions=directions_obj,
            sciences=sciences_obj,
            type_edu=type_edu_obj,
            organization=organization_name,
            number=phone_number,
            oak_decision=request.FILES.get("oak_decision"),
            work_order=request.FILES.get("work_order"),
            reference_letter=request.FILES.get("reference_letter"),
            application=application_file,
        )

        messages.success(request, "Ariza muvaffaqiyatli yuborildi!")
        return redirect(reverse('admin_applications'))
        

    # Kontekst ma'lumotlar
    context = {
        'applications': applications,
        'sciences': science_list,
        'type_edu': type_edu,
        'directions': directions,
        'statuses': statuses,
        'selected_science': selected_science,
        'selected_status': selected_status,
        'status_counts': status_counts,
        'selected_direction_id': direction_id,  # Tanlangan direction ID'si
    }

    template_name = 'adminapplications.html' if request.user.is_staff else 'applications.html'
    return render(request, template_name, context)



def comissions_view(request):
    application = Applications.objects.all()
    # Groups modelidan barcha ma'lumotlarni olish
    applications = Applications.objects.select_related('directions',
                                                       'directions__comission').all()  # 'comission' bilan bog'langan Groups

    context = {
        'application': application,
        'applications': applications,  # Templatega o'tkaziladigan ma'lumotlar
    }

    return render(request, 'comissions.html', context)



def export_excel(request):
    # Excel faylini yaratish
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Applications'

    # Ustun nomlarini yozish (header)
    sheet['A1'] = 'ID'
    sheet['B1'] = 'FIO'
    sheet['C1'] = 'YO‘NALISH'
    sheet['D1'] = 'TASHKILOT'
    sheet['E1'] = 'FAN NOMI'
    sheet['F1'] = 'STATUS'

    # Ma'lumotlar bazasidan arizalarni olish
    applications = Applications.objects.all()  # Barcha arizalar

    # Agar arizalar mavjud bo'lsa
    if applications.exists():
        # Har bir ariza uchun yangi satr qo'shish
        row = 2  # 1-chi qatorda ustun nomlari bor, shuning uchun 2-qatorni boshlaymiz
        for application in applications:
            # Har bir talabgor haqida ma'lumotlar
            sheet[f'A{row}'] = application.id
            sheet[f'B{row}'] = f"{application.last_name} {application.first_name} {application.mid_name}"
            sheet[f'C{row}'] = str(application.directions)  # 'groups' o'rniga 'directions'
            sheet[f'D{row}'] = application.organization
            sheet[f'E{row}'] = str(application.sciences)  # `Sciences` obyektini stringga aylantirish
            sheet[f'F{row}'] = application.status

            row += 1  # Har bir talabgor uchun yangi satr

    # Django response yaratish
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="applications.xlsx"'

    # Excel faylini response ga saqlash
    workbook.save(response)

    return response


@csrf_exempt
def update_status(request, pk):
    if request.method == 'POST':
        application = get_object_or_404(Applications, pk=pk)
        status = request.POST.get('status')  # POST so'rovdan statusni olish

        if not status:
            return JsonResponse({'success': False, 'message': 'Status tanlanmagan!'}, status=400)

        reason = request.POST.get('reason', '')  # Rad etish sababi, agar mavjud bo'lsa
        application.status = status
        if status == 'rejected':
            application.reason = reason  # Rad etish sababi saqlanadi
        application.save()
        return JsonResponse({'success': True, 'status': application.status})
    return JsonResponse({'success': False}, status=405)

#word fayl

def ArchiveView(request):
    status_counts = {}
    for status, _ in Applications.STATUS_CHOICES:
        status_counts[status] = Applications.objects.filter(status=status).count()
    # user = request.user  # Hozirgi foydalanuvchi

    edutype = Edutype.objects.all()
    direction = Groups.objects.all()
    science = Sciences.objects.all()

    context = {
        "science": science,
        "edutype": edutype,
        "direction": direction,
        'status_counts': status_counts,
    }
    return render(request, 'archive.html', context)



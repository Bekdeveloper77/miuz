from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from docx import Document
from docx.shared import Inches
from django.urls import reverse, reverse_lazy
from datetime import datetime
from django.core.files.storage import FileSystemStorage
from PyPDF2 import PdfReader, PdfWriter, PdfFileWriter, PdfFileReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import qrcode
import io
from textwrap import wrap
#from weasyprint import HTML
import fitz  # PyMuPDF
from django.http import FileResponse
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse

from django.contrib import messages
from .models import Applications, Edutype, Sciences, Groups, Comissions, CustomUser, ExamResult,Curriculum
from .forms import ApplicationForm, ScienceForm, GroupForm, ComissionForm, ExamResultForm
from openpyxl import Workbook
from django.http import HttpResponse
import calendar
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.views import LoginView
import uuid
import requests
from urllib.parse import urlencode
from django.utils import timezone
from django.template.loader import render_to_string
import json
import logging
import random
import string
import textwrap
logger = logging.getLogger(__name__)
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.utils.timezone import now
from datetime import timedelta

def LoginView(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse_lazy('home' if user.is_superuser else 'applications'))
            #return redirect('home' if user.is_superuser else 'applications')
        else:
            return redirect("404.html", status=400)

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


def generate_new_username(length=20):
    """Yangi username yaratish uchun funksiya."""


def callback(request):
    code = request.GET.get('code')
    if not code:
        return HttpResponse("Authorization code missing", status=400)

    # Token olish uchun so'rov yuborish
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

    # Foydalanuvchi ma'lumotlarini olish
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

        user_id = user_info.get('user_id', None)
        if not user_id:
            return HttpResponse("User ID not found in the response", status=400)

        # user_id-ni username sifatida ishlatish
        username = user_id  # user_id ni username sifatida ishlatish

        # Foydalanuvchi tizimda mavjudmi?
        user, created = CustomUser.objects.update_or_create(
            username=username,
            defaults={
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('sur_name', ''),
                'mid_name': user_info.get('mid_name', ''),
            }
        )

        # Agar foydalanuvchi topilsa, uning ma'lumotlarini yangilash
        if not created:
            user.first_name = user_info.get('first_name', '')
            user.last_name = user_info.get('sur_name', '')
            user.mid_name = user_info.get('mid_name', '')
        
        user.save()

        # Foydalanuvchini tizimga kiritish
        login(request, user)

        # 'next' parametri bo'lsa, unga o'tish, aks holda 'applications'ga yo'naltirish
        next_url = request.GET.get('next', reverse('applications', kwargs={'user_id': user.username}))
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
    if selected_directions:  # Agar ixtisoslik tanlangan bo'lsa, faqat shu ixtisoslikka tegishli fanlarni ko'rsat
        sciences = sciences.filter(directions__id=selected_directions)

    if selected_name:
        sciences = sciences.filter(name__icontains=selected_name)

    # Foydalanuvchi ko'rishi uchun mavjud nomlar va yo'nalishlar
    all_names = Sciences.objects.values_list('name', flat=True).distinct()
    all_directions = Groups.objects.all()  # Yo'nalishlar (ixtisosliklar) ro'yxati

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



#def export_excelgroup(request):
#    # Excel faylini yaratish
#    workbook = Workbook()
#    sheet = workbook.active
#    sheet.title = 'datetime'
#
#    # Ustun nomlarini yozish (header)
#    sheet['A1'] = 'ID'
#    sheet['B1'] = 'SANA'
#    sheet['C1'] = 'FAN NOMI'
#
#    # Ma'lumotlar bazasidan fanlarni olish
#    groups = Groups.objects.all()  # Barcha fanlar
#
#    # Agar fanlar mavjud bo'lsa
#    if groups.exists():
#        # Har bir fanlar uchun yangi satr qo'shish
#        row = 2  # 1-chi qatorda ustun nomlari bor, shuning uchun 2-qatorni boshlaymiz
#        for group in groups:
#            # Har bir talabgor haqida ma'lumotlar
#            sheet[f'A{row}'] = group.id
#            sheet[f'B{row}'] = group.datetime
#            sheet[f'C{row}'] = str(group.sciences)  # 'groups' o'rniga 'sciences'
#
#            row += 1  # Har bir fan uchun yangi satr
#
#    # Django response yaratish
#    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#    response['Content-Disposition'] = 'attachment; filename="science_datetime.xlsx"'
#
#    # Excel faylini response ga saqlash
#    workbook.save(response)
#
#    return response

   

def admin_applicationfilter_user(request, user_id):
    # user_id orqali foydalanuvchini username bilan izlash
    user = get_object_or_404(CustomUser, username=user_id)

    applications = Applications.objects.filter(user=user).order_by('-created_at')
    results = ExamResult.objects.filter(application__in=applications)

     # Tanlangan direction_id (ixtisoslik) bo'yicha fanlarni filtrlash
    direction_id = request.GET.get('direction_id')  # direction_id ni olish
    sciences = Sciences.objects.all()  # Barcha fanlarni olish

    if direction_id:
        sciences = sciences.filter(directions_id=direction_id)  # direction_id bo'yicha filtrlash

    # Fanlar ro'yxatini JSON formatida yuborish
    science_list = [{'id': science.id, 'name': science.name} for science in sciences]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'sciences': science_list})

    type_edu = Edutype.objects.all()
    directions = Groups.objects.all()

    # POST so'rovini tekshirish
    if request.method == 'POST':
        first_name = request.POST.get('first_name', user.first_name)
        last_name = request.POST.get('last_name', user.last_name)
        mid_name = request.POST.get('mid_name', user.mid_name)
        
        directions_obj = get_object_or_404(Groups, id=request.POST.get("directions"))
        sciences_obj = get_object_or_404(Sciences, id=request.POST.get("sciences"))
        type_edu_obj = get_object_or_404(Edutype, id=request.POST.get("type_edu"))

        existing_application = Applications.objects.filter(
            user=user,
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
            user=user,
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
        return redirect(reverse('applications', kwargs={'user_id': user.username}))

    context = {
        'applications': applications,
        'sciences': science_list,
        'type_edu': type_edu,
        'directions': directions,
        'selected_direction_id': direction_id,  # Tanlangan direction ID'si
        'results': results,
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
    
    results = ExamResult.objects.filter(application__in=applications)

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
        # Avval checkboxlarni tekshirish
        if request.POST.get("chb_milliy") == "UZMU":
            phone_number = request.POST.get("phone_number1", "").replace(' ', '').replace('-', '').strip()
            organization_name = "UZMU"
        elif request.POST.get("chb_boshqa") == "other":
            phone_number = request.POST.get("phone_number", "").replace(' ', '').replace('-', '').strip()
            organization_name = request.POST.get("organization_name")
        else:
            phone_number = ""
            organization_name = None
        

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
	'results': results,
    }

    template_name = 'adminapplications.html' if request.user.is_staff else 'applications.html'
    return render(request, template_name, context)



def comissions(request):
    # Applications statuslarining sonini hisoblash
    status_counts = {}
    for status, _ in Applications.STATUS_CHOICES:
        status_counts[status] = Applications.objects.filter(status=status).count()

    selected_comission = request.GET.get('chairman')  # Filtrlangan komissiya

    # POST so'rovi bilan kelgan ma'lumotni saqlash
    if request.method == 'POST':
        form = ComissionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('comission')  # Fan ro'yxat sahifasiga qaytish
    else:
        form = ComissionForm()

    # Komissiyalarni olish
    all_comissions = Comissions.objects.all()

    # Filtrlash
    if selected_comission:
        comissions = Comissions.objects.filter(id=selected_comission)
    else:
        comissions = Comissions.objects.all()
    
    # Foydalanuvchi ko'rishi uchun mavjud nomlar va yo'nalishlar
    context = {
        'comissions': comissions,  # Filtrlangan komissiyalar
        'all_comissions': all_comissions,  # Barcha komissiyalar (filtrni ko'rsatish uchun)
        'selected_comission': selected_comission,
        'form': form,
        'status_counts': status_counts,
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
    sheet['C1'] = 'YOâ€˜NALISH'
    sheet['D1'] = 'TASHKILOT'
    sheet['E1'] = 'FAN NOMI'
    sheet['F1'] = 'STATUS'
    sheet['G1'] = 'TELEFON'

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
            sheet[f'G{row}'] = application.number

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
        if status == 'rejected' and reason:
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

    #edutype = Edutype.objects.all()
    #direction = Groups.objects.all()
    #science = Sciences.objects.all()

    #context = {
     #   "science": science,
      #  "edutype": edutype,
       # "direction": direction,
        #'status_counts': status_counts,
    #}
    #return render(request, 'archive.html', context)
    three_days_ago = now() - timedelta(days=3)
    archived_apps = Applications.objects.filter(created_at__lt=three_days_ago)  # 3 kundan eski arizalar
    return render(request, 'archive.html', {'applications': archived_apps, 'status_counts': status_counts})


import textwrap

def split_text(text, max_length=500):
    """Matnni maksimal uzunlikka qarab qatorlarga bo'lish"""
    return textwrap.wrap(text, width=max_length)

def insert_justified_text(page, x, y, text_parts, fontnames, fontsize=12, max_width=500):
    """Matnni ketma-ket, justify formatda joylashtirish, shriftlarni saqlagan holda"""
    y_position = y
    current_x = x
    font_cache = {}
    words_with_fonts = list(zip(text_parts, fontnames))  # Matn qismlari va ularning shriftlari

    line_words = []
    line_width = 0

    for word, fontname in words_with_fonts:
        if fontname not in font_cache:
            font_cache[fontname] = fitz.Font(fontname)

        word_width = font_cache[fontname].text_length(word + " ", fontsize)

        # Agar qo'shilsa, max_width oshib ketmasa, qatorga qo'shamiz
        if line_width + word_width <= max_width:
            line_words.append((word, fontname))
            line_width += word_width
        else:
            # Yangi qatorni joylashtirish
            y_position = distribute_words(page, current_x, y_position, line_words, font_cache, fontsize, max_width)
            line_words = [(word, fontname)]  # Yangi qatorni boshlash
            line_width = word_width

    # Oxirgi qatorni joylashtirish
    if line_words:
        y_position = distribute_words(page, current_x, y_position, line_words, font_cache, fontsize, max_width)

    return y_position

def distribute_words(page, x, y, words_with_fonts, font_cache, fontsize, max_width):
    """So'zlarni to'g'ri taqsimlab joylashtirish"""
    total_text_width = sum(font_cache[font].text_length(word, fontsize) for word, font in words_with_fonts)

    num_spaces = len(words_with_fonts) - 1
    if num_spaces > 0:
        space_width = (max_width - total_text_width) / num_spaces
    else:
        space_width = 0

    current_x = x

    # So'zlarni joylashtirish
    for word, fontname in words_with_fonts:
        page.insert_text((current_x, y), word, fontsize=fontsize, fontname=fontname, color=(0, 0, 0))
        current_x += font_cache[fontname].text_length(word, fontsize) + space_width

    y += fontsize + 2  # Keyingi qatorga o'tish

    return y  # Yangi y pozitsiyasini qaytarish


def format_date(date_obj):
    """Sanani O'zbekcha formatga o'zgartirish."""
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()  # Agar datetime bo'lsa, faqat sanasini olish
    
    formatted_date = date_obj.strftime("%Y-%m-%d")
    
    month_names = {
        "01": "yanvardagi", "02": "fevraldagi", "03": "mart", "04": "aprel", "05": "may", "06": "iyun",
        "07": "iyul", "08": "avgust", "09": "sentabr", "10": "oktabr", "11": "noyabr", "12": "dekabr"
    }

    year, month, day = formatted_date.split('-')
    month_name = month_names[month]
    formatted_date = f"{year}-yil {int(day)}-{month_name}"

    return formatted_date

def generate_certificate(request, result_id):
    try:
        exam_result = get_object_or_404(ExamResult, id=result_id)

        
        application = exam_result.application
        full_name = f"{application.last_name} {application.first_name} {application.mid_name}".upper()
        directions_text = str(application.directions)  # Ob'ektni stringga aylantirish
        edutype_text = str(application.type_edu)  # Shu qatorni o'zgartirdik
        exam_subject = str(application.sciences)  # Ob'ektni stringga aylantirish
        score = exam_result.score
        exam_date_table = exam_result.exam_date
        exam_date = format_date(exam_result.exam_date)


        doc = fitz.open("media/certificates/certificate.pdf")
        page = doc[0]

        
        # Komissiya a'zolarini olish
        commission = application.directions.comission
        chairman = commission.chairman
        deputy = commission.deputy
        secretary = commission.secretary
        members = commission.members
        members_list = members.split(";")
        members_text = ";\n".join([member.strip() for member in members_list[:-1]]) + ";\n" + members_list[-1].strip() + "."

        # QR kodni yaratish
        qr_buffer = io.BytesIO()
        qrcode.make(f"https://mi.nuu.uz/verify/{exam_result.id}/").save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        # PDF shablonini tayyorlash
        doc = fitz.open("media/certificates/certificate.pdf")
        page = doc[0]
	
        y_position = 225  # Boshlang'ich joylashuv

        text_parts = [
            full_name,             # BOLD
            directions_text,       # BOLD
            " ixtisosligi boyicha ",  # ODDIY
            edutype_text,         # BOLD
            " ilmiy darajasini olish uchun ",  # ODDIY
            exam_subject,         # BOLD
            " fanidan malakaviy imtihon topshirdi va quyidagi bahoni oldi: "  # ODDIY
        ]

        fontnames = [
            "times-bold", "times-bold", "times-roman",
            "times-bold", "times-roman", "times-bold", "times-roman"
        ]

        # Matnni joylashtirish
        y_position = insert_justified_text(page, 70, y_position, text_parts, fontnames)

        page.insert_text((80, 470), f"{exam_subject}", fontsize=12, color=(0, 0, 0), fontname="times-bold")
        page.insert_text((200, 470), f"{exam_date_table}", fontsize=12, color=(0, 0, 0), fontname="times-bold")  # Bu yerda o'zgartirish
        page.insert_text((300, 470), f"{exam_result.score} ball", fontsize=12, color=(0, 0, 0), fontname="times-bold")

        # Komissiya a'zolarini joylashtirish
        page.insert_text((355, 385), f"Komissiya raisi:", fontsize=12, color=(0, 0, 0), fontname="times-bold")
        page.insert_text((355, 420), f"Rais o'rinbosari:", fontsize=12, color=(0, 0, 0), fontname="times-bold")
        page.insert_text((355, 455), f"Komissiya kotibi:", fontsize=12, color=(0, 0, 0), fontname="times-bold")
        page.insert_text((355, 490), f"Komissiya a'zolari:", fontsize=12, color=(0, 0, 0), fontname="times-bold")

        # Komissiya a'zolarini PDFga kiritish
        page.insert_text((355, 400), f"{chairman}", fontsize=12, color=(0, 0, 0), fontname="times-roman")
        page.insert_text((355, 435), f"{deputy}", fontsize=12, color=(0, 0, 0), fontname="times-roman")
        page.insert_text((355, 470), f"{secretary}", fontsize=12, color=(0, 0, 0), fontname="times-roman")
        page.insert_text((355, 500), f"{members_text}", fontsize=12, color=(0, 0, 0), fontname="times-roman")

        page.insert_text((356, 620), f"{exam_date}", fontsize=12, color=(0, 0, 0), fontname="times-roman")
        page.insert_text((375, 670), f"{chairman}", fontsize=12, color=(0, 0, 0), fontname="times-bold")

        # QR kodni joylashtirish
        qr_img = fitz.Pixmap(qr_buffer.getvalue())
        page.insert_image(fitz.Rect(500, 670, 600, 770), pixmap=qr_img)

        # PDFni yaratish
        pdf_buffer = io.BytesIO()
        doc.save(pdf_buffer)
        pdf_buffer.seek(0)

        # Sertifikatni yuklash
        return FileResponse(pdf_buffer, as_attachment=True, filename=f"certificate_{exam_result.id}.pdf")

    except ExamResult.DoesNotExist:
        return HttpResponse("Imtihon natijasi topilmadi.", status=404)
    except Exception as e:
        return HttpResponse(f"Xatolik yuz berdi: {e}", status=500)



def verify_certificate(request, result_id):
    try:
        # ExamResult ni olish
        #exam_result = get_object_or_404(ExamResult, id=result_id)
        #application = exam_result.application
        exam_result = get_object_or_404(ExamResult, id=result_id)

        # Agar admin bo'lsa, faqat shu idga tegishli ExamResultni ko'rsatsin
        if request.user.is_staff and exam_result.application.user != request.user:
            return HttpResponse("Siz boshqa talabgorning sertifikatini ko'rishingiz mumkin emas.", status=403)

        application = exam_result.application
        # Talabgorning to'liq ismi
        full_name = f"{application.last_name} {application.first_name} {application.mid_name}".upper()

        # Komissiya a'zolari va boshqa ma'lumotlarni olish
        directions = application.directions
        commission = directions.comission

        chairman = commission.chairman
        deputy = commission.deputy
        secretary = commission.secretary
        members = commission.members

        # Komissiya a'zolarini ajratish
        members_list = members.split(";")  # Nuqta-vergul orqali ajratish
        if len(members_list) > 1:
            members_text = ";\n".join([member.strip() for member in members_list[:-1]])  # Oxirgi a'zodan oldingi a'zolarni ; bilan ajratish
            members_text += ";\n" + members_list[-1].strip() + "."  # Oxirgi a'zodan keyin nuqta qo'yish
        else:
            members_text = members_list[0].strip() + "."  # Faqat bitta a'zo bo'lsa, nuqta bilan tugaydi

        # Sertifikatni tasdiqlovchi ma'lumotlar
        context = {
            'full_name': full_name,
            'score': exam_result.score,
            'exam_subject': exam_result.exam_subject,
            'exam_date': exam_result.exam_date,
            'chairman': chairman,
            'deputy': deputy,
            'secretary': secretary,
            'members_text': members_text,
            'qr_code_url': f"https://mi.nuu.uz/verify/{exam_result.id}/"
        }

        # Sertifikatni tekshirish sahifasini render qilish
        return render(request, "verify_certificate.html", {
            "certificate_pdf_url": f"/media/certificates/certificate_{exam_result.id}.pdf",
            "context": context  # Send all necessary context data to the template
        })

    except ExamResult.DoesNotExist:
        raise Http404("Sertifikat topilmadi!")


@login_required
def curriculum_view(request):
    status_counts = {}
    for status, _ in Applications.STATUS_CHOICES:
        status_counts[status] = Applications.objects.filter(status=status).count()
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Sizda ushbu amalni bajarish huquqi yo'q!")
        return redirect("curriculum_view")

    if request.method == "POST":
        directions_name = request.POST.get("directions")
        direct_file = request.FILES.get("pdf")

        if directions_name and direct_file:
            curriculum = Curriculum(directions_name=directions_name, direct_file=direct_file)
            curriculum.save()
            messages.success(request, "Yangi ixtisoslik muvaffaqiyatli qo'shildi!")
        else:
            messages.error(request, "Ixtisoslik nomini va PDF faylini kiritish shart!")

        return redirect("curriculum_view")

    curriculums = Curriculum.objects.all()
    return render(request, "curriculums.html", {"curriculums": curriculums, "status_counts":status_counts})


def curriculum_user(request):
    curriculum_user = Curriculum.objects.all()
    return render(request, 'curriculm_user.html', {'curriculum_user': curriculum_user})




def save_exam_results(request, application_id):
    application = get_object_or_404(Applications, id=application_id)
    
    # Avval tekshiramiz: ushbu application uchun natija allaqachon kiritilganmi?
    if ExamResult.objects.filter(application=application).exists():
        messages.error(request, "Ushbu ariza uchun imtihon natijasi allaqachon kiritilgan!")
        return redirect('admin_applications')  # Natija kiritilgan bo‘lsa, qayta yo‘naltiramiz
    
    if request.method == 'POST':
        form = ExamResultForm(request.POST)
        if form.is_valid():
            exam_result = form.save(commit=False)
            exam_result.application = application
            exam_result.save()

            # Statusni "Baholangan" qilib o'zgartirish
            application.status = 'graded'
            application.save()

            messages.success(request, "Natija muvaffaqiyatli saqlandi!")
            return redirect('admin_applications')
    
    form = ExamResultForm()
    return render(request, 'adminapplications.html', {'form': form, 'application': application})


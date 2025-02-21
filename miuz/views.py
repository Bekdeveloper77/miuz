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
from weasyprint import HTML
import fitz  # PyMuPDF
from django.http import FileResponse
from django.contrib.auth import authenticate, login, logout
from .forms import ApplicationForm, ScienceForm, GroupForm
from django.contrib import messages
from .models import Applications, Edutype, Sciences, Groups, Comissions, CustomUser, ExamResult,Curriculum
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

from django.utils import timezone
from django.template.loader import render_to_string
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
            return redirect(reverse_lazy('home' if user.is_superuser else 'applications'))
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



def generate_new_birth_date(length=6):
    """Yangi birth_date yaratish uchun funksiya."""
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
        # OneID'dan username yo'q, lekin user_id va birth_date mavjud
        user_id = user_info.get('user_id', '')
        birth_date = user_info.get('birth_date', '')

        # Pin orqali username yaratish
        username = birth_date # 'pin' ni username sifatida ishlatish

        # Agar foydalanuvchi tizimga kirayotgan bo'lsa, avvalgi birth_date o'chirib, yangisini saqlash
        if birth_date:
            # Foydalanuvchi topilib, birth_date yangilash
            user = CustomUser.objects.filter(birth_date=birth_date).first()
            if user:
                user.birth_date = generate_new_birth_date()  # Yangi birth_date yaratish yoki saqlash
                user.save()

        user, created = CustomUser.objects.update_or_create(
            username=birth_date,  # Pin-ni username sifatida ishlatamiz
            defaults={
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('sur_name', ''),
                'mid_name': user_info.get('mid_name', ''),
                'birth_date': birth_date,
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
        next_url = request.GET.get('next', reverse('applications'))
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


def admin_applicationfilter_user(request):
    # URL parametridan foydalanuvchi (birth_date) ma'lumotlarini olish
    # Agar foydalanuvchi avtorizatsiya qilgan bo'lsa, u holda `request.user` dan foydalaning
    #birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
    #user_instance = get_object_or_404(CustomUser, birth_date=birth_date)
    
    # Foydalanuvchi uchun arizalar
    applications = Applications.objects.filter(user=request.user).order_by('-created_at')
    results = ExamResult.objects.filter(application__in=applications)
    
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
        return redirect(reverse('applications'))
   
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
	'results': results,
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


def split_text(text, max_length=80):
    """Matnni maksimal uzunlikka qarab ikkita qatorga bo'lib chiqarish"""
    return "\n".join(wrap(text, width=max_length))

def generate_certificate(request, result_id):
    try:
        exam_result = ExamResult.objects.get(id=result_id)
        application = exam_result.application

        

        full_name = f"{application.last_name} {application.first_name} {application.mid_name}".upper()
        sciences_text = str(exam_result.exam_subject)  # Faqat shu fanga mos
        wrapped_sciences = split_text(sciences_text)

        qr_buffer = io.BytesIO()
        qrcode.make(f"https://mi.nuu.uz/verify/{exam_result.id}/").save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        doc = fitz.open("media/certificates/certificate.pdf")
        page = doc[0]

        text_data = [
            ((200, 225), full_name, "times-bold"),
            ((200, 285), wrapped_sciences, "times-bold"),
            ((280, 490), f"{exam_result.score} ball", "times-bold"),
            ((80, 490), exam_result.exam_subject, "times-bold"),
            ((180, 490), str(exam_result.exam_date), "times-bold"),
        ]

        for (x, y), text, font in text_data:
            page.insert_text((x, y), text, fontsize=12, color=(0, 0, 0), fontname=font)

        qr_img = fitz.Pixmap(qr_buffer.getvalue())
        page.insert_image(fitz.Rect(450, 630, 550, 730), pixmap=qr_img)

        pdf_buffer = io.BytesIO()
        doc.save(pdf_buffer)
        pdf_buffer.seek(0)

        return FileResponse(pdf_buffer, as_attachment=True, filename=f"certificate_{exam_result.exam_subject}_{exam_result.id}.pdf")

    except ExamResult.DoesNotExist:
        return HttpResponse("Imtihon natijasi topilmadi.", status=404)
    except Exception as e:
        return HttpResponse(f"Xatolik yuz berdi: {e}", status=500)






def verify_certificate(request, result_id):
    try:
        # ExamResult ni olish
        exam_result = get_object_or_404(ExamResult, id=result_id)
        application = exam_result.application

        # Talabgorning to'liq ismi
        full_name = f"{application.last_name} {application.first_name} {application.mid_name}".upper()

        # Komissiya a'zolari va boshqa ma'lumotlarni olish
        chairman = application.directions.comission.chairman
        deputy = application.directions.comission.deputy
        secretary = application.directions.comission.secretary
        members = application.directions.comission.members

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

        return render(request, "verify_certificate.html", {
            "certificate_pdf_url": f"/media/certificates/certificate_{exam_result.id}.pdf",
        })

    except ExamResult.DoesNotExist:
        raise Http404("Sertifikat topilmadi!")


@login_required
def curriculum_view(request):
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
    return render(request, "curriculums.html", {"curriculums": curriculums})


def curriculum_user(request):
    curriculum_user = Curriculum.objects.all()
    return render(request, 'curriculm_user.html', {'curriculum_user': curriculum_user})


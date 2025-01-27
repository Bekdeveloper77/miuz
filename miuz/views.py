from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from docx import Document

import io
from django.contrib.auth import authenticate, login, logout
from .forms import ApplicationForm, ScienceForm, GroupForm
from django.contrib import messages
from .models import Applications, Edutype, Sciences, Groups, Comissions
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




# Create your views here.
# Login View


def LoginView(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return HttpResponse("Invalid login credentials", status=400)

    if request.GET.get("oneid_login"):
        # Avvalgi sessiyadagi state qiymatini tozalash
        if 'oauth_state' in request.session:
            del request.session['oauth_state']
    
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



def callback(request):
    # URL'dan code va state qiymatini olish
    code = request.GET.get('code')
    
    if not code:
        return HttpResponse("Authorization code missing", status=400)

    # Token olish uchun OneID API'ga so'rov yuborish
    token_url = "https://sso.egov.uz/sso/oauth/Authorization.do"  # Token olish URL
    data = {
        'grant_type': 'one_authorization_code',  # OAUTH grant_type
        'client_id': settings.ONEID_CLIENT_ID,  # Administrator tomonidan taqdim etilgan client_id
        'client_secret': settings.ONEID_CLIENT_SECRET,  # Administrator tomonidan taqdim etilgan client_secret
        'code': code,  # URL'dan olingan authorization code
        'redirect_uri': settings.ONEID_REDIRECT_URI,  # To'g'ri redirect_uri
    }

    # So'rov yuborish
    response = requests.post(token_url, data=data)

    # So'rov javobini tekshirish
    print("Response Status Code:", response.status_code)
    print("Response Text:", response.text)
    try:
        print("Response JSON:", response.json())  # Agar JSON shaklida javob kelsa
    except ValueError:
        pass  # Agar JSON formatida bo'lmasa

    if response.status_code != 200:
        return HttpResponse(f"Error fetching access token: {response.text}", status=400)

    # So'rov muvaffaqiyatli bo'lsa, access_token olish
    token_data = response.json()
    access_token = token_data.get('access_token')

    if not access_token:
        return HttpResponse(f"Access token not found in response: {token_data}", status=400)

    # Token bilan foydalanuvchi ma'lumotlarini olish
    user_info_url = "https://sso.egov.uz/sso/oauth/Authorization.do"  # Foydalanuvchi ma'lumotlarini olish URL
    user_info_data = {
        'grant_type': 'one_access_token_identify',  # Token orqali foydalanuvchi ma'lumotlarini olish
        'client_id': settings.ONEID_CLIENT_ID,  # Administrator tomonidan taqdim etilgan client_id
        'client_secret': settings.ONEID_CLIENT_SECRET,  # Administrator tomonidan taqdim etilgan client_secret
        'access_token': access_token,  # Olingan access_token
        'scope': 'myportal',  # Administrator tomonidan taqdim etilgan scope
    }

   # Foydalanuvchi ma'lumotlarini olish uchun so'rov yuborish
    user_info_response = requests.post(user_info_url, data=user_info_data)

    if user_info_response.status_code == 200:
        # JSON formatda qaytgan barcha ma'lumotlarni chop etish
        print("OneID javobi:", user_info_response.json())
    
        # Foydalanuvchi ma'lumotlarini olish
        user_info = user_info_response.json()
    
        # Bu yerda o'zgarishlar qilishingiz mumkin
        user, created = User.objects.get_or_create(
            username=user_info['user_id'], 
            defaults={
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('sur_name', ''),
                'full_name': user_info.get('full_name', ''),  # Agar email mavjud bo'lsa, saqlanadi
            }
        )

        if created:
            message = "Foydalanuvchi yaratildi."
        else:
            message = "Foydalanuvchi avvaldan mavjud."

        # Javob qaytarish
        return JsonResponse({
            "status": "success",
            "message": message,
            "user": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
            }
        })

        # Foydalanuvchini tizimga kiritish
        login(request, user)
        next_url = request.GET.get('next', 'applications')
        return redirect(next_url)
    else:
        print("Error fetching user info:", user_info_response.text)
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


def admin_applicationfilter(request):
    # Status bo'yicha statistik ma'lumotlarni yig'ish
    status_counts = {status: Applications.objects.filter(status=status).count() for status, _ in Applications.STATUS_CHOICES}

    selected_science = request.GET.get('science')  # Fan nomi
    selected_status = request.GET.get('status')  # Ariza holati

    # Hamma kerakli ma'lumotlarni olish
    if request.user.is_staff:
        applications = Applications.objects.all()
    else:
        applications = Applications.objects.filter(user=request.user)

    applications = applications.order_by('-created_at')

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
        full_name = request.POST.get('full_name', request.user.full_name)
        directions_obj = get_object_or_404(Groups, id=request.POST.get("directions"))
        sciences_obj = get_object_or_404(Sciences, id=request.POST.get("sciences"))
        type_edu_obj = get_object_or_404(Edutype, id=request.POST.get("type_edu"))
        # Talabgor tomonidan tanlangan fandan ariza yuborilganligini tekshirish
        existing_application = Applications.objects.filter(
            user=request.user,
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
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            directions=directions_obj,
            sciences=sciences_obj,
            type_edu=type_edu_obj,
            organization=organization_name,
            number=phone_number,
            oak_decision=request.FILES.get("oak_decision"),
            work_order=request.FILES.get("work_order"),
            reference_letter=request.FILES.get("reference_letter"),
            application=application_file,
            user=request.user
        )
        messages.success(request, "Ariza muvaffaqiyatli yuborildi!")
        return redirect(reverse('applications', kwargs={'user': request.user.username}))

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
    return render(request, template_name, context,)



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


#def applications(request):
#    return render(request, 'applications.html')  # applications sahifasi shabloni

# def ApplicationsView(request):
#     applications = Applications.objects.filter(user=request.user)  # Faqat foydalanuvchining arizalari
#     # Baza ma'lumotlarini olish
#     type_edu = Edutype.objects.all()
#     directions = Groups.objects.all()  # Bu yerda 'directions' ro'yxat bo'lishi kerak
#     sciences = Sciences.objects.all()
#
#     # Formani yuborish uchun POST so'rovi
#     if request.method == "POST":
#         try:
#             # Formaga yuborilgan ma'lumotlarni olish
#             directions = get_object_or_404(Groups, id=request.POST.get("directions"))
#             sciences = get_object_or_404(Sciences, id=request.POST.get("sciences"))
#             type_edu = get_object_or_404(Edutype, id=request.POST.get("type_edu"))
#
#             # Fayl hajmini tekshirish
#             application_file = request.FILES.get("application")
#             if application_file and application_file.size > 5 * 1024 * 1024:
#                 messages.error(request, "Ariza hajmi 5MB dan oshmasligi kerak!")
#                 return render(request, "applications.html", context)
#
#             if request.POST.get("chb_milliy") == "UZMU":
#                 organization_name = "UZMU"
#             elif request.POST.get("chb_boshqa") == "other":
#                 organization_name = request.POST.get(
#                     "organization_name")  # Boshqa tashkilot nomini input orqali olingan
#             else:
#                 organization_name = None
#
#             # Tashkilot tanlanganini aniqlash
#             if "chb_milliy" in request.POST:
#                 phone_number = request.POST.get("phone_number", "")  # Milliy uchun raqam
#                 # Belgilarni tozalash
#                 cleaned_phone = phone_number.replace('-', '').strip()
#                 return HttpResponse(f"Telefon raqamingiz: {cleaned_phone}")
#
#             elif "chb_boshqa" in request.POST:
#                 phone_number = request.POST.get("number_boshqa", "")  # Boshqa tashkilot uchun raqam
#             else:
#                 phone_number = None  # Agar hech narsa tanlanmasa
#
#             # Ma'lumotlarni bazaga qo'shish
#             Applications.objects.create(
#                 first_name=request.POST.get("first_name"),
#                 last_name=request.POST.get("last_name"),
#                 father_name=request.POST.get("father_name"),
#                 directions=directions,
#                 sciences=sciences,
#                 type_edu=type_edu,
#                 organization=organization_name,  # To'g'irlangan qism,
#                 number=phone_number,
#                 oak_decision=request.FILES.get("oak_decision"),
#                 work_order=request.FILES.get("work_order"),
#                 reference_letter=request.FILES.get("reference_letter"),
#                 application=application_file
#             )
#
#             # Muvaffaqiyatli saqlanganini bildirish
#             messages.success(request, "Ariza muvaffaqiyatli yuborildi!")
#         except Exception as e:
#             # Xatolik yuz berganda
#             messages.error(request, f"Ariza yuborishda xatolik yuz berdi: {str(e)}")
#
#     context = {
#         'applications': applications,
#         'sciences': sciences,
#         'type_edu': type_edu,
#         'directions': directions,  # Bu yerda 'directions' ro'yxat sifatida olingan
#     }
#
#     return render(request, 'applications.html', context)


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
            sheet[f'B{row}'] = f"{application.last_name} {application.first_name} {application.father_name}"
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
def generate_certificate(application):
    doc = Document()

    # Ballga qarab xabarni tayyorlash
    if application.score >= 56:
        result_message = "imtihonni muvofaqqiyatli topshiridingiz."
    elif application.score > 0:
        result_message = "imtihonni muvofaqqiyatli topshira olmadingiz."
    else:
        result_message = "imtihonga qatnashmagansiz."

    # Word faylga ma'lumot qo'shish
    doc.add_heading(f"Hurmatli {application.first_name} {application.last_name} {application.father_name}", level=1)
    doc.add_paragraph(f"Siz {application.sciences} fanidan {application.score} ball to'pladingiz.")
    doc.add_paragraph(f"Natija: {result_message}")

    # Faylni saqlash
    file_name = f"{application.first_name}_{application.last_name}_natija.docx"
    doc.save(file_name)
    return file_name

def download_certificate(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    file_path = generate_certificate(application)
    response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{file_path}"'
    return response\

def application_review(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    if request.method == "POST":
        application.score = request.POST.get('score')
        application.save()
        return redirect('download_certificate', application_id=application.id)
    return render(request, 'adminapplications.html', {'application': application})

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

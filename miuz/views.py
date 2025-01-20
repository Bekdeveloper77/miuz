from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

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

import requests

# Create your views here.

@login_required
def LoginRedirectView(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_superuser:  # Agar foydalanuvchi admin bo'lsa
        return redirect('account')  # Admin sahifasiga yo'naltirish
    else:  # Oddiy foydalanuvchi bo'lsa
        return redirect('applications')  # Foydalanuvchi sahifasiga yo'naltirish

@login_required
def HomeView(request):
    status_counts = {}
    for status, _ in Applications.STATUS_CHOICES:
        status_counts[status] = Applications.objects.filter(status=status).count()
    # user = request.user  # Hozirgi foydalanuvchi
    context = {
        'status_counts': status_counts,
        'user': request.user,
    }

    return render(request, 'home.html', context)

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
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            father_name=request.POST.get("father_name"),
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
        return redirect('applications', {'user': request.user})

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
    return render(request, template_name, context, {'user': request.user})



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


# def application_create_view(request):
#
#
#     # Shablonni qaytarish
#     return render(request, "adminapplications.html", context)


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

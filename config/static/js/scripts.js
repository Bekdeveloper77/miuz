/*!
    * Start Bootstrap - SB Admin v7.0.7 (https://startbootstrap.com/template/sb-admin)
    * Copyright 2013-2023 Start Bootstrap
    * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-sb-admin/blob/master/LICENSE)
    */
    // 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

});


//add new
document.getElementById('export-excel').addEventListener('click', function() {
     // AJAX orqali serverga so'rov yuborish
     fetch('/export_excel/', {
         method: 'GET',
     })
     .then(response => response.blob())
     .then(blob => {
         // Excel faylini olish va foydalanuvchiga ko'rsatish
         const link = document.createElement('a');
         link.href = window.URL.createObjectURL(blob);
         link.download = 'applications.xlsx';  // Fayl nomi
         link.click();
     })
     .catch(error => console.error('Error exporting to Excel:', error));
});

$(document).ready(function() {
        $('#myTable').DataTable();
});

 // Example starter JavaScript for disabling form submissions if there are invalid fields
(function() {
  'use strict';
  window.addEventListener('load', function() {
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.getElementsByClassName('needs-validation');
    // Loop over them and prevent submission
    var validation = Array.prototype.filter.call(forms, function(form) {
      form.addEventListener('submit', function(event) {
        if (form.checkValidity() === false) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    });
  }, false);
})();

 let timeout = 10 * 60 * 1000; // 10 daqiqa
setTimeout(() => {
    alert("Sizning seansingiz tugadi. Iltimos, qayta tizimga kiring.");
    window.location.href = "/login/"; // Login sahifasiga yo'naltirish
}, timeout);

document.getElementById('openModalBtn').addEventListener('click', function () {
    const modal = new bootstrap.Modal(document.getElementById('exampleModal'));
    modal.show();
});
document.getElementById('openModalBtn1').addEventListener('click', function () {
    const modal = new bootstrap.Modal(document.getElementById('filterModal'));
    modal.show();
});
document.getElementById('openModalBtn2').addEventListener('click', function () {
    const modal = new bootstrap.Modal(document.getElementById('crud_modal'));
    modal.show();
});


function toggleCollapse(section) {
        // Collapse elementlarni olish
    const milliyCheckbox = document.querySelector('input[name="chb_milliy"]');
    const boshqaCheckbox = document.querySelector('input[name="chb_boshqa"]');
    const milliyCollapse = document.getElementById('milliy_collapse');
    const boshqaCollapse = document.getElementById('boshqa_collapse');

        // Collapse bo'limlarni boshqarish va checkboxlarni nazorat qilish
    if (section === 'milliy') {
        if (milliyCheckbox.checked) {
             milliyCollapse.style.display = 'block';
             boshqaCollapse.style.display = 'none';
             boshqaCheckbox.checked = false; // Ikkinchi checkboxni o'chirish
        } else {
             milliyCollapse.style.display = 'none';
        }
    } else if (section === 'boshqa') {
         if (boshqaCheckbox.checked) {
             boshqaCollapse.style.display = 'block';
             milliyCollapse.style.display = 'none';
             milliyCheckbox.checked = false; // Birinchi checkboxni o'chirish
         } else {
             boshqaCollapse.style.display = 'none';
         }
    }
}
function toggleCollapse(section) {
        // Collapse elementlarni olish
    const milliyCheckbox = document.querySelector('input[name="chb_milliy"]');
    const boshqaCheckbox = document.querySelector('input[name="chb_boshqa"]');
    const milliyCollapse = document.getElementById('milliy_collapse');
    const boshqaCollapse = document.getElementById('boshqa_collapse');

        // Collapse bo'limlarni boshqarish va checkboxlarni nazorat qilish
    if (section === 'milliy') {
        if (milliyCheckbox.checked) {
             milliyCollapse.style.display = 'block';
             boshqaCollapse.style.display = 'none';
             boshqaCheckbox.checked = false; // Ikkinchi checkboxni o'chirish
        } else {
             milliyCollapse.style.display = 'none';
        }
    } else if (section === 'boshqa') {
        if (boshqaCheckbox.checked) {
             boshqaCollapse.style.display = 'block';
             milliyCollapse.style.display = 'none';
             milliyCheckbox.checked = false; // Birinchi checkboxni o'chirish
        } else {
             boshqaCollapse.style.display = 'none';
        }
    }
}

// Tugmalarni topamiz
const buttons = document.querySelectorAll('[data-modal-id]');

    buttons.forEach(button => {
        button.addEventListener('click', function () {
            const modalId = button.getAttribute('data-modal-id');
            const modal = document.getElementById(modalId);
            modal.style.display = 'block';
        });
    });

// Modalni yopish uchun tugmalar
const closeButtons = document.querySelectorAll('.modal .btn-close');

    closeButtons.forEach(closeBtn => {
        closeBtn.addEventListener('click', function () {
            const modal = closeBtn.closest('.modal');
            modal.style.display = 'none';
        });
    });

function toggleContent(checkbox, contentId) {
    const contentDiv = document.getElementById(contentId);

    if (checkbox.checked) {
        contentDiv.style.display = "block"; // Forma ochiladi
    } else {
        contentDiv.style.display = "none";  // Forma yopiladi
    }
}

document.getElementById("submit-btn").onclick = function() {
    this.disabled = true; // Tugmani o'chirish
    this.form.submit(); // Formani yuborish
};

function toggleCheckboxes(current, otherId) {
        const otherCheckbox = document.getElementById(otherId);
        if (current.checked) {
            otherCheckbox.checked = false; // Boshqa checkboxni o'chirish
            const reasonContent = document.getElementById('rad_content_' + current.id.split('_')[2]);
            reasonContent.style.display = current.value === 'rejected' ? 'block' : 'none';
        }
    }

    function updateStatus(applicationId) {
        const form = document.getElementById('statusForm_' + applicationId);
        const formData = new FormData(form);
        const csrfToken = formData.get('csrfmiddlewaretoken');
        const status = formData.get('status');
        const reason = formData.get('reason');

        fetch(`/update_status/${applicationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Jadvaldagi statusni yangilash
                    document.getElementById('status_' + applicationId).innerText = data.status === 'accepted'
                        ? 'Qabul qilingan'
                        : 'Rad etilgan';
                    // Modalni yopish
                    const modal = bootstrap.Modal.getInstance(document.getElementById('applicationModal_' + applicationId));
                    modal.hide();
                } else {
                    alert('Xatolik yuz berdi!');
                }
            })
            .catch(error => console.error('Error:', error));

        return false; // Formani qayta yuklashni oldini olish
    }
    function updateStatus(applicationId) {
    const form = document.getElementById('statusForm_' + applicationId);
    const formData = new FormData(form);
    const csrfToken = formData.get('csrfmiddlewaretoken');
    const status = formData.get('status');

    if (!status) {
        alert('Iltimos, statusni tanlang!');
        return false;
    }

    fetch(`/update_status/${applicationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('status_' + applicationId).innerText =
                    data.status === 'accepted' ? 'Qabul qilingan' : 'Rad etilgan';
                const modal = bootstrap.Modal.getInstance(document.getElementById('applicationModal_' + applicationId));
                modal.hide();
            } else {
                alert(data.message || 'Xatolik yuz berdi!');
            }
        })
        .catch(error => console.error('Error:', error));

    return false;
}

def validate_file(file):
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise ValidationError("Fayl hajmi 5MB dan oshmasligi kerak.")
    valid_extensions = ['.pdf', '.doc', '.docx']
    ext = os.path.splitext(file.name)[1]
    if ext.lower() not in valid_extensions:
        raise ValidationError("Faqat PDF yoki Word fayllariga ruxsat beriladi.")

document.getElementById('submit-btn').addEventListener('click', function(event) {
        var directions = document.getElementById('directions').value;
        var sciences = document.getElementById('sciences').value;
        var type_edu = document.getElementById('type_edu').value;
        var first_name = document.getElementById('first_name').value;
        var last_name = document.getElementById('last_name').value;
        var father_name = document.getElementById('father_name').value;
        var phone_number = document.getElementById('phone_number').value;

        // Kerakli maydonlar to'ldirilganligini tekshirish
        if (!directions || !sciences || !type_edu || !first_name || !last_name || !father_name || !phone_number) {
            event.preventDefault();  // Forma yuborilmasligi uchun
            alert("Iltimos, barcha maydonlarni to'ldiring!");
        }
    });

// Sana
  function formatDate(date) {
      const days = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];
      const months = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"];

      const dayName = days[date.getDay()];
      const day = String(date.getDate()).padStart(2, "0");
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const year = date.getFullYear();

      return `${dayName}, ${day}/${month}/${year}`;
  }

  // Sana va soatni yangilash funksiyasi
  function updateDate() {
      const today = new Date();
      const formattedDate = formatDate(today);
      document.getElementById("date-display").textContent = formattedDate;
  }

  // Soat
  function updateTime() {
      const now = new Date();
      const formattedTime = now.toLocaleTimeString("uz-UZ");
      document.getElementById("current-time").textContent = formattedTime;
  }

  // Dastlabki yuklash
  updateDate();
  updateTime();

  // Har 1 soniyada soatni yangilash
  setInterval(updateTime, 1000);


const monthYearElement = document.getElementById("month-year");
const calendarDatesElement = document.getElementById("calendar-dates");
const prevMonthButton = document.getElementById("prev-month");
const nextMonthButton = document.getElementById("next-month");

let currentDate = new Date();

function renderCalendar(date) {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDayOfMonth = new Date(year, month, 1).getDay();
    const lastDateOfMonth = new Date(year, month + 1, 0).getDate();

    // Oylik nomi va yilni ko'rsatish
    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    monthYearElement.textContent = `${monthNames[month]} ${year}`;

    // Sanalarni tozalash
    calendarDatesElement.innerHTML = "";

    // Birinchi kun uchun bo'sh hujayralar
    for (let i = 0; i < (firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1); i++) {
        const emptyDiv = document.createElement("div");
        calendarDatesElement.appendChild(emptyDiv);
    }

    // Oyning barcha kunlarini qo'shish
    for (let day = 1; day <= lastDateOfMonth; day++) {
        const dayDiv = document.createElement("div");
        dayDiv.textContent = day;

        // Agar bugungi kun bo'lsa, alohida sinf qo'shiladi
        if (
            day === new Date().getDate() &&
            month === new Date().getMonth() &&
            year === new Date().getFullYear()
        ) {
            dayDiv.classList.add("today");
        }

        calendarDatesElement.appendChild(dayDiv);
    }
}

// Oldingi va keyingi oyni boshqarish
prevMonthButton.addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar(currentDate);
});

nextMonthButton.addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar(currentDate);
});

// Boshlang'ich kalendarni ko'rsatish
renderCalendar(currentDate);

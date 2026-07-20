document.addEventListener('DOMContentLoaded', function() {
    // تعريف العناصر
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const previewImage = document.getElementById('previewImage');
    const placeholder = document.getElementById('upload-placeholder');
    const resultsList = document.getElementById('results-list');
    const noResults = document.getElementById('noResults');
    const loader = document.getElementById('loader');

    // 1. تفعيل النقر على منطقة الرفع
    if(uploadArea) {
        uploadArea.addEventListener('click', () => fileInput.click());
    }

    // 2. عند اختيار ملف
    if(fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                handleFile(this.files[0]);
            }
        });
    }

    // 3. دالة معالجة الملف والعرض المبدئي
    function handleFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewImage.classList.remove('hidden'); // إظهار الصورة
            previewImage.style.display = 'block';
            if(placeholder) placeholder.classList.add('hidden');
        };
        reader.readAsDataURL(file);

        // استدعاء دالة الرفع للسيرفر
        uploadImage(file);
    }

    // 4. دالة الإرسال للسيرفر (AJAX/Fetch)
    function uploadImage(file) {
        // إظهار التحميل وإخفاء النتائج القديمة
        loader.classList.remove('hidden');
        resultsList.innerHTML = "";
        noResults.classList.add('hidden');

        const formData = new FormData();
        formData.append('image', file); // 'image' هو الاسم الذي ينتظره views.py

        fetch('/search/', { // تأكد أن هذا الرابط مطابق لـ urls.py
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken') // ضروري لحماية جانغو
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            loader.classList.add('hidden');
            displayResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            loader.classList.add('hidden');
            alert("حدث خطأ أثناء المعالجة، يرجى المحاولة مرة أخرى.");
        });
    }

    // 5. دالة عرض النتائج (التي أرسلتها أنت مع التعديل)
    function displayResults(results) {
        resultsList.innerHTML = "";

        // إذا كانت المصفوفة فارغة أو فيها خطأ
        if (!results || results.length === 0 || results.error) {
            noResults.classList.remove("hidden");
            return;
        }

        const result = results[0]; // نعرض أفضل نتيجة فقط

        const card = document.createElement("div");
        card.classList.add("result-card");

        const img = document.createElement("img");
        // دمج بادئة Base64 لتعمل الصورة
        if (result.thumbnail) {
            img.src = "data:image/jpeg;base64," + result.thumbnail;
        } else {
            img.src = ""; // صورة فارغة أو افتراضية
        }
        img.alt = "match";

        const info = document.createElement("div");
        info.classList.add("result-info");

        const pPath = document.createElement("p");
        // قمنا بتنسيق النص
        pPath.innerHTML = `<strong>المسار:</strong> ${result.path}`;
        pPath.style.wordBreak = "break-all"; // لضمان عدم خروج النص عن الكارد

        const pScore = document.createElement("p");
        // كلما قل الرقم زاد التشابه (0 هو تطابق تام)
        pScore.innerHTML = `<strong>درجة الاختلاف:</strong> ${result.distance.toFixed(4)}`;
        pScore.style.color = result.distance < 0.6 ? "green" : "#f1c40f";

        info.appendChild(pPath);
        info.appendChild(pScore);
        card.appendChild(img);
        card.appendChild(info);
        resultsList.appendChild(card);
    }

    // 6. دالة مساعدة لجلب التوكن (CSRF) - مهمة جداً في جانغو
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});



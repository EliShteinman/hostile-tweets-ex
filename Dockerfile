# =====================================================================
# שלב 1: אימג' בסיס של Red Hat UBI 9 עם פייתון.
# אימג' זה תואם FIPS ונועד לרוץ ב-OpenShift.
# הוא רץ כמשתמש non-root (UID 1001) כברירת מחדל.
# =====================================================================
FROM registry.access.redhat.com/ubi9/python-311

# הגדרות סביבה סטנדרטיות
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# הגדר את ספריית העבודה
WORKDIR /app

# ---------------------------------------------------------------------
# חלק זה דורש הרשאות root, לכן אנו עוברים זמנית למשתמש root
USER root
# שנה את הבעלות על ספריית העבודה למשתמש ברירת המחדל (1001)
# הקבוצה 0 היא קבוצת root, שהמשתמש שייך אליה ויש לו הרשאות כתיבה
RUN chown -R 1001:0 /app
# ---------------------------------------------------------------------

# חזור למשתמש ה-non-root המאובטח להמשך הבנייה והריצה
USER 1001

# העתק והתקן תלויות (כמשתמש non-root)
COPY requirements.txt .
RUN pip install -r requirements.txt

# העתק את קוד המקור (כמשתמש non-root)
COPY ./app /app/app
COPY ./data /app/data

# חשוף את הפורט
EXPOSE 8080

# הפקודה להרצת האפליקציה
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
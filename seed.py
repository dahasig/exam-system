from app.database import create_db_and_tables, get_session
from app.models import User, Question
from sqlmodel import select, delete


TOPICS = [
    ("مستخدم لا يرى مجلد مشترك", "فحص صلاحيات الوصول وعضوية المجموعات", ["التحقق من NTFS Permissions", "مراجعة Share Permissions", "فحص Effective Access"]),
    ("مستخدم لا يستطيع تعديل ملف مشترك", "فحص صلاحيات الكتابة على المجلد", ["التحقق من Write Permission", "مراجعة Inheritance", "فحص Ownership"]),
    ("ظهور Access Denied عند فتح مجلد", "تحليل صلاحيات الوصول", ["مراجعة ACL", "التحقق من Group Membership", "فحص Deny Permissions"]),
    ("مستخدم لا يرى تطبيق مخصص له", "فحص الصلاحيات وسياسة النشر", ["مراجعة Security Group", "فحص Deployment Policy", "التحقق من User Scope"]),
    ("مستخدم لا يستطيع الوصول لنظام داخلي", "فحص الصلاحيات المرتبطة بالنظام", ["مراجعة Role Assignment", "فحص Access Policy", "التحقق من User Permissions"]),

    ("مستخدم لا يستطيع تسجيل الدخول", "فحص حالة الحساب وسجلات الدخول", ["التحقق من Lockout Status", "مراجعة Login Logs", "فحص Password Expiry"]),
    ("تكرار قفل حساب مستخدم", "تحليل سبب القفل من السجلات", ["مراجعة Logon Attempts", "فحص Stored Credentials", "التحقق من الخدمات المرتبطة"]),
    ("فشل تسجيل الدخول رغم صحة البيانات", "تحليل عملية المصادقة", ["مراجعة Authentication Logs", "فحص Domain Connectivity", "التحقق من Policy Restrictions"]),
    ("مستخدم لا يستطيع تغيير كلمة المرور", "فحص سياسات كلمة المرور وحالة الحساب", ["مراجعة Password Policy", "فحص Account Restrictions", "التحقق من Domain Connection"]),
    ("Outlook يطلب كلمة المرور بشكل متكرر", "فحص بيانات الاعتماد وطريقة المصادقة", ["حذف Credential Manager", "مراجعة Authentication Method", "التحقق من Token Validity"]),

    ("النظام يعمل بالـ IP ولا يعمل بالاسم", "فحص DNS وسجلات الاسم", ["التحقق من A Record", "تفريغ DNS Cache", "مراجعة DNS Server Settings"]),
    ("ظهور خطأ DNS_PROBE_FINISHED_NXDOMAIN", "تحليل DNS واسم النطاق", ["مراجعة Name Resolution", "فحص DNS Records", "التحقق من Domain Name"]),
    ("بطء في استجابة DNS", "تحليل أداء DNS", ["فحص DNS Response Time", "مراجعة DNS Server Load", "التحقق من Network Latency"]),
    ("عدم حل اسم خادم معين", "تحليل سجلات DNS", ["التحقق من Zone Records", "مراجعة Forwarders", "فحص Local DNS Cache"]),
    ("DNS يعمل لبعض المستخدمين فقط", "تحليل إعدادات العملاء ونطاق الشبكة", ["مراجعة Client DNS Settings", "فحص DNS Scope", "التحقق من Network Segment"]),

    ("جهاز لا يحصل على IP", "فحص DHCP ونطاق العناوين", ["التحقق من Scope Range", "مراجعة Lease Availability", "فحص DHCP Service"]),
    ("تعارض عنوان IP في الشبكة", "تحليل DHCP والعناوين الثابتة", ["مراجعة DHCP Lease Table", "فحص Static Assignments", "التحقق من Rogue DHCP"]),
    ("جهاز يحصل على APIPA", "تحليل وصول الجهاز إلى DHCP", ["فحص DHCP Reachability", "مراجعة Network Adapter", "التحقق من VLAN"]),
    ("DHCP يعمل لبعض الأجهزة فقط", "تحليل النطاق والتقسيم الشبكي", ["فحص Scope Configuration", "مراجعة Network Segmentation", "التحقق من Relay Agent"]),
    ("تأخير في الحصول على IP", "تحليل أداء DHCP", ["مراجعة DHCP Response Time", "فحص Network Latency", "التحقق من DHCP Load"]),

    ("بطء عام في الشبكة", "تحليل الأداء الشبكي", ["فحص Latency", "مراجعة Packet Loss", "تحليل Bandwidth Usage"]),
    ("انقطاع متكرر في الاتصال", "تحليل استقرار الشبكة", ["فحص Link Stability", "مراجعة Network Logs", "التحقق من Switch Port"]),
    ("جهاز لا يصل للإنترنت", "فحص المسار والبوابة و DNS", ["التحقق من Gateway", "مراجعة DNS", "فحص Routing"]),
    ("بطء في موقع معين فقط", "تحليل المسار إلى الموقع", ["فحص Traceroute", "مراجعة Routing Path", "تحليل Latency"]),
    ("مشكلة بعد تعديل VLAN", "تحليل إعدادات VLAN", ["مراجعة VLAN Config", "فحص Tagging", "التحقق من Port Assignment"]),

    ("بطء جهاز مستخدم", "تحليل موارد الجهاز", ["فحص CPU Usage", "مراجعة Memory Usage", "تحليل Disk Activity"]),
    ("استهلاك CPU مرتفع", "تحديد العملية المتسببة", ["تحديد Process", "مراجعة Load", "تحليل Background Services"]),
    ("امتلاء القرص", "تحليل استهلاك التخزين", ["فحص Disk Usage", "مراجعة Large Files", "تحليل Logs"]),
    ("بطء في فتح البرامج", "تحليل أداء النظام", ["فحص Startup Programs", "مراجعة System Resources", "تحليل Disk Speed"]),
    ("تأخير تسجيل الدخول للجهاز", "تحليل سياسات الدخول والخدمات", ["مراجعة Login Scripts", "فحص GPO", "تحليل Network Delay"]),

    ("Outlook لا يرسل بريد", "فحص إعدادات الإرسال والاتصال", ["مراجعة SMTP Settings", "فحص Connectivity", "التحقق من Mailbox Quota"]),
    ("تأخير في وصول البريد", "تحليل مسار البريد", ["مراجعة Mail Queue", "فحص Server Load", "تحليل Mail Flow"]),
    ("عدم مزامنة البريد", "تحليل إعدادات المزامنة", ["فحص Sync Settings", "مراجعة Connection", "التحقق من Server Status"]),
    ("رسائل البريد ترجع Bounce", "تحليل سبب الارتداد", ["مراجعة Mail Logs", "فحص DNS Records", "التحقق من Blacklist"]),
    ("Outlook لا يفتح", "تحليل ملف التعريف والإضافات", ["فحص Outlook Profile", "مراجعة Add-ins", "تحليل Application Logs"]),

    ("HTTP 500 في نظام داخلي", "تحليل أخطاء التطبيق", ["مراجعة Application Logs", "فحص Exceptions", "تحليل Server Errors"]),
    ("HTTP 403 في نظام داخلي", "تحليل الصلاحيات وسياسات الوصول", ["مراجعة ACL", "فحص Access Policy", "التحقق من Permissions"]),
    ("HTTP 502 في نظام داخلي", "تحليل الاتصال بين البوابة والخادم الخلفي", ["فحص Backend Server", "مراجعة Gateway Logs", "تحليل Connection"]),
    ("HTTP 504 في نظام داخلي", "تحليل مهلة الاتصال", ["فحص Response Time", "مراجعة Backend Performance", "تحليل Network Delay"]),
    ("بطء موقع ويب داخلي", "تحليل أداء الموقع", ["فحص Load Time", "مراجعة Server Load", "تحليل Network Path"]),

    ("اشتباه ببرمجية خبيثة على جهاز", "تحليل مؤشرات الإصابة", ["فحص Antivirus Logs", "مراجعة Running Processes", "تحليل Suspicious Behavior"]),
    ("برنامج الحماية لا يعمل", "فحص حالة الحماية", ["مراجعة Service Status", "فحص Update Status", "تحليل Security Logs"]),
    ("محاولات دخول مشبوهة", "تحليل سجلات الأمان", ["مراجعة Security Logs", "فحص IP Source", "تحليل Login Patterns"]),
    ("اشتباه باختراق حساب", "تحليل نشاط الحساب", ["مراجعة Login History", "فحص Permission Changes", "تحليل User Activity"]),
    ("فشل تحديث أمني", "تحليل سبب فشل التحديث", ["مراجعة Update Logs", "فحص Dependencies", "تحليل Compatibility"]),

    ("فشل النسخ الاحتياطي", "تحليل عملية النسخ الاحتياطي", ["مراجعة Backup Logs", "فحص Storage Availability", "تحليل Connection"]),
    ("Load Balancer لا يوزع الطلبات", "تحليل التوزيع والفحص الصحي", ["فحص Health Checks", "مراجعة Node Status", "تحليل Routing Rules"]),
    ("GPO لا يطبق على جهاز", "تحليل تطبيق السياسات", ["مراجعة OU", "فحص Security Filtering", "تحليل gpresult"]),
    ("فشل Kerberos", "تحليل بيئة المصادقة", ["فحص Time Sync", "مراجعة SPN", "تحليل DNS"]),
    ("SSO لا يعمل", "تحليل المصادقة الموحدة", ["مراجعة Token Validation", "فحص Identity Provider", "تحليل Time Sync"]),

    ("VPN لا يتصل", "تحليل اتصال VPN", ["فحص Authentication Method", "مراجعة VPN Profile", "التحقق من Certificate Validity"]),
    ("VPN يتصل ولا يصل للأنظمة", "تحليل المسارات بعد الاتصال", ["فحص Routing Table", "مراجعة Split Tunnel", "التحقق من DNS بعد الاتصال"]),
    ("فشل تطبيق تحديثات مركزية", "تحليل عميل التحديث والسياسات", ["مراجعة Update Agent", "فحص Policy Assignment", "تحليل Deployment Logs"]),
    ("تطبيق داخلي بطيء لعدة مستخدمين", "تحليل نطاق التأثر والخادم", ["مراجعة Server Resources", "فحص Application Logs", "تحليل Database Response"]),
    ("تطبيق داخلي بطيء لمستخدم واحد", "تحليل بيئة المستخدم والجهاز", ["فحص User Profile", "مراجعة Client Resources", "تحليل User-Specific Logs"]),

    ("حساب خدمة يتكرر قفله", "تحليل مصادر استخدام الحساب", ["مراجعة Scheduled Tasks", "فحص Services Credentials", "تحليل Failed Logons"]),
    ("تعذر تثبيت برنامج معتمد", "تحليل سياسة التثبيت والصلاحيات", ["فحص Installation Policy", "مراجعة Software Center", "التحقق من User Privileges"]),
    ("جهاز لا يظهر في نظام الإدارة المركزي", "تحليل اتصال عميل الإدارة", ["فحص Management Agent", "مراجعة Client Logs", "التحقق من Boundary Group"]),
    ("فشل تكامل بين نظامين", "تحليل الاتصال والمصادقة والبيانات", ["مراجعة API Logs", "فحص Authentication", "تحليل Payload Format"]),
    ("بطء استعلام في قاعدة البيانات", "تحليل أداء قاعدة البيانات", ["فحص Execution Plan", "مراجعة Indexes", "تحليل Locks"]),
]


ESSAY = [
    ("medium", "اشرح خطواتك في تشخيص مشكلة مستخدم لا يستطيع الوصول إلى مجلد مشترك مع توضيح الفرق بين Share Permissions و NTFS Permissions."),
    ("medium", "اشرح منهجيتك في التعامل مع جهاز لا يحصل على عنوان IP من DHCP مع ذكر الفحوصات الأساسية."),
    ("medium", "اشرح كيف تحلل مشكلة بطء جهاز مستخدم مع المحافظة على بياناته وعدم تعطيل عمله."),
    ("hard", "اشرح طريقة تشخيص فشل SSO لعدة مستخدمين مع تحديد الأدلة الفنية المطلوبة."),
    ("hard", "اشرح كيف تتعامل مع حساب خدمة يتكرر قفله يوميا مع تحديد مصادر الفحص المحتملة."),
    ("hard", "اشرح خطة تحليل مشكلة بطء تطبيق داخلي يؤثر على عدة إدارات مع تحديد مسار التصعيد.")
]


def add_question(session, level, qtype, question, options=None, correct="A"):
    existing = session.exec(
        select(Question).where(
            Question.question == question,
            Question.level == level,
            Question.qtype == qtype
        )
    ).first()

    if existing:
        return

    options = options or ["", "", "", ""]
    session.add(
        Question(
            category="support",
            level=level,
            qtype=qtype,
            question=question,
            option_a=options[0],
            option_b=options[1],
            option_c=options[2],
            option_d=options[3],
            correct_option=correct,
        )
    )


def run():
    create_db_and_tables()
    session = next(get_session())

    # يحذف الأسئلة فقط لتحديث بنك الأسئلة
    # لا يحذف المستخدمين ولا نتائج الاختبارات
    session.exec(delete(Question))
    session.commit()

    user = session.exec(
        select(User).where(User.username == "nimda")
    ).first()

    if user:
        user.password = "nimdaa"
        session.add(user)
    else:
        session.add(User(username="nimda", password="nimdaa"))

    letters = ["A", "B", "C", "D"]
    half = len(TOPICS) // 2

    for i in range(len(TOPICS)):
        topic, correct_text, wrongs = TOPICS[i]
        level = "medium" if i < half else "hard"

        question = f"ما الإجراء الأنسب عند {topic}؟"

        correct_letter = letters[i % 4]
        options = ["", "", "", ""]
        options[letters.index(correct_letter)] = correct_text

        w = 0
        for idx in range(4):
            if options[idx] == "":
                options[idx] = wrongs[w]
                w += 1

        add_question(session, level, "mcq", question, options, correct_letter)

    for level, q in ESSAY:
        add_question(session, level, "essay", q)

    session.commit()
    session.close()

    print("تم تحديث بنك الأسئلة بأمان")
    print("60 سؤال اختياري")
    print("6 أسئلة مقالية")
    print("لم يتم حذف المستخدمين أو نتائج الاختبارات")
    print("بيانات الإدارة: nimda / nimdaa")


if __name__ == "__main__":
    run()

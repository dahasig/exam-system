from app.database import create_db_and_tables, get_session
from app.models import User, Question
from sqlmodel import select


TOPICS = [

# ===== ACCESS / PERMISSIONS =====
("مستخدم لا يرى مجلد مشترك",
 "فحص صلاحيات الوصول وعضوية المجموعات",
 ["التحقق من NTFS Permissions", "مراجعة Share Permissions", "التأكد من عضوية المستخدم في المجموعة"]),

("مستخدم لا يستطيع تعديل ملف مشترك",
 "فحص صلاحيات الكتابة على المجلد",
 ["التحقق من Write Permission", "مراجعة Inheritance", "فحص Effective Permissions"]),

("ظهور Access Denied عند فتح مجلد",
 "تحليل صلاحيات الوصول",
 ["مراجعة ACL", "التحقق من Ownership", "فحص Group Membership"]),

("مستخدم لا يرى تطبيق مخصص له",
 "فحص الصلاحيات والتوزيع",
 ["مراجعة Security Group", "فحص Deployment Policy", "التحقق من User Scope"]),

("مستخدم لا يستطيع الوصول لنظام",
 "فحص الصلاحيات المرتبطة بالنظام",
 ["مراجعة Role Assignment", "فحص Access Policy", "التحقق من User Permissions"]),

# ===== ACCOUNT / LOGIN =====
("مستخدم لا يستطيع تسجيل الدخول",
 "فحص حالة الحساب",
 ["التحقق من Lockout Status", "مراجعة Event Logs", "التأكد من Password Expiry"]),

("تكرار قفل حساب مستخدم",
 "تحليل سبب القفل",
 ["مراجعة Logon Attempts", "فحص Stored Credentials", "التحقق من الخدمات المرتبطة"]),

("فشل تسجيل الدخول رغم صحة البيانات",
 "تحليل عملية المصادقة",
 ["مراجعة Authentication Logs", "فحص Domain Connectivity", "التحقق من Policy Restrictions"]),

("مستخدم لا يستطيع تغيير كلمة المرور",
 "فحص سياسات كلمة المرور",
 ["مراجعة Password Policy", "التحقق من Account Restrictions", "فحص Domain Connection"]),

("Outlook يطلب كلمة المرور بشكل متكرر",
 "فحص بيانات الاعتماد",
 ["حذف Credential Manager", "مراجعة Authentication Method", "التحقق من Token Validity"]),

# ===== DNS =====
("النظام يعمل بالـ IP ولا يعمل بالاسم",
 "فحص DNS",
 ["التحقق من A Record", "تفريغ DNS Cache", "مراجعة DNS Server Settings"]),

("خطأ DNS_PROBE_FINISHED_NXDOMAIN",
 "تحليل DNS",
 ["مراجعة Name Resolution", "فحص DNS Records", "التحقق من Domain Name"]),

("بطء في استجابة DNS",
 "تحليل الأداء",
 ["فحص DNS Response Time", "مراجعة DNS Server Load", "التحقق من Network Latency"]),

("عدم resolve لاسم معين",
 "تحليل المشكلة",
 ["التحقق من Zone Records", "مراجعة Forwarders", "فحص Local DNS Cache"]),

("DNS يعمل لبعض المستخدمين فقط",
 "تحليل النطاق",
 ["مراجعة Client Settings", "فحص DNS Scope", "التحقق من Network Segment"]),

# ===== DHCP =====
("جهاز لا يحصل على IP",
 "فحص DHCP",
 ["التحقق من Scope Range", "مراجعة Lease Availability", "فحص DHCP Service"]),

("IP متكرر في الشبكة",
 "تحليل DHCP",
 ["مراجعة DHCP Lease Table", "فحص Static Assignments", "التحقق من Rogue DHCP"]),

("جهاز يحصل على APIPA",
 "تحليل المشكلة",
 ["فحص DHCP Reachability", "مراجعة Network Adapter", "التحقق من VLAN"]),

("DHCP يعمل لبعض الأجهزة فقط",
 "تحليل النطاق",
 ["فحص Scope Configuration", "مراجعة Network Segmentation", "التحقق من Relay Agent"]),

("تأخير في الحصول على IP",
 "تحليل الأداء",
 ["مراجعة DHCP Response Time", "فحص Network Latency", "التحقق من DHCP Load"]),

# ===== NETWORK =====
("بطء في الشبكة",
 "تحليل الأداء",
 ["فحص Latency", "مراجعة Packet Loss", "تحليل Bandwidth Usage"]),

("انقطاع متكرر في الاتصال",
 "تحليل الشبكة",
 ["فحص Stability", "مراجعة Logs", "التحقق من Network Devices"]),

("جهاز لا يصل للإنترنت",
 "فحص الاتصال",
 ["التحقق من Gateway", "مراجعة DNS", "فحص Routing"]),

("بطء في موقع معين فقط",
 "تحليل المسار",
 ["فحص Traceroute", "مراجعة Routing", "تحليل Latency"]),

("مشاكل في VLAN",
 "تحليل الشبكة",
 ["مراجعة VLAN Config", "فحص Tagging", "التحقق من Port Assignment"]),

# ===== SYSTEM PERFORMANCE =====
("بطء جهاز مستخدم",
 "تحليل الأداء",
 ["فحص CPU Usage", "مراجعة Memory Usage", "تحليل Disk Activity"]),

("استهلاك CPU مرتفع",
 "تحليل العمليات",
 ["تحديد Process", "مراجعة Load", "تحليل Background Services"]),

("امتلاء القرص",
 "تحليل التخزين",
 ["فحص Disk Usage", "مراجعة Large Files", "تحليل Logs"]),

("بطء في فتح البرامج",
 "تحليل الأداء",
 ["فحص Startup Programs", "مراجعة System Resources", "تحليل Disk Speed"]),

("تأخير تسجيل الدخول",
 "تحليل النظام",
 ["مراجعة Login Scripts", "فحص GPO", "تحليل Network Delay"]),

# ===== EMAIL =====
("Outlook لا يرسل بريد",
 "فحص الإعدادات",
 ["مراجعة SMTP Settings", "فحص Connectivity", "التحقق من Mailbox Quota"]),

("تأخير في وصول البريد",
 "تحليل الأداء",
 ["مراجعة Mail Queue", "فحص Server Load", "تحليل Network"]),

("عدم مزامنة البريد",
 "تحليل المشكلة",
 ["فحص Sync Settings", "مراجعة Connection", "التحقق من Server Status"]),

("رسائل ترجع Bounce",
 "تحليل السبب",
 ["مراجعة Mail Logs", "فحص DNS Records", "التحقق من Blacklist"]),

("Outlook لا يفتح",
 "تحليل التطبيق",
 ["فحص Profile", "مراجعة Add-ins", "تحليل Logs"]),

# ===== WEB =====
("HTTP 500",
 "تحليل التطبيق",
 ["مراجعة Logs", "فحص Exceptions", "تحليل Server Errors"]),

("HTTP 403",
 "تحليل الصلاحيات",
 ["مراجعة ACL", "فحص Access Policy", "التحقق من Permissions"]),

("HTTP 502",
 "تحليل البنية",
 ["فحص Backend Server", "مراجعة Gateway", "تحليل Connection"]),

("HTTP 504",
 "تحليل Timeout",
 ["فحص Response Time", "مراجعة Backend", "تحليل Network Delay"]),

("بطء موقع ويب",
 "تحليل الأداء",
 ["فحص Load Time", "مراجعة Server Load", "تحليل Network"]),

# ===== SECURITY =====
("اشتباه ببرمجية خبيثة",
 "تحليل الأمان",
 ["فحص Antivirus Logs", "مراجعة Processes", "تحليل Behavior"]),

("برنامج الحماية لا يعمل",
 "فحص النظام",
 ["مراجعة Service Status", "فحص Update Status", "تحليل Logs"]),

("محاولات دخول مشبوهة",
 "تحليل الأمان",
 ["مراجعة Security Logs", "فحص IP Source", "تحليل Patterns"]),

("حساب مخترق",
 "تحليل الحادثة",
 ["مراجعة Login History", "فحص Permissions", "تحليل Activity"]),

("فشل تحديث أمني",
 "تحليل التحديث",
 ["مراجعة Update Logs", "فحص Dependencies", "تحليل Compatibility"]),

# ===== INFRA =====
("فشل Backup",
 "تحليل العملية",
 ["مراجعة Backup Logs", "فحص Storage", "تحليل Connection"]),

("Load Balancer لا يعمل",
 "تحليل التوزيع",
 ["فحص Health Checks", "مراجعة Nodes", "تحليل Routing"]),

("GPO لا يطبق",
 "تحليل السياسة",
 ["مراجعة OU", "فحص Security Filtering", "تحليل gpresult"]),

("Kerberos يفشل",
 "تحليل البيئة",
 ["فحص Time Sync", "مراجعة SPN", "تحليل DNS"]),

("SSO لا يعمل",
 "تحليل المصادقة",
 ["مراجعة Token", "فحص IdP", "تحليل Time Sync"]),
]

PHRASES = [
    "ما الإجراء الأنسب عند",
    "ما الفحص الأدق في حالة",
    "ما التحليل الأقرب عند",
    "ما المسار التشخيصي الأفضل عند",
    "ما القرار الفني الصحيح عند",
]


ESSAY = [
    ("medium", "اشرح خطواتك في تشخيص مشكلة عدم قدرة مستخدم واحد على الدخول إلى نظام داخلي مهم."),
    ("medium", "اشرح منهجيتك في التعامل مع بلاغ يؤثر على عدة إدارات من الاستقبال حتى الإغلاق."),
    ("medium", "اشرح كيف تحلل بطء جهاز مستخدم مع المحافظة على بياناته وعدم تعطيل عمله."),
    ("hard", "اشرح كيف تحلل انقطاعا متكررا بين موقعين مع تحديد الأدلة الفنية المطلوبة."),
    ("hard", "اشرح طريقة التعامل مع مشكلة ظهرت بعد تحديث أمني مع الحفاظ على الأمن واستمرارية العمل."),
    ("hard", "اشرح خطة لتقليل البلاغات المتكررة في بيئة دعم فني مؤسسية."),
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

    user = session.exec(
        select(User).where(User.username == "nimda")
    ).first()

    if user:
        user.password = "nimdaa"
        session.add(user)
    else:
        session.add(User(username="nimda", password="nimdaa"))

    letters = ["A", "B", "C", "D"]

    for i in range(len(TOPICS)):
        topic, correct_text, wrongs = TOPICS[i % len(TOPICS)]
        phrase = PHRASES[i % len(PHRASES)]

        if i < 75:
            level = "medium"
            question = f"{phrase} {topic}؟"
        else:
            level = "hard"
            question = f"{phrase} {topic}؟"

        correct_letter = letters[i % 4]
        options = ["", "", "", ""]
        options[letters.index(correct_letter)] = correct_text

        w = 0
        for idx in range(4):
            if options[idx] == "":
                options[idx] = wrongs[w]
                w += 1

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
        phrase = PHRASES[i % len(PHRASES)]

        level = "medium" if i < half else "hard"
        question = f"{phrase} {topic}؟"

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

    print("تم تجهيز بنك الأسئلة بأمان")
    print("لا يتم حذف المستخدمين أو الأسئلة أو النتائج")
    print("بيانات الإدارة: nimda / nimdaa")


if __name__ == "__main__":
    run()

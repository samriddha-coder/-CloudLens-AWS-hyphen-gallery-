import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image as RLImage
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Circle, String

PAGE_WIDTH, PAGE_HEIGHT = A4

class BorderedNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(BorderedNumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, page_count):
        self.saveState()
        
        # Outer border
        self.setStrokeColor(colors.HexColor("#1e293b"))
        self.setLineWidth(1.5)
        self.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56)
        
        # Inner thin border
        self.setLineWidth(0.5)
        self.rect(31, 31, PAGE_WIDTH - 62, PAGE_HEIGHT - 62)

        # Header & Page numbers (on pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawString(42, PAGE_HEIGHT - 40, "INTERNSHIP TRAINING REPORT — KALNA POLYTECHNIC")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(42, 38, "Department of Computer Science & Technology | Dreamz Vision Finishing")
            self.drawRightString(PAGE_WIDTH - 42, 38, f"Page {self._pageNumber} of {page_count}")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(42, PAGE_HEIGHT - 44, PAGE_WIDTH - 42, PAGE_HEIGHT - 44)
        
        self.restoreState()

def ensure_annotated_images():
    screen1_path = os.path.join(os.path.dirname(__file__), "annotated_screen1.png")
    screen2_path = os.path.join(os.path.dirname(__file__), "annotated_screen2.png")
    if os.path.exists(screen1_path) and os.path.exists(screen2_path):
        return

    import math
    from PIL import Image, ImageDraw, ImageFont

    def draw_arrow(draw, start, end, color='#dc2626', width=3, arrow_size=12):
        x1, y1 = start
        x2, y2 = end
        draw.line([start, end], fill=color, width=width)
        angle = math.atan2(y2 - y1, x2 - x1)
        p1 = (x2 - arrow_size * math.cos(angle - math.pi/6),
              y2 - arrow_size * math.sin(angle - math.pi/6))
        p2 = (x2 - arrow_size * math.cos(angle + math.pi/6),
              y2 - arrow_size * math.sin(angle + math.pi/6))
        draw.polygon([end, p1, p2], fill=color)

    def draw_callout(draw, box, badge_pos, num, color='#dc2626', arrow_target=None):
        draw.rectangle(box, outline=color, width=3)
        bx, by = badge_pos
        if arrow_target is None:
            cx = (box[0] + box[2]) // 2
            cy = (box[1] + box[3]) // 2
            if bx < box[0]:
                target = (box[0], cy)
            elif bx > box[2]:
                target = (box[2], cy)
            elif by < box[1]:
                target = (cx, box[1])
            else:
                target = (cx, box[2])
        else:
            target = arrow_target
        draw_arrow(draw, badge_pos, target, color=color, width=3, arrow_size=12)
        r = 18
        draw.ellipse([bx - r + 2, by - r + 2, bx + r + 2, by + r + 2], fill='#64748b')
        draw.ellipse([bx - r, by - r, bx + r, by + r], fill=color, outline='#ffffff', width=2)
        try:
            font = ImageFont.truetype('arialbd.ttf', 20)
        except:
            font = ImageFont.load_default()
        txt = str(num)
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((bx - tw/2, by - th/2 - 2), txt, fill='#ffffff', font=font)

    # Candidate source files
    src1 = r"C:/Users/SAMRIDDHA/.gemini/antigravity/brain/11baa4f9-8626-4b45-a8b5-e9e8a7942107/.user_uploaded/media_1794109525646_cb558415.png"
    if os.path.exists(src1):
        im1 = Image.open(src1).convert('RGB')
        draw1 = ImageDraw.Draw(im1)
        draw_callout(draw1, (115, 65, 290, 100), (55, 82), 1, color='#dc2626', arrow_target=(115, 82))
        draw_callout(draw1, (630, 68, 775, 96), (702, 32), 2, color='#2563eb', arrow_target=(702, 68))
        draw_callout(draw1, (785, 66, 882, 100), (940, 83), 3, color='#7c3aed', arrow_target=(882, 83))
        draw_callout(draw1, (275, 240, 720, 275), (180, 257), 4, color='#059669', arrow_target=(275, 257))
        draw_callout(draw1, (130, 315, 865, 435), (55, 375), 5, color='#d97706', arrow_target=(130, 375))
        draw_callout(draw1, (130, 480, 865, 530), (55, 505), 6, color='#dc2626', arrow_target=(130, 505))
        im1.save(screen1_path, 'PNG')

    src2 = r"C:/Users/SAMRIDDHA/.gemini/antigravity/brain/11baa4f9-8626-4b45-a8b5-e9e8a7942107/.user_uploaded/media_1794109536619_eba34bef.jpg"
    if os.path.exists(src2):
        im2 = Image.open(src2).convert('RGB')
        draw2 = ImageDraw.Draw(im2)
        draw_callout(draw2, (750, 140, 875, 178), (940, 159), 1, color='#7c3aed', arrow_target=(875, 159))
        draw_callout(draw2, (115, 210, 310, 245), (55, 227), 2, color='#0284c7', arrow_target=(115, 227))
        draw_callout(draw2, (125, 258, 175, 280), (55, 269), 3, color='#ea580c', arrow_target=(125, 269))
        draw_callout(draw2, (115, 250, 365, 470), (430, 350), 4, color='#2563eb', arrow_target=(365, 350))
        draw_callout(draw2, (125, 476, 185, 510), (55, 493), 5, color='#059669', arrow_target=(125, 493))
        draw_callout(draw2, (290, 480, 360, 506), (430, 493), 6, color='#dc2626', arrow_target=(360, 493))
        im2.save(screen2_path, 'PNG')

def create_internship_report():
    ensure_annotated_images()
    pdf_path = os.path.join(os.path.dirname(__file__), "Internship_Training_Report_Samriddha_Das_Final.pdf")
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=50,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    main_title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=12
    )

    on_style = ParagraphStyle(
        'OnStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=12
    )

    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=8
    )

    dept_style = ParagraphStyle(
        'DeptStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=25
    )

    org_label_style = ParagraphStyle(
        'OrgLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#881337'),
        alignment=1,
        spaceAfter=6
    )

    org_name_style = ParagraphStyle(
        'OrgName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=20,
        textColor=colors.HexColor('#881337'),
        alignment=1,
        spaceAfter=20
    )

    page2_label = ParagraphStyle(
        'Page2Label',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=16,
        textColor=colors.HexColor('#0f172a')
    )

    page2_val = ParagraphStyle(
        'Page2Val',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=16,
        textColor=colors.HexColor('#1e1b4b')
    )

    section_header = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=12,
        textTransform='uppercase'
    )

    sub_header = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_text = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=9,
        alignment=4
    )

    bullet_text = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    table_th = ParagraphStyle(
        'TableTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    table_td = ParagraphStyle(
        'TableTD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # =========================================================================
    # PAGE 1: COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 15))
    story.append(Paragraph("INTERNSHIP TRAINING REPORT", main_title_style))
    story.append(Paragraph("ON", on_style))
    story.append(Paragraph("INTERNSHIP ON CLOUD COMPUTING", sub_title_style))
    story.append(Paragraph("(COMPUTER SCIENCE)", dept_style))
    story.append(Spacer(1, 10))

    # Center Emblem (Dreamz Vision Finishing)
    d = Drawing(160, 160)
    d.add(Circle(80, 80, 70, strokeColor=colors.HexColor('#450a0a'), strokeWidth=3, fillColor=colors.HexColor('#7f1d1d')))
    d.add(Circle(80, 80, 56, strokeColor=colors.HexColor('#b91c1c'), strokeWidth=1.5, fillColor=colors.white))
    d.add(String(58, 65, "DV", fontName="Times-BoldItalic", fontSize=44, fillColor=colors.HexColor('#7f1d1d')))
    story.append(d)
    story.append(Spacer(1, 25))

    story.append(HRFlowable(width="90%", thickness=1, color=colors.HexColor('#991b1b'), spaceBefore=8, spaceAfter=12))
    story.append(Paragraph("ORGANISED BY", org_label_style))
    story.append(Paragraph("DREAMZ VISION FINISHING", org_name_style))
    story.append(HRFlowable(width="90%", thickness=1, color=colors.HexColor('#991b1b'), spaceBefore=6, spaceAfter=45))
    story.append(Spacer(1, 40))

    # Signatures at bottom
    sig_data = [
        [
            Paragraph("<b>TRAINER'S SIGNATURE</b><br/><br/><br/>___________________________", ParagraphStyle('SigL', fontName='Helvetica-Bold', fontSize=10, leading=14, alignment=0)),
            Paragraph("<b>SUBMITTED BY</b><br/><br/><b>Samriddha Das</b><br/>___________________________", ParagraphStyle('SigR', fontName='Helvetica-Bold', fontSize=10, leading=14, alignment=2))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[240, 259])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(sig_table)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: CANDIDATE & INSTITUTION DETAILS
    # =========================================================================
    story.append(Spacer(1, 20))

    cand_data = [
        [Paragraph("NAME", page2_label), Paragraph(":", page2_label), Paragraph("Samriddha Das", page2_val)],
        [Paragraph("REG. NO.", page2_label), Paragraph(":", page2_label), Paragraph("D242520118", page2_val)],
        [Paragraph("SEM", page2_label), Paragraph(":", page2_label), Paragraph("5TH", page2_val)],
        [Paragraph("YEAR", page2_label), Paragraph(":", page2_label), Paragraph("2026-2027", page2_val)],
        [Paragraph("INSTITUTE NAME", page2_label), Paragraph(":", page2_label), Paragraph("Kalna Polytechnic", page2_val)],
        [Paragraph("DEPARTMENT", page2_label), Paragraph(":", page2_label), Paragraph("Computer Science and Technology", page2_val)],
        [Paragraph("FIELD OF TRAINING", page2_label), Paragraph(":", page2_label), Paragraph("INTERNSHIP ON CLOUD COMPUTING (COMPUTER SCIENCE)", page2_val)],
        [Paragraph("PERIOD", page2_label), Paragraph(":", page2_label), Paragraph("FROM 28/10/26 TO 06/11/26", page2_val)],
        [Paragraph("PROJECT NAME", page2_label), Paragraph(":", page2_label), Paragraph("CloudLens - AWS S3 & EC2 Image Gallery Web App", page2_val)],
        [Paragraph("LIVE WEB URL", page2_label), Paragraph(":", page2_label), Paragraph("<font color='#2563eb'><u>http://32.236.11.79</u></font>", page2_val)],
        [Paragraph("GITHUB LINK", page2_label), Paragraph(":", page2_label), Paragraph("<font color='#2563eb' size='9'><u>https://github.com/samriddha-coder/-CloudLens-AWS-hyphen-gallery-</u></font>", page2_val)],
    ]

    cand_table = Table(cand_data, colWidths=[155, 15, 329])
    cand_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (2, 0), (2, 3), 0.75, colors.HexColor('#0f172a')),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(cand_table)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: INTRODUCTION TO CLOUD COMPUTING & AWS
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("INTRODUCTION", section_header))
    story.append(Paragraph(
        "Cloud Computing is the on-demand delivery of IT resources over the Internet with pay-as-you-go pricing. "
        "Instead of buying, owning, and maintaining physical servers and data centers, organizations can access technology services, "
        "such as compute power, storage, and databases, on an as-needed basis from a cloud provider like Amazon Web Services (AWS).",
        body_text
    ))
    story.append(Paragraph(
        "In modern Computer Science and Software Engineering, cloud infrastructure is foundational for deploying resilient, "
        "high-availability web applications. By utilizing cloud-native architectures, developers decouple frontend clients, "
        "backend APIs, relational databases, and static media storage into scalable microservices.",
        body_text
    ))
    story.append(Paragraph(
        "<b>Amazon Web Services (AWS)</b> is the world's most comprehensive and broadly adopted cloud platform. "
        "During this internship training, two primary AWS core services were integrated and deployed to build the <b>CloudLens</b> project:",
        body_text
    ))
    story.append(Paragraph("• <b>Amazon Simple Storage Service (S3):</b> An industry-leading object storage service offering 99.999999999% (11 9s) of data durability. S3 is utilized to store, manage, and deliver user-uploaded images globally with fine-grained bucket policies and Cross-Origin Resource Sharing (CORS).", bullet_text))
    story.append(Paragraph("• <b>Amazon Elastic Compute Cloud (EC2):</b> Provides secure, resizable compute capacity in the cloud. An Ubuntu Linux virtual machine instance was provisioned to execute the containerized Node.js backend, React frontend, and PostgreSQL database cluster.", bullet_text))
    story.append(Paragraph("• <b>Containerization with Docker:</b> Encapsulates application code and its dependencies into lightweight containers, guaranteeing seamless parity between development and production cloud environments.", bullet_text))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: AIM & OBJECTIVES OF THE PROJECT
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("AIM", section_header))
    story.append(Paragraph(
        "To design, develop, and deploy a full-stack, cloud-native web application named <b>CloudLens</b> using modern web technologies "
        "(React.js, Node.js, Express, PostgreSQL) and enterprise cloud infrastructure (AWS S3, AWS EC2, and Docker), "
        "implementing public image ingestion and viewing alongside Role-Based Access Control (RBAC) for administrative asset deletion.",
        body_text
    ))

    story.append(Paragraph("CORE INTERNSHIP OBJECTIVES", sub_header))
    story.append(Paragraph("1. <b>Cloud Infrastructure Provisioning:</b> Gain hands-on practical competence in creating, configuring, and securing Amazon S3 buckets and Amazon EC2 virtual machines in the <code>ap-southeast-2</code> (Sydney) region.", bullet_text))
    story.append(Paragraph("2. <b>Direct S3 Media Streaming:</b> Implement server-side binary buffer streaming using the official AWS SDK (<code>@aws-sdk/client-s3</code>) to upload and delete objects without storing temporary files on disk.", bullet_text))
    story.append(Paragraph("3. <b>Relational Database Modeling:</b> Design a normalized PostgreSQL schema to persist image metadata (IDs, S3 URLs, original names, uploader identities, and timestamps).", bullet_text))
    story.append(Paragraph("4. <b>Role-Based Access Control (RBAC):</b> Implement JWT-based authentication ensuring that public users can only upload and view images, while destructive deletion operations are restricted strictly to administrators.", bullet_text))
    story.append(Paragraph("5. <b>DevOps Container Orchestration:</b> Architect a multi-container Docker Compose pipeline running PostgreSQL, Express API, and Nginx reverse proxy on an AWS EC2 Ubuntu instance.", bullet_text))
    story.append(Paragraph("6. <b>Version Control & Public Verification:</b> Version control all codebase artifacts on GitHub and verify live accessibility on public IPv4 <b>32.236.11.79</b>.", bullet_text))

    story.append(Spacer(1, 6))
    story.append(Paragraph("SYSTEM ARCHITECTURE OVERVIEW", sub_header))

    arch_data = [
        [Paragraph("Tier", table_th), Paragraph("Technology", table_th), Paragraph("Key Role in CloudLens", table_th)],
        [Paragraph("Client Layer", table_td), Paragraph("React.js (Vite), CSS3", table_td), Paragraph("Responsive web UI, drag-and-drop file upload, lightbox preview, and admin modal.", table_td)],
        [Paragraph("Application Layer", table_td), Paragraph("Node.js (Express REST API)", table_td), Paragraph("API routing, Multer memory buffer streaming, JWT authorization.", table_td)],
        [Paragraph("Cloud Storage", table_td), Paragraph("Amazon S3 (ap-southeast-2)", table_td), Paragraph("Durable object storage bucket (<code>samriddhabaket1718</code>) with CORS & public read.", table_td)],
        [Paragraph("Database Tier", table_td), Paragraph("PostgreSQL 16 Engine", table_td), Paragraph("Relational schema tracking asset metadata with persistent host volume mounting.", table_td)],
        [Paragraph("Compute / Host", table_td), Paragraph("AWS EC2 (Ubuntu 24.04)", table_td), Paragraph("Virtual cloud server hosting the entire Docker cluster at <code>http://32.236.11.79</code>.", table_td)],
    ]
    arch_t = Table(arch_data, colWidths=[90, 130, 279])
    arch_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(arch_t)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: FAMILIARIZATION WITH AWS CLOUD SERVICES & IAM
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("FAMILIARIZATION WITH AWS CLOUD SERVICES", section_header))
    story.append(Paragraph(
        "A foundational component of the internship was mastering the AWS Management Console navigation, "
        "Identity and Access Management (IAM), and security isolation principles.",
        body_text
    ))

    story.append(Paragraph("Key Components Mastered:", sub_header))
    story.append(Paragraph("1. <b>AWS Management Console:</b> Unified web-based portal to access, provision, and monitor Amazon Web Services across global geographic regions.", bullet_text))
    story.append(Paragraph("2. <b>Region Selection:</b> Configured compute and storage resources in the Asia Pacific (Sydney) <code>ap-southeast-2</code> region for optimized latency.", bullet_text))
    story.append(Paragraph("3. <b>IAM Identity & Access Management:</b> Created dedicated programmatic service user <code>gallery-app-user</code> with least-privilege security principle.", bullet_text))
    story.append(Paragraph("4. <b>Access Key & Secret Key Generation:</b> Provisioned secure API credentials (<code>AKIA...</code>) enabling server-to-cloud API communications.", bullet_text))
    story.append(Paragraph("5. <b>Security Groups (Stateful Virtual Firewalls):</b> Configured inbound ingress rules controlling network protocols, ports, and allowed IP CIDR ranges.", bullet_text))
    story.append(Paragraph("6. <b>EC2 Instance Connect:</b> Established browser-based SSH terminal sessions directly to the running Linux instance.", bullet_text))

    story.append(Spacer(1, 8))
    story.append(Paragraph("AWS EC2 Inbound Network Security Configuration:", sub_header))

    sg_data = [
        [Paragraph("Type / Protocol", table_th), Paragraph("Port", table_th), Paragraph("Source", table_th), Paragraph("Operational Purpose", table_th)],
        [Paragraph("HTTP (TCP)", table_td), Paragraph("80", table_td), Paragraph("0.0.0.0/0", table_td), Paragraph("Standard Production Web Traffic (Nginx Reverse Proxy)", table_td)],
        [Paragraph("Custom TCP", table_td), Paragraph("3000", table_td), Paragraph("0.0.0.0/0", table_td), Paragraph("React Frontend Development Web Server", table_td)],
        [Paragraph("Custom TCP", table_td), Paragraph("5000", table_td), Paragraph("0.0.0.0/0", table_td), Paragraph("Node.js Express Backend REST API Endpoint", table_td)],
        [Paragraph("SSH (TCP)", table_td), Paragraph("22", table_td), Paragraph("0.0.0.0/0", table_td), Paragraph("Secure Remote Linux Terminal Management", table_td)],
    ]
    sg_t = Table(sg_data, colWidths=[90, 45, 80, 284])
    sg_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(sg_t)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: EXPERIMENT 1 - S3 OBJECT STORAGE & BUCKET POLICIES
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("EXPERIMENT NO. 1: AMAZON S3 CONFIGURATION & POLICIES", section_header))
    
    story.append(Paragraph("<b>1. Aim:</b> To create an Amazon S3 bucket, configure public read access policies, enable Cross-Origin Resource Sharing (CORS), and integrate the AWS SDK for seamless image upload and deletion.", body_text))
    story.append(Paragraph("<b>2. Target S3 Resource:</b> Bucket Name: <code>samriddhabaket1718</code> | Region: <code>ap-southeast-2</code>", body_text))
    
    story.append(Paragraph("<b>3. Step-by-Step Practical Procedure:</b>", sub_header))
    story.append(Paragraph("1. Navigated to <b>Amazon S3 > Buckets > Create bucket</b> in AWS Console.", bullet_text))
    story.append(Paragraph("2. Entered global unique name <code>samriddhabaket1718</code> and disabled Bucket Versioning to eliminate unnecessary storage overhead.", bullet_text))
    story.append(Paragraph("3. Unchecked <b>'Block all public access'</b> and confirmed acknowledgment to permit direct browser retrieval of uploaded images.", bullet_text))
    story.append(Paragraph("4. Applied the following <b>JSON Bucket Policy</b> to grant universal <code>s3:GetObject</code> permissions:", bullet_text))

    policy_code = (
        "{\n"
        '  "Version": "2012-10-17",\n'
        '  "Statement": [{\n'
        '    "Sid": "PublicReadGetObject",\n'
        '    "Effect": "Allow",\n'
        '    "Principal": "*",\n'
        '    "Action": "s3:GetObject",\n'
        '    "Resource": "arn:aws:s3:::samriddhabaket1718/*"\n'
        "  }]\n"
        "}"
    )
    story.append(Paragraph(f"<font face='Courier' size=8 color='#1e1b4b'>{policy_code.replace(chr(10), '<br/>&nbsp;&nbsp;')}</font>", body_text))

    story.append(Paragraph("5. Configured Cross-Origin Resource Sharing (CORS) with allowed methods <code>GET, PUT, POST, DELETE, HEAD</code> and wildcard origin (<code>*</code>).", bullet_text))
    story.append(Paragraph("6. Implemented Node.js streaming upload using <code>PutObjectCommand</code> and atomic deletion with <code>DeleteObjectCommand</code>.", bullet_text))

    story.append(Paragraph("<b>4. Result:</b> Images stream directly into Amazon S3 with low-latency CDN performance, yielding zero server-side disk bloat.", body_text))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: EXPERIMENT 2 - POSTGRESQL & DOCKER ARCHITECTURE
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("EXPERIMENT NO. 2: POSTGRESQL & DOCKER ORCHESTRATION", section_header))

    story.append(Paragraph("<b>1. Aim:</b> To containerize application microservices and configure an automated, persistent PostgreSQL 16 relational database via Docker Compose.", body_text))
    
    story.append(Paragraph("<b>2. Database Schema Design (PostgreSQL):</b>", sub_header))
    story.append(Paragraph(
        "An automated table initialization routine executes on startup, provisioning two core entities:",
        body_text
    ))
    story.append(Paragraph("• <b>Table <code>users</code>:</b> Stores user IDs, unique usernames, Bcrypt hashed passwords, user roles (<code>user</code> vs <code>admin</code>), and registration timestamps.", bullet_text))
    story.append(Paragraph("• <b>Table <code>images</code>:</b> Stores auto-incrementing IDs, image titles, original filenames, public S3 URLs, S3 object keys, uploader names, and upload timestamps.", bullet_text))

    story.append(Paragraph("<b>3. Multi-Container Orchestration (docker-compose.yml):</b>", sub_header))

    docker_data = [
        [Paragraph("Service Name", table_th), Paragraph("Base Image", table_th), Paragraph("Ports", table_th), Paragraph("Configuration & Environmental Roles", table_th)],
        [Paragraph("<b>postgres</b>", table_td), Paragraph("postgres:16-alpine", table_td), Paragraph("5432:5432", table_td), Paragraph("Database engine with persistent volume <code>postgres_data</code> and automated healthchecks.", table_td)],
        [Paragraph("<b>backend</b>", table_td), Paragraph("node:20-alpine", table_td), Paragraph("5000:5000", table_td), Paragraph("Express API connected to internal Docker PostgreSQL network and external AWS S3 API.", table_td)],
        [Paragraph("<b>frontend</b>", table_td), Paragraph("nginx:alpine (multi-stage)", table_td), Paragraph("80:80, 3000:80", table_td), Paragraph("High-performance web server hosting React production build with API reverse proxy.", table_td)],
    ]
    docker_t = Table(docker_data, colWidths=[80, 110, 65, 244])
    docker_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(docker_t)

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>4. Result:</b> Executing <code>sudo docker compose up -d --build</code> builds and starts all three services in isolated, interconnected containers in under 90 seconds.", body_text))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: EXPERIMENT 3 - FULL-STACK CODE IMPLEMENTATION & RBAC
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("EXPERIMENT NO. 3: FULL-STACK DEVELOPMENT & RBAC", section_header))

    story.append(Paragraph("<b>1. Frontend Implementation (React.js + Vite):</b>", sub_header))
    story.append(Paragraph("• <b>Drag-and-Drop Uploader:</b> Developed an interactive upload card with live image thumbnail preview, custom title inputs, and format validation.", bullet_text))
    story.append(Paragraph("• <b>Interactive Masonry Grid:</b> Displays all uploaded images with badges distinguishing S3 cloud assets from local fallback files.", bullet_text))
    story.append(Paragraph("• <b>Lightbox Modal:</b> Full-resolution zoom view with metadata inspection and direct links to original S3 objects.", bullet_text))
    story.append(Paragraph("• <b>Role Switcher & Status Banner:</b> Live chips showing real-time health connectivity for AWS EC2, Amazon S3, and PostgreSQL.", bullet_text))

    story.append(Paragraph("<b>2. Role-Based Access Control (RBAC) Logic:</b>", sub_header))
    story.append(Paragraph(
        "A core project requirement was ensuring that public users can freely upload and view images, "
        "while image deletion is restricted strictly to authorized administrators.",
        body_text
    ))

    rbac_data = [
        [Paragraph("Role", table_th), Paragraph("Upload Permission", table_th), Paragraph("View Permission", table_th), Paragraph("Delete Permission", table_th), Paragraph("Security Mechanism", table_th)],
        [Paragraph("<b>Public User</b>", table_td), Paragraph("ALLOWED", table_td), Paragraph("ALLOWED", table_td), Paragraph("<b>DENIED</b> (Locked)", table_td), Paragraph("Read-only UI; backend returns 403 Forbidden without admin token.", table_td)],
        [Paragraph("<b>Administrator</b>", table_td), Paragraph("ALLOWED", table_td), Paragraph("ALLOWED", table_td), Paragraph("<b>ALLOWED</b> (Active)", table_td), Paragraph("Secured by Bcrypt hashed login and JWT bearer token authorization.", table_td)],
    ]
    rbac_t = Table(rbac_data, colWidths=[75, 75, 75, 85, 189])
    rbac_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(rbac_t)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: EXPERIMENT 4 - AWS EC2 DEPLOYMENT & TESTING
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("EXPERIMENT NO. 4: CLOUD DEPLOYMENT & LIVE VERIFICATION", section_header))

    story.append(Paragraph("<b>1. Deployment Procedure on AWS EC2:</b>", sub_header))
    story.append(Paragraph("1. Launched an AWS EC2 instance running Ubuntu 24.04 LTS with public IPv4 address <code>32.236.11.79</code>.", bullet_text))
    story.append(Paragraph("2. Connected via EC2 Instance Connect browser terminal and installed Docker and Docker Compose:", bullet_text))
    story.append(Paragraph("<code>sudo apt update -y && sudo apt install -y docker.io docker-compose-v2 unzip</code>", bullet_text))
    story.append(Paragraph("3. Downloaded the production application bundle directly from the configured S3 bucket:", bullet_text))
    story.append(Paragraph("<code>curl -sO https://samriddhabaket1718.s3.ap-southeast-2.amazonaws.com/project.zip</code>", bullet_text))
    story.append(Paragraph("4. Unpacked archive and deployed all microservice containers with zero downtime:", bullet_text))
    story.append(Paragraph("<code>sudo docker compose up -d --build</code>", bullet_text))

    story.append(Paragraph("<b>2. Live Operational Verification:</b>", sub_header))
    story.append(Paragraph("• <b>Live Application Endpoint:</b> Verified accessible globally at <b><font color='#2563eb'>http://32.236.11.79</font></b> and port 3000.", bullet_text))
    story.append(Paragraph("• <b>Image Ingestion Verification:</b> Uploaded sample images from browser; binary assets successfully verified within S3 bucket <code>samriddhabaket1718</code>.", bullet_text))
    story.append(Paragraph("• <b>Database State Persistence:</b> PostgreSQL accurately logged image IDs, S3 URLs, and timestamps across container restarts.", bullet_text))
    story.append(Paragraph("• <b>RBAC Deletion Verification:</b> Authenticated as <code>admin</code>; executed deletion test. Asset was simultaneously purged from AWS S3 and deleted from PostgreSQL.", bullet_text))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 10: REAL-WORLD APPLICATIONS & CONCLUSION
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("REAL-WORLD APPLICATIONS & CONCLUSION", section_header))

    story.append(Paragraph("Real-World Applications in Computer Science:", sub_header))
    story.append(Paragraph("1. <b>E-Commerce & Digital Asset Management (DAM):</b> Storing, tagging, and distributing product catalogs and user-submitted review imagery.", bullet_text))
    story.append(Paragraph("2. <b>Social Media Platforms:</b> Scalable media ingestion pipelines with microservice-driven image transformations and CDN delivery.", bullet_text))
    story.append(Paragraph("3. <b>Healthcare & Radiology Repositories:</b> Secure, redundant archiving of diagnostic medical imagery adhering to data durability mandates.", bullet_text))
    story.append(Paragraph("4. <b>Enterprise Cloud Migrations:</b> Modernizing legacy monolithic architectures into decoupled, containerized microservices on AWS.", bullet_text))

    story.append(Paragraph("Internship Learning Outcomes:", sub_header))
    story.append(Paragraph("• Gained practical proficiency in AWS Cloud Infrastructure (S3, EC2, IAM, Security Groups).", bullet_text))
    story.append(Paragraph("• Mastered containerization workflows using Docker and multi-container Docker Compose.", bullet_text))
    story.append(Paragraph("• Developed full-stack proficiency with React.js (Vite), Node.js (Express), and PostgreSQL 16.", bullet_text))
    story.append(Paragraph("• Implemented modern software security principles including RBAC, JWT, and CORS protection.", bullet_text))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Conclusion:", sub_header))
    story.append(Paragraph(
        "The internship on <b>Cloud Computing (Computer Science)</b> provided comprehensive, hands-on exposure to cloud architecture, "
        "containerized deployment, and full-stack software development. The resulting <b>CloudLens</b> project serves as a production-ready, "
        "highly scalable web application demonstrating best practices in cloud computing, security, and DevOps. "
        "The project is fully live, verified, and publicly accessible on AWS EC2 and version-controlled on GitHub.",
        body_text
    ))

    # =========================================================================
    # PAGE 11: EXPERIMENT 5 - WEB APPLICATION USER INTERFACE & INGESTION TIER
    # =========================================================================
    story.append(PageBreak())
    story.append(Spacer(1, 8))
    story.append(Paragraph("EXPERIMENT NO. 5: CLOUD WEB APPLICATION INTERFACE &amp; INGESTION TIER", section_header))
    story.append(Paragraph(
        "The frontend client of <b>CloudLens</b> is engineered using React.js (Vite) and Tailwind CSS, presenting an intuitive, "
        "cloud-synchronized dashboard deployed live on AWS EC2 at <b><font color='#2563eb'>http://32.236.11.79</font></b>. "
        "The annotated interface below details the ingestion subsystem, health monitoring controls, and user navigation.",
        body_text
    ))
    story.append(Spacer(1, 4))
    
    screen1_path = os.path.join(os.path.dirname(__file__), "annotated_screen1.png")
    if os.path.exists(screen1_path):
        story.append(RLImage(screen1_path, width=475, height=251))
        story.append(Spacer(1, 6))

    story.append(Paragraph("UI Component Functional Architecture &amp; Control Reference:", sub_header))

    ui1_data = [
        [Paragraph("Ref", table_th), Paragraph("UI Component / Control", table_th), Paragraph("Cloud Service &amp; Operational Function", table_th)],
        [
            Paragraph("<b><font color='#dc2626'>[1]</font></b>", table_th),
            Paragraph("<b>CloudLens Brand &amp; Architecture Badge</b>", table_td),
            Paragraph("Identifies application branding and verifies cloud-native microservice integration with Amazon S3 object storage and AWS EC2 compute capacity.", table_td)
        ],
        [
            Paragraph("<b><font color='#2563eb'>[2]</font></b>", table_th),
            Paragraph("<b>Role Context Indicator (User Mode)</b>", table_td),
            Paragraph("Displays active authorization context (<code>Upload &amp; View</code>). Guarantees least-privilege security by informing public users that delete privileges are locked.", table_td)
        ],
        [
            Paragraph("<b><font color='#7c3aed'>[3]</font></b>", table_th),
            Paragraph("<b>Admin Login Privilege Escalation Action</b>", table_td),
            Paragraph("Triggers modal dialog requesting JWT credentials (<code>admin</code> / <code>cloudadmin123</code>). Grants role elevation for asset management and deletion.", table_td)
        ],
        [
            Paragraph("<b><font color='#059669'>[4]</font></b>", table_th),
            Paragraph("<b>Multi-Cloud Service Health Monitors</b>", table_td),
            Paragraph("Real-time status indicators tracking the operational connectivity of the AWS EC2 virtual machine, S3 bucket (<code>samriddhabaket1718</code>), and PostgreSQL container.", table_td)
        ],
        [
            Paragraph("<b><font color='#d97706'>[5]</font></b>", table_th),
            Paragraph("<b>Cloud Ingestion Drag &amp; Drop Dropzone</b>", table_td),
            Paragraph("High-performance HTML5 drag-and-drop dropzone supporting PNG, JPG, WEBP, and GIF formats. Streams raw file buffers asynchronously to the Express API.", table_td)
        ],
        [
            Paragraph("<b><font color='#dc2626'>[6]</font></b>", table_th),
            Paragraph("<b>Asset Metadata Parameter Inputs</b>", table_td),
            Paragraph("Form input controls capturing custom <code>Image Title</code> and optional <code>Uploader Name</code>. Attributes are indexed in PostgreSQL alongside the unique S3 Object Key.", table_td)
        ],
    ]
    ui1_t = Table(ui1_data, colWidths=[28, 120, 351])
    ui1_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(ui1_t)

    # =========================================================================
    # PAGE 12: EXPERIMENT 6 - GALLERY REPOSITORY & RBAC INTERFACE
    # =========================================================================
    story.append(PageBreak())
    story.append(Spacer(1, 8))
    story.append(Paragraph("EXPERIMENT NO. 6: ASSET REPOSITORY &amp; ROLE-BASED ACCESS CONTROL (RBAC)", section_header))
    story.append(Paragraph(
        "The gallery and asset inspection tier provides real-time cataloging of persisted images. "
        "It enforces strict Role-Based Access Control (RBAC), allowing unrestricted public inspection while isolating "
        "destructive deletion workflows behind authenticated administrative tokens.",
        body_text
    ))
    story.append(Spacer(1, 4))
    
    screen2_path = os.path.join(os.path.dirname(__file__), "annotated_screen2.png")
    if os.path.exists(screen2_path):
        story.append(RLImage(screen2_path, width=475, height=252))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Gallery &amp; Security Boundary Functional Reference:", sub_header))

    ui2_data = [
        [Paragraph("Ref", table_th), Paragraph("UI Component / Control", table_th), Paragraph("Cloud Service &amp; Operational Function", table_th)],
        [
            Paragraph("<b><font color='#7c3aed'>[1]</font></b>", table_th),
            Paragraph("<b>S3 Ingestion Execution Control (Upload Image)</b>", table_td),
            Paragraph("Transmits the multipart/form-data payload via asynchronous HTTP POST to <code>/api/upload</code>. Streams binary stream directly to Amazon S3 without intermediate disk storage.", table_td)
        ],
        [
            Paragraph("<b><font color='#0284c7'>[2]</font></b>", table_th),
            Paragraph("<b>Persistent Cloud Asset Registry Counter</b>", table_td),
            Paragraph("Displays the real-time total count of indexed assets stored in the S3 bucket (<code>samriddhabaket1718</code>) and queried from the PostgreSQL metadata table.", table_td)
        ],
        [
            Paragraph("<b><font color='#ea580c'>[3]</font></b>", table_th),
            Paragraph("<b>Amazon S3 Cloud Origin Indicator Badge</b>", table_td),
            Paragraph("Visual confirmation tag proving that the rendered media asset originates directly from Amazon S3's globally distributed object storage infrastructure.", table_td)
        ],
        [
            Paragraph("<b><font color='#2563eb'>[4]</font></b>", table_th),
            Paragraph("<b>Cataloged Asset Thumbnail &amp; Metadata Card</b>", table_td),
            Paragraph("Responsive UI card presenting the uploaded image preview, custom title (<code>PIC ME</code>), uploader attribution, and server-generated UTC timestamp.", table_td)
        ],
        [
            Paragraph("<b><font color='#059669'>[5]</font></b>", table_th),
            Paragraph("<b>High-Resolution Lightbox Inspector (View)</b>", table_td),
            Paragraph("Opens an interactive full-screen modal preview displaying the uncompressed image and providing the direct, shareable AWS S3 public CDN/bucket URL.", table_td)
        ],
        [
            Paragraph("<b><font color='#dc2626'>[6]</font></b>", table_th),
            Paragraph("<b>RBAC Deletion Lock Indicator (Admin only)</b>", table_td),
            Paragraph("Enforces strict zero-trust security boundaries. Unauthenticated users cannot delete images; the delete trigger is disabled until an admin JWT session is active.", table_td)
        ],
    ]
    ui2_t = Table(ui2_data, colWidths=[28, 120, 351])
    ui2_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(ui2_t)

    # Build document
    doc.build(story, canvasmaker=BorderedNumberedCanvas)
    print("PDF generated successfully! Size:", os.path.getsize(pdf_path), "bytes")

if __name__ == "__main__":
    create_internship_report()

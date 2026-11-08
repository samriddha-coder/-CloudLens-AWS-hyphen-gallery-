import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 36, "CloudLens: AWS S3 & EC2 Image Gallery — Project Report")
        self.drawRightString(612 - 54, 36, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)
        self.restoreState()

def create_report():
    pdf_path = os.path.join(os.path.dirname(__file__), "CloudLens_Project_Report.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=18
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#1e1b4b'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#334155'),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # Title & Header
    story.append(Paragraph("PROJECT SUBMISSION REPORT", ParagraphStyle('TopBadge', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.HexColor('#4f46e5'), alignment=1, spaceAfter=6)))
    story.append(Paragraph("CloudLens: Cloud-Native Image Gallery", title_style))
    story.append(Paragraph("Full-Stack Enterprise Web Application with AWS S3, EC2, Node.js, React & PostgreSQL", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4f46e5'), spaceBefore=2, spaceAfter=14))

    # Meta Table
    meta_data = [
        [Paragraph("Candidate Name:", table_header_style), Paragraph("<b>Samriddha Das</b>", table_cell_style)],
        [Paragraph("Project Topic:", table_header_style), Paragraph("Cloud-Native Image Gallery using AWS S3, EC2, Node.js, React & PostgreSQL", table_cell_style)],
        [Paragraph("Live Web Application URL:", table_header_style), Paragraph("<b><font color='#2563eb'>http://32.236.11.79</font></b>", table_cell_style)],
        [Paragraph("GitHub Repository:", table_header_style), Paragraph("<b><font color='#2563eb'>https://github.com/samriddha-coder/-CloudLens-AWS-hyphen-gallery-</font></b>", table_cell_style)],
        [Paragraph("Compute Infrastructure:", table_header_style), Paragraph("Amazon Web Services (AWS) EC2 Ubuntu 24.04 LTS (Instance: ap-southeast-2)", table_cell_style)],
        [Paragraph("Object Storage Bucket:", table_header_style), Paragraph("Amazon S3 (Bucket: <code>samriddhabaket1718</code> | Region: ap-southeast-2)", table_cell_style)],
        [Paragraph("Database Service:", table_header_style), Paragraph("PostgreSQL 16 Engine with persistent volume storage (Dockerized)", table_cell_style)],
        [Paragraph("DevOps Orchestration:", table_header_style), Paragraph("Multi-Container Docker & Docker Compose Cluster", table_cell_style)]
    ]
    meta_table = Table(meta_data, colWidths=[150, 354])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "<b>CloudLens</b> is a scalable, cloud-native image repository and management web application built to address modern enterprise requirements for high-durability media storage, role-based security, and microservices architecture. The system enables public visitors to upload and explore media assets while restricting destructive administrative tasks (image deletion) strictly to authenticated administrator accounts. The solution leverages Amazon Web Services (AWS S3 and EC2) alongside Docker orchestration and PostgreSQL to guarantee zero single-point-of-failure and rapid scalability.",
        body_style
    ))

    # 2. Architecture & Tech Stack
    story.append(Paragraph("2. System Architecture & Component Design", h1_style))
    story.append(Paragraph(
        "The project decouples presentation, application business logic, relational metadata, and binary object storage into modular tiers:",
        body_style
    ))

    arch_data = [
        [Paragraph("Component", table_header_style), Paragraph("Technology", table_header_style), Paragraph("Architectural Responsibility", table_header_style)],
        [Paragraph("<b>Frontend UI</b>", table_cell_style), Paragraph("React.js (Vite), CSS3, Lucide Icons", table_cell_style), Paragraph("Single Page Application (SPA), drag-and-drop uploader, real-time preview, lightbox modal & admin authentication.", table_cell_style)],
        [Paragraph("<b>Backend API</b>", table_cell_style), Paragraph("Node.js, Express.js REST API", table_cell_style), Paragraph("Multipart stream processing via Multer memory buffers, JWT verification, and PostgreSQL queries.", table_cell_style)],
        [Paragraph("<b>Object Storage</b>", table_cell_style), Paragraph("Amazon S3 (ap-southeast-2)", table_cell_style), Paragraph("Direct streaming of image assets using <code>@aws-sdk/client-s3</code> with custom bucket and CORS policies.", table_cell_style)],
        [Paragraph("<b>Database</b>", table_cell_style), Paragraph("PostgreSQL 16 Engine", table_cell_style), Paragraph("Relational schema tracking image IDs, original filenames, S3 URLs, uploader identities, and timestamps.", table_cell_style)],
        [Paragraph("<b>Compute / Server</b>", table_cell_style), Paragraph("AWS EC2 (Ubuntu Linux)", table_cell_style), Paragraph("Virtual host in ap-southeast-2 executing all microservice containers with public IPv4 routing.", table_cell_style)],
        [Paragraph("<b>Containerization</b>", table_cell_style), Paragraph("Docker & Docker Compose", table_cell_style), Paragraph("Automated building, isolated networking, volume persistence, and service health monitoring.", table_cell_style)],
    ]
    arch_table = Table(arch_data, colWidths=[90, 130, 284])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 12))

    # 3. Core Functional Modules
    story.append(Paragraph("3. Core Functional Capabilities", h1_style))
    story.append(Paragraph("<b>3.1 Public User Capabilities (Upload & View):</b>", h2_style))
    story.append(Paragraph("• <b>Drag-and-Drop Image Ingestion:</b> Supports high-resolution JPG, PNG, WEBP, GIF, and SVG formats up to 10MB.", bullet_style))
    story.append(Paragraph("• <b>Direct S3 In-Memory Streaming:</b> Files are read directly into server memory buffers and streamed to S3 without writing intermediate files to local disk, saving compute IOPS.", bullet_style))
    story.append(Paragraph("• <b>Responsive Gallery Grid:</b> High-speed interactive grid showing image title, uploader name, format, and timestamp.", bullet_style))
    story.append(Paragraph("• <b>Full-Screen Lightbox Preview:</b> Modal view for high-definition asset inspection with direct links to original S3 objects.", bullet_style))

    story.append(Paragraph("<b>3.2 Administrator Security & RBAC:</b>", h2_style))
    story.append(Paragraph("• <b>Restricted Deletion:</b> Public users observe locked indicator badges. Destructive deletion requires an authorized JWT.", bullet_style))
    story.append(Paragraph("• <b>Admin Modal Authentication:</b> Secured login using Bcrypt password hashing and token expiry.", bullet_style))
    story.append(Paragraph("• <b>Synchronized Two-Phase Deletion:</b> Deleting an asset removes the file from the AWS S3 bucket and prunes metadata from PostgreSQL.", bullet_style))
    story.append(Spacer(1, 10))

    # 4. AWS Cloud Infrastructure Implementation
    story.append(Paragraph("4. AWS Infrastructure & Deployment Configuration", h1_style))
    story.append(Paragraph("<b>4.1 Amazon S3 Bucket Configuration:</b>", h2_style))
    story.append(Paragraph("• <b>Bucket Name:</b> <code>samriddhabaket1718</code> (Region: <code>ap-southeast-2</code>)", bullet_style))
    story.append(Paragraph("• <b>Bucket Policy:</b> Configured with public read permissions (<code>s3:GetObject</code>) allowing global low-latency browser rendering.", bullet_style))
    story.append(Paragraph("• <b>CORS Configuration:</b> Enabled GET, PUT, POST, DELETE, and HEAD verbs for web browser origins.", bullet_style))
    story.append(Paragraph("• <b>IAM Role & Access:</b> Provisioned programmatic IAM credentials bound with <code>AmazonS3FullAccess</code> policy.", bullet_style))

    story.append(Paragraph("<b>4.2 Amazon EC2 Networking & Security Groups:</b>", h2_style))
    story.append(Paragraph("• <b>Virtual Machine:</b> Ubuntu 24.04 LTS instance with allocated Public IPv4 <b>32.236.11.79</b>.", bullet_style))
    story.append(Paragraph("• <b>Inbound Port Rules:</b> Port 80 (HTTP Production Web), Port 3000 (React Frontend Web), Port 5000 (Express REST API), Port 22 (SSH Management).", bullet_style))
    story.append(Spacer(1, 10))

    # 5. Multi-Container Orchestration
    story.append(Paragraph("5. Docker Container Orchestration", h1_style))
    story.append(Paragraph(
        "All application services run as isolated containers within a unified Docker Compose network:",
        body_style
    ))
    story.append(Paragraph("1. <b>gallery_postgres:</b> PostgreSQL 16 Alpine container with host volume mounting for database durability and automated healthchecks.", bullet_style))
    story.append(Paragraph("2. <b>gallery_backend:</b> Node.js runtime connected to the internal Docker PostgreSQL network and the external AWS S3 API.", bullet_style))
    story.append(Paragraph("3. <b>gallery_frontend:</b> Multi-stage Nginx Alpine container serving optimized React production builds with reverse-proxy routing.", bullet_style))
    story.append(Spacer(1, 10))

    # 6. Verification & Conclusion
    story.append(Paragraph("6. Verification Results & Conclusion", h1_style))
    story.append(Paragraph(
        "The application has been thoroughly tested and verified. Live testing confirms that files uploaded from the web browser stream seamlessly to AWS S3, metadata persists in PostgreSQL across container lifecycles, and administrator credentials successfully execute atomic asset deletions. The solution represents a robust, cloud-native software architecture adhering to industry best practices.",
        body_style
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print("CloudLens_Project_Report.pdf generated successfully! Size:", os.path.getsize(pdf_path), "bytes")

if __name__ == "__main__":
    create_report()

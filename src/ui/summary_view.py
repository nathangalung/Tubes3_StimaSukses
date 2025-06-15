"""CV summary dialog"""

from PyQt5 import QtWidgets, QtCore
from database.models import CVSummary, JobHistory, Education

class SummaryView(QtWidgets.QDialog):
    """CV summary dialog"""
    
    def __init__(self, cv_summary: CVSummary = None, parent=None):
        super().__init__(parent)
        self.resume_id = None
        self.setup_ui()
        if cv_summary:
            self.show_summary(cv_summary.name, cv_summary)
    
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("CV Summary")
        self.setModal(True)
        self.resize(700, 800)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        
        # Content widget
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # Action buttons
        buttons = self._create_buttons()
        layout.addWidget(buttons)
    
    def _create_header(self) -> QtWidgets.QWidget:
        """Create header with name"""
        header = QtWidgets.QWidget()
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3498db, stop: 1 #2980b9);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QtWidgets.QHBoxLayout(header)
        
        self.name_label = QtWidgets.QLabel("CV Summary")
        self.name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        layout.addWidget(self.name_label)
        layout.addStretch()
        
        return header
    
    def _create_buttons(self) -> QtWidgets.QWidget:
        """Create action buttons"""
        buttons_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(buttons_widget)
        
        layout.addStretch()
        
        # Close button
        close_btn = QtWidgets.QPushButton("✖ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return buttons_widget
    
    def show_summary(self, resume_id: str, summary: CVSummary):
        """Show CV summary"""
        self.resume_id = resume_id
        
        print(f"displaying summary for {summary.name}")
        print(f"   skills: {len(summary.skills)}")
        print(f"   jobs: {len(summary.job_history)}")
        print(f"   education: {len(summary.education)}")
        
        # Update header
        self.name_label.setText(f"📋 {summary.name}")
        
        # Clear previous content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add sections
        if summary.contact_info:
            self._add_contact_section(summary.contact_info)
        
        if summary.summary:
            self._add_section("💼 Professional Summary", summary.summary)
        
        if summary.skills:
            self._add_skills_section(summary.skills)
        else:
            self._add_section("⚡ Skills", "No skills found")
        
        if summary.job_history:
            self._add_job_history_section(summary.job_history)
        else:
            self._add_section("💼 Work Experience", "No work experience found")
        
        if summary.education:
            self._add_education_section(summary.education)
        else:
            self._add_section("🎓 Education", "No education found")
        
        # Add stretch
        self.content_layout.addStretch()
        
        # Show dialog
        self.show()
    
    def _add_contact_section(self, contact_info: dict):
        """Add contact information section"""
        if not contact_info:
            return
            
        section = QtWidgets.QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #17a2b8;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(section)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QtWidgets.QLabel("📞 Contact Information")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        layout.addWidget(title_label)
        
        # Contact details
        contact_layout = QtWidgets.QHBoxLayout()
        
        if 'email' in contact_info:
            email_label = QtWidgets.QLabel(f"✉️ {contact_info['email']}")
            email_label.setStyleSheet(self._get_contact_style())
            contact_layout.addWidget(email_label)
        
        if 'phone' in contact_info:
            phone_label = QtWidgets.QLabel(f"📱 {contact_info['phone']}")
            phone_label.setStyleSheet(self._get_contact_style())
            contact_layout.addWidget(phone_label)
        
        if 'address' in contact_info:
            address_label = QtWidgets.QLabel(f"📍 {contact_info['address']}")
            address_label.setStyleSheet(self._get_contact_style())
            contact_layout.addWidget(address_label)
        
        contact_layout.addStretch()
        layout.addLayout(contact_layout)
        
        self.content_layout.addWidget(section)
    
    def _get_contact_style(self):
        """Get contact item style"""
        return """
            QLabel {
                font-size: 12px;
                color: #495057;
                background-color: white;
                padding: 6px 10px;
                border-radius: 15px;
                margin: 2px;
            }
        """
    
    def _add_section(self, title: str, content: str):
        """Add general section"""
        section = QtWidgets.QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #3498db;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(section)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        layout.addWidget(title_label)
        
        # Content
        content_label = QtWidgets.QLabel(content)
        content_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #495057;
                background-color: transparent;
                padding: 5px 0;
            }
        """)
        content_label.setWordWrap(True)
        layout.addWidget(content_label)
        
        self.content_layout.addWidget(section)
    
    def _add_skills_section(self, skills: list):
        """Add skills section - show all skills without truncation"""
        section = QtWidgets.QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #e8f5e8;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #28a745;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(section)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QtWidgets.QLabel(f"⚡ Skills ({len(skills)} items)")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        layout.addWidget(title_label)
        
        # Skills container with flow layout
        skills_container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(skills_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)
        
        # Show ALL skills in rows of 6
        colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6f42c1']
        skills_per_row = 6
        
        for start_idx in range(0, len(skills), skills_per_row):
            # Create row widget
            row_widget = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            
            # Add skills for this row
            end_idx = min(start_idx + skills_per_row, len(skills))
            for i in range(start_idx, end_idx):
                skill = skills[i]
                skill_tag = QtWidgets.QLabel(skill)
                color = colors[i % len(colors)]
                skill_tag.setStyleSheet(f"""
                    QLabel {{
                        background-color: {color};
                        color: white;
                        padding: 6px 12px;
                        border-radius: 15px;
                        font-size: 11px;
                        font-weight: bold;
                        margin: 2px;
                    }}
                """)
                skill_tag.setAlignment(QtCore.Qt.AlignCenter)
                row_layout.addWidget(skill_tag)
            
            # Add stretch to left-align skills
            row_layout.addStretch()
            
            # Add row to container
            container_layout.addWidget(row_widget)
        
        layout.addWidget(skills_container)
        self.content_layout.addWidget(section)
    
    def _add_job_history_section(self, job_history: list):
        """Add job history section"""
        section = QtWidgets.QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #fff8e1;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #ff9800;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QtWidgets.QLabel(f"💼 Work Experience ({len(job_history)} positions)")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        layout.addWidget(title_label)
        
        # Job entries
        for i, job in enumerate(job_history):
            job_widget = self._create_job_entry(job, i + 1)
            layout.addWidget(job_widget)
        
        self.content_layout.addWidget(section)
    
    def _create_job_entry(self, job: JobHistory, index: int) -> QtWidgets.QWidget:
        """Create job entry widget"""
        job_widget = QtWidgets.QWidget()
        job_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
                padding: 12px;
                border: 1px solid #e9ecef;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(job_widget)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Job header
        header_layout = QtWidgets.QHBoxLayout()
        
        # Position
        position_label = QtWidgets.QLabel(f"{index}. {job.position}")
        position_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        header_layout.addWidget(position_label)
        
        # Date range
        if job.start_date or job.end_date:
            date_range = f"{job.start_date or 'N/A'} - {job.end_date or 'Present'}"
            date_label = QtWidgets.QLabel(date_range)
            date_label.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #6c757d;
                    background-color: #f8f9fa;
                    padding: 2px 8px;
                    border-radius: 10px;
                }
            """)
            header_layout.addWidget(date_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Company (only show if not unknown/empty)
        if (job.company and 
            job.company.lower() not in ['unknown company', 'unknown', 'n/a', 'na'] and
            job.company.strip()):
            company_label = QtWidgets.QLabel(f"🏢 {job.company}")
            company_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #495057;
                    background-color: transparent;
                    margin-left: 10px;
                }
            """)
            layout.addWidget(company_label)
        
        # Description
        if job.description and len(job.description.strip()) > 10:
            desc_label = QtWidgets.QLabel(f"📝 {job.description}")
            desc_label.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #6c757d;
                    background-color: transparent;
                    margin-left: 10px;
                    font-style: italic;
                }
            """)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        return job_widget
    
    def _add_education_section(self, education: list):
        """Add education section"""
        section = QtWidgets.QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #e3f2fd;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #2196f3;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QtWidgets.QLabel(f"🎓 Education ({len(education)} entries)")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        layout.addWidget(title_label)
        
        # Education entries
        for i, edu in enumerate(education):
            edu_widget = self._create_education_entry(edu, i + 1)
            layout.addWidget(edu_widget)
        
        self.content_layout.addWidget(section)
    
    def _create_education_entry(self, edu: Education, index: int) -> QtWidgets.QWidget:
        """Create education entry widget"""
        edu_widget = QtWidgets.QWidget()
        edu_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
                padding: 12px;
                border: 1px solid #e9ecef;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(edu_widget)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Education header
        header_layout = QtWidgets.QHBoxLayout()
        
        # Degree
        degree_label = QtWidgets.QLabel(f"{index}. {edu.degree}")
        degree_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        header_layout.addWidget(degree_label)
        
        # Graduation year (fixed attribute name)
        if edu.graduation_year:
            year_label = QtWidgets.QLabel(edu.graduation_year)
            year_label.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #6c757d;
                    background-color: #f8f9fa;
                    padding: 2px 8px;
                    border-radius: 10px;
                }
            """)
            header_layout.addWidget(year_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Institution
        institution_label = QtWidgets.QLabel(f"🏫 {edu.institution}")
        institution_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #495057;
                background-color: transparent;
                margin-left: 10px;
            }
        """)
        layout.addWidget(institution_label)
        
        # GPA if available
        if edu.gpa:
            gpa_label = QtWidgets.QLabel(f"📊 GPA: {edu.gpa}")
            gpa_label.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #6c757d;
                    background-color: transparent;
                    margin-left: 10px;
                    font-style: italic;
                }
            """)
            layout.addWidget(gpa_label)
        
        return edu_widget
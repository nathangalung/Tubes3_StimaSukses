"""Search panel for keyword input"""

from PyQt5 import QtWidgets, QtCore
import re

class SearchPanel(QtWidgets.QWidget):
    """Search panel widget"""
    
    search_requested = QtCore.pyqtSignal(dict)
    algorithm_changed = QtCore.pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_presets()
    
    def setup_ui(self):
        """Setup user interface"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Panel title
        title = QtWidgets.QLabel("🔍 CV Search")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
        """)
        layout.addWidget(title)
        
        # Keywords section
        self.create_keywords_section(layout)
        
        # Algorithm selection
        self.create_algorithm_section(layout)
        
        # Parameters section
        self.create_parameters_section(layout)
        
        # Search button
        self.create_search_button(layout)
        
        # Presets section
        self.create_presets_section(layout)
        
        layout.addStretch()
        
        # Apply panel styling
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-right: 1px solid #dee2e6;
            }
        """)
        
        self.setFixedWidth(400)
    
    def create_keywords_section(self, layout):
        """Create keywords input section"""
        keywords_group = QtWidgets.QGroupBox("Keywords")
        keywords_group.setStyleSheet(self.get_group_style())
        keywords_layout = QtWidgets.QVBoxLayout(keywords_group)
        
        # Keywords input
        self.keywords_input = QtWidgets.QTextEdit()
        self.keywords_input.setPlaceholderText(
            "Enter keywords separated by commas...\n\n"
            "Examples:\n"
            "• Python, SQL, Machine Learning\n"
            "• React, JavaScript, Node.js\n"
            "• Accounting, Excel, Finance"
        )
        self.keywords_input.setMaximumHeight(120)
        self.keywords_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
        """)
        keywords_layout.addWidget(self.keywords_input)
        
        # Keywords validation label
        self.keywords_validation = QtWidgets.QLabel("")
        self.keywords_validation.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 12px;
                padding: 2px 0;
            }
        """)
        self.keywords_validation.hide()
        keywords_layout.addWidget(self.keywords_validation)
        
        layout.addWidget(keywords_group)
    
    def create_algorithm_section(self, layout):
        """Create algorithm selection section"""
        algo_group = QtWidgets.QGroupBox("Algorithm")
        algo_group.setStyleSheet(self.get_group_style())
        algo_layout = QtWidgets.QVBoxLayout(algo_group)
        
        # Algorithm radio buttons
        self.algorithm_buttons = {}
        algorithms = [
            ("KMP", "Knuth-Morris-Pratt - General purpose"),
            ("BM", "Boyer-Moore - Long patterns"),
            ("AC", "Aho-Corasick - Multiple keywords"),
            ("LEVENSHTEIN", "Levenshtein - Fuzzy matching")
        ]
        
        for algo_code, description in algorithms:
            radio = QtWidgets.QRadioButton(description)
            radio.setStyleSheet("""
                QRadioButton {
                    font-size: 13px;
                    padding: 5px 0;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            
            if algo_code == "KMP":
                radio.setChecked(True)
            
            radio.toggled.connect(
                lambda checked, code=algo_code: 
                self.algorithm_changed.emit(code) if checked else None
            )
            
            self.algorithm_buttons[algo_code] = radio
            algo_layout.addWidget(radio)
        
        layout.addWidget(algo_group)
    
    def create_parameters_section(self, layout):
        """Create search parameters section"""
        params_group = QtWidgets.QGroupBox("Parameters")
        params_group.setStyleSheet(self.get_group_style())
        params_layout = QtWidgets.QFormLayout(params_group)
        
        # Top N results
        self.top_n_spin = QtWidgets.QSpinBox()
        self.top_n_spin.setRange(1, 50)
        self.top_n_spin.setValue(10)
        self.top_n_spin.setStyleSheet(self.get_input_style())
        params_layout.addRow("Max Results:", self.top_n_spin)
        
        # Fuzzy threshold
        self.fuzzy_threshold_spin = QtWidgets.QDoubleSpinBox()
        self.fuzzy_threshold_spin.setRange(0.1, 1.0)
        self.fuzzy_threshold_spin.setSingleStep(0.1)
        self.fuzzy_threshold_spin.setValue(0.7)
        self.fuzzy_threshold_spin.setStyleSheet(self.get_input_style())
        params_layout.addRow("Fuzzy Threshold:", self.fuzzy_threshold_spin)
        
        layout.addWidget(params_group)
    
    def create_search_button(self, layout):
        """Create search button"""
        self.search_button = QtWidgets.QPushButton("🔍 Search CVs")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.search_button.clicked.connect(self.perform_search)
        layout.addWidget(self.search_button)
    
    def create_presets_section(self, layout):
        """Create keyword presets section"""
        presets_group = QtWidgets.QGroupBox("Quick Presets")
        presets_group.setStyleSheet(self.get_group_style())
        presets_layout = QtWidgets.QVBoxLayout(presets_group)
        
        # Create preset buttons
        self.preset_buttons = []
        presets = [
            ("💻 IT Skills", "Python, Java, SQL, React, Machine Learning"),
            ("💼 Finance", "Accounting, Excel, Financial Analysis, Budget"),
            ("🏗️ Engineering", "AutoCAD, Project Management, Quality Control"),
            ("🏥 Healthcare", "Patient Care, Medical Records, Clinical"),
            ("📊 Data Science", "Python, R, Statistics, Analytics, Visualization")
        ]
        
        for name, keywords in presets:
            btn = QtWidgets.QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 8px 12px;
                    border-radius: 4px;
                    text-align: left;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #3498db;
                }
            """)
            btn.clicked.connect(lambda checked, kw=keywords: self.load_preset(kw))
            presets_layout.addWidget(btn)
            self.preset_buttons.append(btn)
        
        layout.addWidget(presets_group)
    
    def get_group_style(self):
        """Get group box style"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
        """
    
    def get_input_style(self):
        """Get input field style"""
        return """
            QSpinBox, QDoubleSpinBox {
                border: 2px solid #e9ecef;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                background-color: white;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #3498db;
            }
        """
    
    def load_preset(self, keywords):
        """Load keyword preset"""
        self.keywords_input.setText(keywords)
        self.validate_keywords()
    
    def load_presets(self):
        """Load saved presets"""
        # Could load from settings file
        pass
    
    def get_selected_algorithm(self):
        """Get selected algorithm"""
        for algo, button in self.algorithm_buttons.items():
            if button.isChecked():
                return algo
        return "KMP"
    
    def validate_keywords(self):
        """Validate keywords input"""
        text = self.keywords_input.toPlainText().strip()
        
        if not text:
            self.keywords_validation.setText("❌ Keywords are required")
            self.keywords_validation.show()
            return False
        
        # Parse keywords
        keywords = [kw.strip() for kw in re.split(r'[,\n]', text) if kw.strip()]
        
        if len(keywords) == 0:
            self.keywords_validation.setText("❌ Enter at least one keyword")
            self.keywords_validation.show()
            return False
        
        if len(keywords) > 20:
            self.keywords_validation.setText("❌ Maximum 20 keywords allowed")
            self.keywords_validation.show()
            return False
        
        self.keywords_validation.hide()
        return True
    
    def perform_search(self):
        """Perform search with validation"""
        if not self.validate_keywords():
            return
        
        # Get keywords
        text = self.keywords_input.toPlainText().strip()
        keywords = [kw.strip() for kw in re.split(r'[,\n]', text) if kw.strip()]
        
        # Get parameters
        search_params = {
            'keywords': keywords,
            'algorithm': self.get_selected_algorithm(),
            'top_n': self.top_n_spin.value(),
            'fuzzy_threshold': self.fuzzy_threshold_spin.value()
        }
        
        # Emit signal
        self.search_requested.emit(search_params)
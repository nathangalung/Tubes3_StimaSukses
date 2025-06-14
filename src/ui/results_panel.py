"""Results display panel"""

from PyQt5 import QtWidgets, QtCore, QtGui
from typing import List
from database.models import SearchResult

class ResultsPanel(QtWidgets.QWidget):
    """Results display panel"""
    
    summary_requested = QtCore.pyqtSignal(str)
    view_cv_requested = QtCore.pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user interface"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Results header
        self.results_header = QtWidgets.QLabel("Search Results")
        self.results_header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        self.results_header.hide()
        layout.addWidget(self.results_header)
        
        # Scroll area
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Container widget
        self.results_widget = QtWidgets.QWidget()
        self.results_layout = QtWidgets.QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(10)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area)
        
        # Initial message
        self.show_welcome_message()
        
        # Set background
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)
    
    def show_welcome_message(self):
        """Show welcome message"""
        self.clear_results()
        
        welcome_widget = QtWidgets.QWidget()
        welcome_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
                padding: 40px;
                border: 2px dashed #dee2e6;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(welcome_widget)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Icon
        icon_label = QtWidgets.QLabel("🔍")
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                background-color: transparent;
            }
        """)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QtWidgets.QLabel("ATS CV Search")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QtWidgets.QLabel(
            "Enter keywords in the search panel to find matching CVs\n"
            "using advanced pattern matching algorithms"
        )
        desc_label.setAlignment(QtCore.Qt.AlignCenter)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                background-color: transparent;
                line-height: 1.5;
            }
        """)
        layout.addWidget(desc_label)
        
        self.results_layout.addWidget(welcome_widget)
        self.results_layout.addStretch()
    
    def show_loading(self, message: str = "Searching..."):
        """Show loading message"""
        self.clear_results()
        
        loading_widget = QtWidgets.QWidget()
        loading_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
                padding: 40px;
                border: 1px solid #dee2e6;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(loading_widget)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Loading icon
        loading_label = QtWidgets.QLabel("⏳")
        loading_label.setAlignment(QtCore.Qt.AlignCenter)
        loading_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                background-color: transparent;
            }
        """)
        layout.addWidget(loading_label)
        
        # Loading message
        message_label = QtWidgets.QLabel(message)
        message_label.setAlignment(QtCore.Qt.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #3498db;
                background-color: transparent;
            }
        """)
        layout.addWidget(message_label)
        
        self.results_layout.addWidget(loading_widget)
        self.results_layout.addStretch()
    
    def show_search_results(self, results: List[SearchResult], timing_info: str):
        """Show search results"""
        self.clear_results()
        
        if not results:
            self.show_no_results()
            return
        
        # Results header
        self.results_header.setText(f"🎯 Found {len(results)} matching CVs")
        self.results_header.show()
        
        # Results cards
        for result in results:
            card = self._create_result_card(result)
            self.results_layout.addWidget(card)
        
        # Timing info
        if timing_info:
            timing_widget = self._create_timing_widget(timing_info)
            self.results_layout.addWidget(timing_widget)
        
        self.results_layout.addStretch()
    
    def show_no_results(self):
        """Show no results message"""
        no_results_widget = QtWidgets.QWidget()
        no_results_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
                padding: 40px;
                border: 1px solid #ffc107;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(no_results_widget)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Icon
        icon_label = QtWidgets.QLabel("❌")
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                background-color: transparent;
            }
        """)
        layout.addWidget(icon_label)
        
        # Message
        message_label = QtWidgets.QLabel("No matching CVs found")
        message_label.setAlignment(QtCore.Qt.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #e67e22;
                background-color: transparent;
            }
        """)
        layout.addWidget(message_label)
        
        # Suggestions
        suggestions_label = QtWidgets.QLabel(
            "Try using different keywords or enable fuzzy matching"
        )
        suggestions_label.setAlignment(QtCore.Qt.AlignCenter)
        suggestions_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                background-color: transparent;
            }
        """)
        layout.addWidget(suggestions_label)
        
        self.results_layout.addWidget(no_results_widget)
        self.results_layout.addStretch()
    
    def _create_result_card(self, result: SearchResult) -> QtWidgets.QWidget:
        """Create result card"""
        card = QtWidgets.QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #dee2e6;
                padding: 15px;
            }
            QWidget:hover {
                border-color: #3498db;
                box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QtWidgets.QHBoxLayout()
        
        # Resume ID and category
        id_label = QtWidgets.QLabel(f"📄 {result.resume.id}")
        id_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
        """)
        header_layout.addWidget(id_label)
        
        # Category badge
        category_label = QtWidgets.QLabel(result.resume.category)
        category_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(category_label)
        
        # Algorithm used
        algo_label = QtWidgets.QLabel(f"🔍 {result.algorithm_used}")
        algo_label.setStyleSheet("""
            QLabel {
                background-color: #28a745;
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(algo_label)
        
        header_layout.addStretch()
        
        # Relevance score
        score_label = QtWidgets.QLabel(f"⭐ {result.relevance_score:.1f}")
        score_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #f39c12;
                background-color: transparent;
            }
        """)
        header_layout.addWidget(score_label)
        
        layout.addLayout(header_layout)
        
        # Candidate info
        if result.resume.name and result.resume.name != "Unknown":
            name_label = QtWidgets.QLabel(f"👤 {result.resume.name}")
            name_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #495057;
                    background-color: transparent;
                }
            """)
            layout.addWidget(name_label)
        
        # Matched keywords
        keywords_layout = QtWidgets.QHBoxLayout()
        keywords_layout.setSpacing(5)
        
        keywords_label = QtWidgets.QLabel("Keywords:")
        keywords_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6c757d;
                background-color: transparent;
            }
        """)
        keywords_layout.addWidget(keywords_label)
        
        # Show first 5 keywords
        for i, keyword in enumerate(result.matched_keywords[:5]):
            count = result.keyword_matches.get(keyword, 0)
            keyword_badge = QtWidgets.QLabel(f"{keyword} ({count})")
            
            # Color based on fuzzy/exact
            if "(fuzzy)" in keyword:
                bg_color = "#ffc107"
            else:
                bg_color = "#28a745"
            
            keyword_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color};
                    color: white;
                    padding: 2px 6px;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """)
            keywords_layout.addWidget(keyword_badge)
        
        # More keywords indicator
        if len(result.matched_keywords) > 5:
            more_label = QtWidgets.QLabel(f"+{len(result.matched_keywords) - 5} more")
            more_label.setStyleSheet("""
                QLabel {
                    font-size: 10px;
                    color: #6c757d;
                    background-color: transparent;
                    font-style: italic;
                }
            """)
            keywords_layout.addWidget(more_label)
        
        keywords_layout.addStretch()
        layout.addLayout(keywords_layout)
        
        # Action buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        
        # Summary button
        summary_btn = QtWidgets.QPushButton("📋 View Summary")
        summary_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        summary_btn.clicked.connect(
            lambda: self.summary_requested.emit(result.resume.id)
        )
        buttons_layout.addWidget(summary_btn)
        
        # View CV button
        view_btn = QtWidgets.QPushButton("📄 Open CV")
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        view_btn.clicked.connect(
            lambda: self.view_cv_requested.emit(result.resume.id)
        )
        buttons_layout.addWidget(view_btn)
        
        buttons_layout.addStretch()
        
        # Total matches
        matches_label = QtWidgets.QLabel(f"Total matches: {result.total_matches}")
        matches_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6c757d;
                background-color: transparent;
            }
        """)
        buttons_layout.addWidget(matches_label)
        
        layout.addLayout(buttons_layout)
        
        return card
    
    def _create_timing_widget(self, timing_info: str) -> QtWidgets.QWidget:
        """Create timing info widget"""
        timing_widget = QtWidgets.QWidget()
        timing_widget.setStyleSheet("""
            QWidget {
                background-color: #e9ecef;
                border-radius: 6px;
                padding: 10px;
                border-left: 3px solid #6c757d;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(timing_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        timing_label = QtWidgets.QLabel(timing_info)
        timing_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #495057;
                background-color: transparent;
                font-family: monospace;
            }
        """)
        layout.addWidget(timing_label)
        
        return timing_widget
    
    def clear_results(self):
        """Clear all results"""
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.results_header.hide()
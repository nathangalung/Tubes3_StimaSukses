"""Main application window"""

from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import os
from ui.search_panel import SearchPanel
from ui.results_panel import ResultsPanel
from ui.summary_view import SummaryView
from controller.search import SearchController
from controller.cv import CVController

class MainWindow(QtWidgets.QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.search_controller = SearchController()
        self.cv_controller = CVController()
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("ATS CV Search - Pattern Matching System")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Set application icon
        self.setWindowIcon(QtGui.QIcon("assets/icon.png") if os.path.exists("assets/icon.png") else QtGui.QIcon())
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create panels
        self.search_panel = SearchPanel()
        self.results_panel = ResultsPanel()
        
        # Add panels to layout
        main_layout.addWidget(self.search_panel, 1)
        main_layout.addWidget(self.results_panel, 2)
        
        # Apply styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
        """)
        
        # Create status bar
        self.create_status_bar()
        
        # Create menu bar
        self.create_menu_bar()
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Enter keywords to search CVs")
        
        # Add permanent widgets
        self.algorithm_label = QtWidgets.QLabel("Algorithm: KMP")
        self.algorithm_label.setStyleSheet("padding: 5px; color: #6c757d;")
        self.status_bar.addPermanentWidget(self.algorithm_label)
        
        self.progress_label = QtWidgets.QLabel("")
        self.progress_label.setStyleSheet("padding: 5px; color: #28a745;")
        self.status_bar.addPermanentWidget(self.progress_label)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Database menu
        database_menu = menubar.addMenu("Database")
        
        database_stats_action = QtWidgets.QAction("Show Statistics", self)
        database_stats_action.triggered.connect(self.show_database_stats)
        database_menu.addAction(database_stats_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QtWidgets.QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        algorithm_help_action = QtWidgets.QAction("Algorithm Info", self)
        algorithm_help_action.triggered.connect(self.show_algorithm_info)
        help_menu.addAction(algorithm_help_action)
    
    def connect_signals(self):
        """Connect signals and slots"""
        # Search panel signals
        self.search_panel.search_requested.connect(self.perform_search)
        self.search_panel.algorithm_changed.connect(self.update_algorithm_display)
        
        # Results panel signals
        self.results_panel.summary_requested.connect(self.show_cv_summary)
        self.results_panel.view_cv_requested.connect(self.open_cv_file)
        
        # Set progress callback
        self.search_controller.set_progress_callback(self.update_progress)
    
    def perform_search(self, search_params):
        """Perform CV search"""
        keywords = search_params['keywords']
        algorithm = search_params['algorithm']
        top_n = search_params['top_n']
        fuzzy_threshold = search_params['fuzzy_threshold']
        
        print(f"🔍 Starting search: {keywords} using {algorithm}")
        
        # Update status
        self.status_bar.showMessage("Searching CVs...")
        self.results_panel.show_loading(f"Searching with {algorithm}...")
        
        # Process events to update UI
        QtWidgets.QApplication.processEvents()
        
        try:
            # Perform search
            results, timing_info = self.search_controller.search_cvs(
                keywords=keywords,
                algorithm=algorithm,
                top_n=top_n,
                fuzzy_threshold=fuzzy_threshold
            )
            
            # Show results
            self.results_panel.show_search_results(results, timing_info)
            
            # Update status
            result_count = len(results)
            self.status_bar.showMessage(f"Found {result_count} matching CVs")
            
            print(f"✅ Search completed: {result_count} results")
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            self.show_error(f"Search failed: {str(e)}")
            self.status_bar.showMessage("Search failed")
    
    def show_cv_summary(self, resume_id):
        """Show CV summary dialog"""
        try:
            print(f"📋 Showing summary for {resume_id}")
            
            # Get CV summary
            cv_summary = self.cv_controller.get_cv_summary(resume_id)
            if not cv_summary:
                self.show_error(f"Failed to generate summary for {resume_id}")
                return
            
            # Show summary dialog
            summary_dialog = SummaryView(cv_summary, self)
            summary_dialog.exec_()
            
        except Exception as e:
            print(f"❌ Summary failed: {e}")
            self.show_error(f"Failed to show summary: {str(e)}")
    
    def open_cv_file(self, resume_id):
        """Open CV file"""
        try:
            print(f"📄 Opening CV file for {resume_id}")
            
            success = self.cv_controller.open_cv_file(resume_id)
            if success:
                self.status_bar.showMessage(f"Opened CV for {resume_id}")
            else:
                self.show_error(f"Failed to open CV file for {resume_id}")
                
        except Exception as e:
            print(f"❌ Open CV failed: {e}")
            self.show_error(f"Failed to open CV: {str(e)}")
    
    def update_algorithm_display(self, algorithm):
        """Update algorithm display"""
        self.algorithm_label.setText(f"Algorithm: {algorithm}")
    
    def update_progress(self, message):
        """Update progress display"""
        self.progress_label.setText(message)
        QtWidgets.QApplication.processEvents()
    
    def show_database_stats(self):
        """Show database statistics"""
        try:
            stats = self.search_controller.repo.get_database_stats()
            
            stats_text = f"""
Database Statistics:

Total Applicants: {stats.get('total_applicants', 0)}
Total Applications: {stats.get('total_applications', 0)}

Top Application Roles:
"""
            
            for role, count in stats.get('top_roles', []):
                stats_text += f"  • {role}: {count}\n"
            
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Database Statistics")
            msg_box.setText(stats_text)
            msg_box.exec_()
            
        except Exception as e:
            self.show_error(f"Failed to get database stats: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
ATS CV Search Application
Version 1.0

Tugas Besar 3 IF2211 Strategi Algoritma
Institut Teknologi Bandung

Pattern Matching Algorithms:
• Knuth-Morris-Pratt (KMP)
• Boyer-Moore (BM) 
• Aho-Corasick (AC)
• Levenshtein Distance

Authors: Tim Stima Sukses
        """
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("About ATS CV Search")
        msg_box.setText(about_text)
        msg_box.exec_()
    
    def show_algorithm_info(self):
        """Show algorithm information"""
        algo_info = """
Algorithm Performance Guide:

KMP (Knuth-Morris-Pratt):
• Best for: Single keyword searches
• Complexity: O(n + m)
• Recommended: General purpose

Boyer-Moore:
• Best for: Long keywords (>3 chars)
• Complexity: O(nm) worst case
• Recommended: Large pattern searches

Aho-Corasick:
• Best for: Multiple keywords
• Complexity: O(n + m + z)
• Recommended: Many keywords at once

Levenshtein Distance:
• Best for: Fuzzy matching
• Complexity: O(n × m)
• Recommended: Typo tolerance
        """
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Algorithm Information")
        msg_box.setText(algo_info)
        msg_box.exec_()
    
    def show_error(self, message):
        """Show error message"""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec_()
    
    def closeEvent(self, event):
        """Handle close event"""
        reply = QtWidgets.QMessageBox.question(
            self, 
            'Confirm Exit',
            'Are you sure you want to exit?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            print("👋 Closing ATS CV Search Application")
            event.accept()
        else:
            event.ignore()
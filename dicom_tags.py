from PyQt5.QtWidgets import QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QHBoxLayout, QApplication, QMessageBox, QDialog, QComboBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
import os
from dicom_display import display_tags 
import warnings
from pydicom import config

warnings.filterwarnings('ignore', category=UserWarning, module='pydicom.valuerep')
config.convert_wrong_values = True

class TagLoaderThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, tag_info):
        super().__init__()
        self.tag_info = tag_info
        self.chunk_size = 50

    def run(self):
        lines = self.tag_info.split('\n')
        for i in range(0, len(lines), self.chunk_size):
            chunk = '\n'.join(lines[i:i + self.chunk_size])
            self.progress.emit(chunk)
        self.finished.emit()

class TagViewerWindow(QMainWindow):
    def __init__(self, tag_info, dicom_dataset=None):
        super().__init__()
        self.tag_info = tag_info
        self.dicom_dataset = dicom_dataset
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.initUI()

   

    def initUI(self):
        self.setWindowTitle('DICOM Tags')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        search_frame = QHBoxLayout()
        search_label = QLabel('Search Tag:')
        self.search_entry = QLineEdit()
        search_button = QPushButton('Search')
        next_button = QPushButton('Next')

        search_frame.addWidget(search_label)
        search_frame.addWidget(self.search_entry)
        search_frame.addWidget(search_button)
        search_frame.addWidget(next_button)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        layout.addLayout(search_frame)
        layout.addWidget(self.text_edit)

        edit_frame = QHBoxLayout()
        save_button = QPushButton('Save Changes')
        # swap_button = QPushButton('Swap Tags')
        
        edit_frame.addWidget(save_button)
        # edit_frame.addWidget(swap_button)
        layout.addLayout(edit_frame)

        search_button.clicked.connect(self.search)
        next_button.clicked.connect(self.find_next)
        self.search_entry.returnPressed.connect(self.search)

        save_button.clicked.connect(self.save_current_changes)
        # swap_button.clicked.connect(self.show_swap_dialog)

        self.loader_thread = TagLoaderThread(self.tag_info)
        self.loader_thread.progress.connect(self.append_text)
        self.loader_thread.finished.connect(self.loading_finished)
        self.loader_thread.start()

    def append_text(self, text):
        self.text_edit.append(text)

    def loading_finished(self):
        print("Tag loading completed")

    def search(self):
        search_term = self.search_entry.text().strip().lower()
        if not search_term:
            return

        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.Start)
        self.text_edit.setTextCursor(cursor)

        format = self.text_edit.currentCharFormat()
        format.setBackground(Qt.white)
        cursor.select(cursor.Document)
        cursor.mergeCharFormat(format)

        while self.text_edit.find(search_term):
            format = self.text_edit.currentCharFormat()
            format.setBackground(Qt.yellow)
            self.text_edit.mergeCurrentCharFormat(format)

    def find_next(self):
        search_term = self.search_entry.text().strip().lower()
        if not search_term:
            return
        
        self.text_edit.find(search_term)

    
        
    # def show_swap_dialog(self):
    #     dialog = TagSwapDialog(self.dicom_dataset, self.text_edit, self)  # Pass text_edit
    #     dialog.exec_()
    #     if dialog.swapped:
    #         self.text_edit.clear()
    #         self.loader_thread = TagLoaderThread(display_tags(self.dicom_dataset))
    #         self.loader_thread.progress.connect(self.append_text)
    #         self.loader_thread.start()

    def save_current_changes(self, *args):
        """Wrapper method to handle saving changes from the text editor"""
        try:
            current_text = self.text_edit.toPlainText()
            changes_made = False
            
            # Parse the current text to find modified tags
            for line in current_text.split('\n'):
                if ': ' in line:
                    tag_name, value = line.split(': ', 1)
                    # Find the tag in the dataset
                    for elem in self.dicom_dataset:
                        if elem.name == tag_name:
                            # Only try to save if the value is different
                            if str(elem.repval) != value:
                                try:
                                    # Directly modify the value
                                    vr = elem.VR
                                    cleaned_value = value.strip()
                                    while cleaned_value.startswith(("'", '"')) and cleaned_value.endswith(("'", '"')):
                                        cleaned_value = cleaned_value[1:-1].strip()
                                    
                                    if vr in ['DS', 'FL', 'FD']:  # Float types
                                        elem.value = float(cleaned_value.replace(',', '.'))
                                    elif vr in ['IS']:  # Integer types
                                        elem.value = int(cleaned_value.split('.')[0])
                                    elif elem.tag == (0x0028, 0x0006):  # Planar Configuration
                                        elem.value = int(cleaned_value)  # Ensure it's an integer
                                    else:
                                        elem.value = cleaned_value
                                
                                    changes_made = True
                                except Exception as e:
                                    QMessageBox.critical(self, "Error", 
                                        f"Failed to save value for {tag_name}: {str(e)}")
                            break

            if changes_made:
                # Save the modified dataset
                original_path = self.dicom_dataset.filename
                save_path = os.path.join(os.path.dirname(original_path), 
                                       f"modified_{os.path.basename(original_path)}")
                self.dicom_dataset.save_as(save_path)
                QMessageBox.information(self, "Success", 
                    f"Changes saved successfully!\nFile saved to:\n{save_path}")
            else:
                QMessageBox.information(self, "Info", "No changes detected")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")
    
# class TagSwapDialog(QDialog):
#     def __init__(self, dicom_dataset, text_edit, parent=None):
#         super().__init__(parent)
#         self.dicom_dataset = dicom_dataset
#         self.text_edit = text_edit  # Store the reference to text_edit
#         self.swapped = False
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle('Swap Tags')
#         self.setGeometry(200, 200, 400, 150)

#         layout = QVBoxLayout(self)

#         # Create combo boxes for tag selection
#         self.combo1 = QComboBox()
#         self.combo2 = QComboBox()

#         # Populate combo boxes with tag names
#         tag_names = [elem.name for elem in self.dicom_dataset]
#         self.combo1.addItems(tag_names)
#         self.combo2.addItems(tag_names)

#         layout.addWidget(QLabel('Select first tag:'))
#         layout.addWidget(self.combo1)
#         layout.addWidget(QLabel('Select second tag:'))
#         layout.addWidget(self.combo2)

#         # Add swap button
#         swap_button = QPushButton('Swap Tags')
#         swap_button.clicked.connect(self.swap_tags)
#         layout.addWidget(swap_button)

#     def swap_tags(self):
#         try:
#             tag1_name = self.combo1.currentText()
#             tag2_name = self.combo2.currentText()

#             if tag1_name == tag2_name:
#                 QMessageBox.warning(self, "Warning", "Please select different tags.")
#                 return

#             # Find the elements
#             elem1 = None
#             elem2 = None
#             for elem in self.dicom_dataset:
#                 if elem.name == tag1_name:
#                     elem1 = elem
#                 elif elem.name == tag2_name:
#                     elem2 = elem

#             # Swap values
#             if elem1 and elem2:
#                 temp_value = elem1.value
#                 elem1.value = elem2.value
#                 elem2.value = temp_value
                
#                 # Mark changes as made
#                 self.text_edit.append(f"{elem1.name}: {elem1.value}")
#                 self.text_edit.append(f"{elem2.name}: {elem2.value}")
#                 QMessageBox.information(self, "Success", "Tags swapped successfully!")
#             else:
#                 QMessageBox.warning(self, "Error", "Could not find selected tags.")

#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to swap tags: {str(e)}")

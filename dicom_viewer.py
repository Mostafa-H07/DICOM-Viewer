print("dicom_viewer.py is being imported")
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, 
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from dicom_display import load_dicom_file, display_dicom, display_m2d, display_3d, display_tags
from dicom_tags import TagViewerWindow
from dicom_anonymizer import anonymize_dicom
import os
import sys

class DICOMViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.current_ds = None
        self.tag_window = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('DICOM Viewer')
        self.setGeometry(100, 100, 400, 300)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel('DICOM Viewer')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # Anonymization prefix
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel('Anonymization Prefix:')
        self.prefix_input = QLineEdit()
        prefix_layout.addWidget(prefix_label)
        prefix_layout.addWidget(self.prefix_input)
        layout.addLayout(prefix_layout)

        # Buttons
        button_style = "padding: 10px; margin: 5px;"
        
        open_button = QPushButton('Open and Display DICOM')
        open_button.setStyleSheet(button_style)
        open_button.clicked.connect(self.open_and_display)
        layout.addWidget(open_button)

        # Add tag group buttons
        tag_groups_layout = QHBoxLayout()
        
        # Add "All Tags" button first
        all_tags_button = QPushButton('All Tags')
        all_tags_button.setStyleSheet(button_style)
        all_tags_button.clicked.connect(self.explore_all_tags)
        tag_groups_layout.addWidget(all_tags_button)
        
        patient_button = QPushButton('Patient Info')
        patient_button.setStyleSheet(button_style)
        patient_button.clicked.connect(lambda: self.explore_tag_group('Patient'))
        
        study_button = QPushButton('Study Info')
        study_button.setStyleSheet(button_style)
        study_button.clicked.connect(lambda: self.explore_tag_group('Study'))
        
        modality_button = QPushButton('Modality Info')
        modality_button.setStyleSheet(button_style)
        modality_button.clicked.connect(lambda: self.explore_tag_group('Modality'))
        
        physician_button = QPushButton('Physician Info')
        physician_button.setStyleSheet(button_style)
        physician_button.clicked.connect(lambda: self.explore_tag_group('Physician'))
        
        image_button = QPushButton('Image Info')
        image_button.setStyleSheet(button_style)
        image_button.clicked.connect(lambda: self.explore_tag_group('Image'))
        
        tag_groups_layout.addWidget(patient_button)
        tag_groups_layout.addWidget(study_button)
        tag_groups_layout.addWidget(modality_button)
        tag_groups_layout.addWidget(physician_button)
        tag_groups_layout.addWidget(image_button)
        
        layout.addLayout(tag_groups_layout)

        anonymize_button = QPushButton('Anonymize DICOM')
        anonymize_button.setStyleSheet(button_style)
        anonymize_button.clicked.connect(self.anonymize)
        layout.addWidget(anonymize_button)

    def open_and_display(self):
        try:
            ds, filepath = load_dicom_file()
            if ds is not None:
                self.current_ds = ds
                self.current_file = filepath
                
                try:
                    pixel_array = ds.pixel_array
                    shape = pixel_array.shape
                    
                    print(f"Image shape: {shape}")
                    
                    if len(shape) == 4 and shape[-1] == 3:  # Multi-frame color
                        print(f"Displaying multi-frame color image with {shape[0]} frames")
                        display_m2d(ds)
                    elif len(shape) == 2:  # Single image
                        print("Displaying single image")
                        display_dicom(ds)
                    elif len(shape) == 3:
                        if shape[2] == 3:  # Single RGB image
                            print("Displaying RGB image")
                            display_dicom(ds)
                        else:  # 3D volume
                            print(f"Displaying 3D volume with {shape[0]} slices")
                            display_3d(ds)
                    else:
                        QMessageBox.warning(self, "Warning", 
                                          f"Unsupported image format with shape {shape}")
                        
                except Exception as e:
                    QMessageBox.critical(self, "Error", 
                                       f"Error displaying image: {str(e)}")
                    print(f"Full error: {str(e)}")
            else:
                QMessageBox.critical(self, "Error", filepath)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def explore_tag_group(self, group):
        if self.current_ds is None:
            QMessageBox.warning(self, "Warning", "Please load a DICOM file first.")
            return
            
        tag_info = self.get_group_tags(self.current_ds, group)
        window_title = f'{group} DICOM Tags'
        self.tag_window = TagViewerWindow(tag_info, self.current_ds)
        self.tag_window.setWindowTitle(window_title)
        self.tag_window.show()

    def get_group_tags(self, ds, group):
        """Returns tags for specific DICOM groups."""
        tag_list = []
        
        group_keywords = {
            'Patient': ['Patient', 'Birth'],
            'Study': ['Study', 'Series'],
            'Modality': ['Modality', 'Protocol', 'Acquisition'],
            'Physician': ['Physician', 'Operator', 'Institution'],
            'Image': ['Image', 'Pixel', 'Window', 'Bits']
        }
        
        keywords = group_keywords.get(group, [])
        
        for elem in ds:
            try:
                element_name = elem.name.lower()
                if any(keyword.lower() in element_name for keyword in keywords):
                    tag_str = f"{elem.name}: {elem.repval}"
                    tag_list.append(tag_str)
            except Exception as e:
                continue
        
        if not tag_list:
            tag_list.append(f"No {group} tags found.")
            
        return "\n".join(tag_list)

    def anonymize(self):
        if self.current_file is None:
            QMessageBox.warning(self, "Warning", "Please load a DICOM file first.")
            return
        
        prefix = self.prefix_input.text().strip()
        if not prefix:
            QMessageBox.warning(self, "Warning", "Please enter an anonymization prefix.")
            return
        
        if anonymize_dicom(self.current_file, prefix):
            save_path = os.path.join(os.path.dirname(self.current_file), 
                                   f"anonymized_{os.path.basename(self.current_file)}")
            QMessageBox.information(self, "Success", 
                                  f"File anonymized successfully!\nSaved to:\n{save_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to anonymize file.")

    def explore_all_tags(self):
        """Shows all DICOM tags without categorization."""
        if self.current_ds is None:
            QMessageBox.warning(self, "Warning", "Please load a DICOM file first.")
            return
            
        tag_info = display_tags(self.current_ds)
        self.tag_window = TagViewerWindow(tag_info, self.current_ds)
        self.tag_window.setWindowTitle('All DICOM Tags')
        self.tag_window.show()

def main():
    app = QApplication(sys.argv)
    viewer = DICOMViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

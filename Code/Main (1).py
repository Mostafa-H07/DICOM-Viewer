import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from dicom_viewer import DICOMViewer

def main():
    try:
        app = QApplication(sys.argv)
        viewer = DICOMViewer()
        viewer.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

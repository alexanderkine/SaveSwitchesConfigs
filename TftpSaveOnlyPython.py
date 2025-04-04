from netmiko import (
    ConnectHandler,
    NetMikoTimeoutException,
    NetmikoAuthenticationException,
    ConnectionException
)
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QCoreApplication, Qt

class BackupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Cisco Backup Tool')

        self.layout = QVBoxLayout()
        
        self.label = QLabel(self)
        self.label.setText('Сохранение конфигураций коммутаторов')
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # Поле для ввода пути сохранения конфигураций
        self.backup_path_input = QLineEdit(self)
        self.backup_path_input.setPlaceholderText('Введите путь для сохранения конфигураций')
        self.layout.addWidget(self.backup_path_input)

        # Кнопка для выбора папки сохранения
        self.backup_path_button = QPushButton('Выбрать папку для сохранения', self)
        self.backup_path_button.clicked.connect(self.select_backup_path)
        self.layout.addWidget(self.backup_path_button)

        # Поле для ввода пути к файлу с IP
        self.devices_path_input = QLineEdit(self)
        self.devices_path_input.setPlaceholderText('Введите путь к файлу с IP коммутаторов')
        self.layout.addWidget(self.devices_path_input)

        # Кнопка для выбора файла с IP
        self.devices_path_button = QPushButton('Выбрать файл с IP', self)
        self.devices_path_button.clicked.connect(self.select_devices_path)
        self.layout.addWidget(self.devices_path_button)

        # Кнопка для начала резервного копирования
        self.start_button = QPushButton('Начать резервное копирование', self)
        self.start_button.clicked.connect(self.start_backup)
        self.layout.addWidget(self.start_button)

        self.setLayout(self.layout)

    def select_backup_path(self):
        path = QFileDialog.getExistingDirectory(self, 'Выберите папку для сохранения')
        if path:
            self.backup_path_input.setText(path)

    def select_devices_path(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Выберите файл с IP', '', 'Text Files (*.txt);;All Files (*)')
        if path:
            self.devices_path_input.setText(path)

    def parse_devices_file(self, path):
        devices = []
        with open(path, "r") as devices_file:
            for line in devices_file:
                devices.append(line.strip())
        return devices

    def connect_and_save_output(self, device):
        try:
            net_connect = ConnectHandler(**device)
            net_connect.enable()
            hostname = net_connect.find_prompt().strip('#')
            config_output = net_connect.send_command('show running-config')
            net_connect.disconnect()
            return (config_output, hostname)
        except Exception as e:
            print(f'Ошибка подключения: {e}')
            return (None, None)

    def save_config_from_device(self, station_folder, ip):
        device = {
            'device_type': 'cisco_ios_telnet',
            'ip': ip,
            'username': 'root',
            'password': 'root',
            'port': 23
        }
        output = self.connect_and_save_output(device)
        if output[0] is not None:
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            with open(f'{station_folder}/{ip} ({output[1]}_backup_{current_date}.txt', 'w') as file:
                file.write(output[0])
            print(f'{station_folder} {ip} успешно сохранено!')
        else:
            print(f'{station_folder} {ip} не было сохранено!')

    def start_backup(self):
        backup_path = self.backup_path_input.text().strip()
        devices_path = self.devices_path_input.text().strip()

        if not backup_path:
            backup_path = os.getcwd()
        if not devices_path:
            devices_path = 'devices'

        stations = ('Динамо', 'Уральская', 'Машиностроителей', 'Уралмаш', 'Проспект Космонавтов', 
                    'Площадь 1905 года', 'Геологическая', 'Депо', 'Инженерный корпус', 'Чкаловская', 
                    'Ботаническая')

        folder_path = f'{backup_path}/CiscoBackups_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
        os.mkdir(folder_path)

        devices_file = self.parse_devices_file(devices_path)

        for station in stations:
            os.mkdir(f'{folder_path}/{station}')

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for ip in devices_file:
                station_number = ip.split('.')[1]
                station_folder = f'{folder_path}/{stations[int(station_number) - 1]}'
                futures.append(executor.submit(self.save_config_from_device, station_folder, ip))

            for future in futures:
                future.result()

        QMessageBox.information(self, 'Завершено', 'Резервное копирование завершено!')

if __name__ == '__main__':
    app = QApplication([])
    backup_app = BackupApp()
    backup_app.resize(400, 400)
    backup_app.show()
    app.exec_()
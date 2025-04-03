from netmiko import (
    ConnectHandler,
    NetMikoTimeoutException,
    NetmikoAuthenticationException,
    ConnectionException
)
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor

# Configuration options
print('Конфигурации сохраняются в папке вида CiscoBackups_<date>\n')
print('Введите абсолютный путь сохранения конфигураций (пустое поле означает сохранение по текущему месту скрипта) и нажмите <Enter>:')
backup_path = input().strip()
print('Введите абсолютный путь к файлу с IP коммутаторов (пустое поле означает файл c именем devices по текущему месту скрипта) и нажмите <Enter>:')
devices_path = input().strip()

def parse_devices_file(path):
    devices_file = open(path, "r")
    devices = []
    while True:
        ip = devices_file.readline().strip()
        if not ip:
            break
        devices.append(ip)
    devices_file.close()

    return devices

stations = ('Динамо', 'Уральская', 'Машиностроителей', 'Уралмаш', 'Проспект Космонавтов', 'Площадь 1905 года', 'Геологическая', 'Депо', 'Инженерный корпус', 'Чкаловская', 'Ботаническая')   
devices_file = parse_devices_file('devices' if devices_path == '' else f'{devices_path}')
symbol = "" if backup_path == "" else "/"
folder_path = f'{backup_path}{symbol}CiscoBackups_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'.strip()
os.mkdir(folder_path)
os.chdir(folder_path)

for station in stations:
        os.mkdir(f'{station}')

def connect_and_save_output(device):
    try:
        net_connect = ConnectHandler(**device)
    except:
        print(f'{station_folder} {ip} не было сохранено!')
        pass
    else:        
            net_connect.enable()
            hostname = net_connect.find_prompt().strip('#')
            config_output = net_connect.send_command('show running-config')
            net_connect.disconnect()

    return (config_output, hostname)

def save_config_from_device(station_folder, ip):
    device =  { 'device_type':'cisco_ios_telnet', 'ip':ip, 'username':'root', 'password':'root', 'port': 23}
    output = connect_and_save_output(device)
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # сохранение конфигурации в файл
    with open(f'{station_folder}\{ip} ({output[1]}_backup_{current_date}.txt', 'w') as file:
        file.write(output[0])
        
    print(f'{station_folder} {ip} успешно сохранено!')
    
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    for ip in devices_file:    
        station_number = ip.split('.')[1]
        station_folder = stations[int(station_number) - 1]
        futures.append(executor.submit(save_config_from_device, station_folder, ip))

    # Ожидаем завершения всех потоков
    for future in futures:
        future.result()
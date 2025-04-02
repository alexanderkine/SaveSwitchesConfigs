# REQUIRMENTS
# 1) Netmiko installed https://github.com/ktbyers/netmiko
# 2) Cisco SG300 switches must have ip 'ssh password-auth'configured to prevent the username being requested twice
# 3) TFTP server to send the running configs too

import asyncio
from threading import Thread
from netmiko import (
    ConnectHandler,
    NetMikoTimeoutException,
    NetmikoAuthenticationException,
    ConnectionException
)
import datetime
import os

# Configuration options
print('Конфигурации сохраняются в папке вида CiscoBackups_<date>\n')
print('Введите абсолютный путь сохранения конфигураций (пустое поле означает сохранение по текущему месту скрипта) и нажмите <Enter>:')


backup_path = input().strip()
symbol = "" if backup_path == "" else "/"
current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
folder_path = f"{backup_path}{symbol}CiscoBackups_{current_date}".strip()
os.mkdir(folder_path)
stations = ('Динамо', 'Уральская', 'Машиностроителей', 'Уралмаш', 'Проспект Космонавтов', 'Площадь 1905 года', 'Геологическая', 'Депо', 'Инженерный корпус', 'Чкаловская', 'Ботаническая')   

for station in stations:
        os.mkdir(f'{folder_path}\{station}')

def parse_devices_file(path):
    devices = open(path, "r")
    devs = []
    while True:
        line = devices.readline().strip()
        if not line:
            break
        devs.append(line)
    devices.close()

    return devs

async def save_config_from_device(station_folder, ip):
    device =  { 'device_type':'cisco_ios_telnet', 'ip':ip, 'username':'root', 'password':'root', 'port': 23}
    try:
        net_connect = ConnectHandler(**device)
    except:
        print(f'{station_folder} {ip} не было сохранено!')
        pass
    else:        
            net_connect.enable()
            hostname = net_connect.find_prompt().strip('#')
            config_output = net_connect.send_command('show running-config')
    
            # сохранение конфигурации в файл
            with open(f'{folder_path}\{station_folder}\{ip} ({hostname}_backup_{current_date}).txt', 'w') as file:
                file.write(config_output)
        
            print(f'{station_folder} {ip} успешно сохранено!')
            net_connect.disconnect()

for ip in parse_devices_file(f"devices"):	
    station_folder = ''
    station_number = ip.split('.')[1]
    station_folder = stations[int(station_number) - 1]

    asyncio.run(save_config_from_device(station_folder, ip))


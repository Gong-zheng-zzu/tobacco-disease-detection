import serial

ser = serial.Serial('COM3', 9600)  # 替换为您的端口号

while True:
    if (ser.in_waiting > 0):
        data = ser.readline().decode().strip()  # 读取一行数据
        print("Received from Arduino: ", data)  # 打印接收到的数据

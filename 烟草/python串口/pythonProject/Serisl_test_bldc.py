import serial
import time

# 打开串口
ser = serial.Serial('COM3', 9600, timeout=1)  # 请根据实际情况修改串口名称

# 等待串口稳定
time.sleep(2)


# 写入数据到串口
def write_to_serial(data):
    ser.write(f"{data}\n".encode('utf-8'))  # 将数据转换为字节并发送


# 主函数
def main():
    while True:
        try:
            pwm_value = input("请输入PWM值 (1000 - 2000): ")
            if not pwm_value.isdigit():
                print("请输入一个有效的数字")
                continue

            pwm_value = int(pwm_value)
            if 1000 <= pwm_value <= 2000:
                write_to_serial(pwm_value)
                print(f"发送PWM值: {pwm_value}")
            else:
                print("请输入1000到2000之间的值")

        except KeyboardInterrupt:
            print("程序终止")
            break

    ser.close()


if __name__ == "__main__":
    main()

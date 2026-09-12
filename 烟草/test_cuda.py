import torch
import torch.cuda

print('PyTorch版本:', torch.__version__)
print('CUDA编译版本:', torch.version.cuda)
print('cuDNN可用:', torch.backends.cudnn.is_available())

try:
    print('\n尝试初始化CUDA...')
    torch.cuda._lazy_init()
    print('✅ CUDA初始化成功')
    print('GPU数量:', torch.cuda.device_count())
    print('GPU设备:', torch.cuda.get_device_name(0))
except Exception as e:
    print('❌ CUDA初始化失败:')
    print('错误类型:', type(e).__name__)
    print('错误信息:', str(e))

print('\nCUDA可用:', torch.cuda.is_available())

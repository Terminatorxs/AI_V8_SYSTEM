import torch

# 加载 YOLO11 模型
model = torch.load('yolo11n.pt', map_location='cpu')
model.eval()

# YOLO11 输入尺寸 1,3,640,640
dummy_input = torch.randn(1, 3, 640, 640)

torch.onnx.export(
    model,
    dummy_input,
    'yolo11n.onnx',
    input_names=['input'],
    output_names=['output'],
    opset_version=11
)
print("✅ ONNX 导出成功！")

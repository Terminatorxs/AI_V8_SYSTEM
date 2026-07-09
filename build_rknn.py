from rknn.api import RKNN

rknn = RKNN()

print("config...")

rknn.config(
    target_platform='rk3588',
    mean_values=[[0, 0, 0]],
    std_values=[[255, 255, 255]],
    optimization_level=2
)

print("load onnx...")

rknn.load_onnx(
    model='yolo11n.onnx',
    inputs=['images'],
    input_size_list=[[1, 3, 640, 640]]
)

print("build...")

rknn.build(do_quantization=False)

print("export...")

rknn.export_rknn('yolo11n.rknn')

rknn.release()

print("DONE")

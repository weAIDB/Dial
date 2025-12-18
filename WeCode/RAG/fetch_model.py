from modelscope import snapshot_download

model_dir = snapshot_download(
    model_id='BAAI/bge-large-en-v1.5',
    cache_dir=r'C:\Users\17376\Desktop\方言提取器\model4.0'  # 加r表示原始字符串
)
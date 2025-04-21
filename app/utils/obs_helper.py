from obs import ObsClient
import os
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt

class OBSHelper:
    def __init__(self, access_key_id: str, secret_access_key: str, server: str, bucket_name: str):
        self.obs_client = ObsClient(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            server=server
        )
        self.bucket_name = bucket_name

    async def upload_file(self, file_data: bytes, original_filename: str) -> str:
        """
        上传文件到华为云 OBS
        
        Args:
            file_data: 文件二进制数据
            original_filename: 原始文件名
            
        Returns:
            str: 文件的访问URL
        """
        # 生成唯一的对象键
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(original_filename)[1]
        object_key = f"sales_data/{timestamp}{file_ext}"
        
        # 上传文件
        resp = self.obs_client.putContent(
            bucketName=self.bucket_name,
            objectKey=object_key,
            content=file_data
        )
        
        if resp.status < 300:
            # 返回文件访问URL
            return f"https://{self.bucket_name}.{self.obs_client.server}/{object_key}"
        else:
            raise Exception(f"Failed to upload file: {resp.reason}")

    async def upload_figure(self, figure: plt.Figure, filename: str) -> str:
        """
        将 matplotlib 图表上传到华为云 OBS
        
        Args:
            figure: matplotlib 图表对象
            filename: 文件名
            
        Returns:
            str: 图片的访问URL
        """
        # 将图表保存到内存中
        buf = BytesIO()
        figure.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        
        # 生成唯一的对象键
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_key = f"sales_charts/{timestamp}_{filename}.png"
        
        # 上传文件
        resp = self.obs_client.putContent(
            bucketName=self.bucket_name,
            objectKey=object_key,
            content=buf.getvalue()
        )
        
        if resp.status < 300:
            # 返回文件访问URL
            return f"https://{self.bucket_name}.{self.obs_client.server}/{object_key}"
        else:
            raise Exception(f"Failed to upload chart: {resp.reason}")

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'obs_client'):
            self.obs_client.close()
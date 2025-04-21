import pandas as pd
import numpy as np
from typing import Any, Dict, List
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from ...core.base_ability import BaseAbility
from ...utils.obs_helper import OBSHelper
import yaml

class SalesAnalyzer(BaseAbility):
    """Sales data analysis ability"""
    
    def __init__(self):
        # 加载配置文件
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        # 初始化OBS Helper
        obs_config = config.get("huaweicloud", {}).get("obs", {})
        self.obs_helper = OBSHelper(
            access_key_id=obs_config.get("access_key_id"),
            secret_access_key=obs_config.get("secret_access_key"),
            server=obs_config.get("server"),
            bucket_name=obs_config.get("bucket_name")
        )
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimSun', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
    
    @property
    def name(self) -> str:
        return "sales_analyzer"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def validate(self, context: Dict[str, Any]) -> bool:
        """验证输入参数
        
        必需参数:
        - file_url: 销售数据文件的URL
        - analysis_type: 分析类型，可选值：
            - 'basic_stats': 基础统计
            - 'sales_by_region': 区域销售分析
            - 'sales_by_product': 产品销售分析
            - 'sales_by_channel': 渠道销售分析
            - 'profit_analysis': 利润分析
            - 'visualization': 数据可视化
        """
        required_fields = ['file_url', 'analysis_type']
        if not all(field in context for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")
            
        valid_analysis_types = [
            'basic_stats',
            'sales_by_region',
            'sales_by_product',
            'sales_by_channel',
            'profit_analysis',
            'visualization'
        ]
        
        if context['analysis_type'] not in valid_analysis_types:
            raise ValueError(f"Invalid analysis type. Must be one of {valid_analysis_types}")
            
        return True
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """执行销售数据分析
        
        Args:
            context: 包含输入参数的字典
            
        Returns:
            Dict: 分析结果
        """
        # 从 URL 读取数据
        response = requests.get(context['file_url'])
        if response.status_code != 200:
            raise Exception(f"Failed to download file from URL: {response.status_code}")
        
        # 读取Excel数据
        df = pd.read_excel(BytesIO(response.content))
        
        # 确保date列是datetime类型
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime('%Y-%m')
        
        # 根据分析类型执行相应的分析
        analysis_type = context['analysis_type']
        
        if analysis_type == 'basic_stats':
            return self._basic_stats_analysis(df)
        elif analysis_type == 'sales_by_region':
            return self._region_analysis(df)
        elif analysis_type == 'sales_by_product':
            return self._product_analysis(df)
        elif analysis_type == 'sales_by_channel':
            return self._channel_analysis(df)
        elif analysis_type == 'profit_analysis':
            return self._profit_analysis(df)
        elif analysis_type == 'visualization':
            return await self._create_visualizations(df)
    
    def _basic_stats_analysis(self, df: pd.DataFrame) -> Dict:
        """基础统计分析"""
        return {
            'total_sales': df['total_sales'].sum(),
            'total_profit': df['profit'].sum(),
            'average_daily_sales': df.groupby('date')['total_sales'].sum().mean(),
            'total_orders': len(df),
            'summary_stats': df[['total_sales', 'profit', 'quantity']].describe().to_dict()
        }
    
    def _region_analysis(self, df: pd.DataFrame) -> Dict:
        """区域销售分析"""
        region_sales = df.groupby('region').agg({
            'total_sales': 'sum',
            'profit': 'sum',
            'quantity': 'sum'
        }).to_dict('index')
        
        city_sales = df.groupby('city')['total_sales'].sum().sort_values(ascending=False).head(10)
        
        return {
            'region_sales': region_sales,
            'top_10_cities': city_sales.to_dict()
        }
    
    def _product_analysis(self, df: pd.DataFrame) -> Dict:
        """产品销售分析"""
        product_analysis = df.groupby('product').agg({
            'total_sales': 'sum',
            'profit': 'sum',
            'quantity': 'sum'
        }).sort_values('total_sales', ascending=False).to_dict('index')
        
        category_analysis = df.groupby('category').agg({
            'total_sales': 'sum',
            'profit': 'sum'
        }).to_dict('index')
        
        return {
            'product_analysis': product_analysis,
            'category_analysis': category_analysis
        }
    
    def _channel_analysis(self, df: pd.DataFrame) -> Dict:
        """渠道销售分析"""
        # 先计算每个渠道的总销售额和利润
        channel_metrics = df.groupby('channel').agg({
            'total_sales': 'sum',
            'profit': 'sum',
            'quantity': 'sum'
        })
        
        # 计算利润率
        channel_profit_margins = (channel_metrics['profit'] / channel_metrics['total_sales'] * 100)
        
        return {
            'channel_analysis': channel_metrics.sort_values('total_sales', ascending=False).to_dict('index'),
            'channel_profit_margin': channel_profit_margins.to_dict()
        }
    
    def _profit_analysis(self, df: pd.DataFrame) -> Dict:
        """利润分析"""
        # 计算总体指标
        total_sales = df['total_sales'].sum()
        total_profit = df['profit'].sum()
        
        # 按产品和地区分组计算
        product_metrics = df.groupby('product').agg({
            'profit': 'sum',
            'total_sales': 'sum'
        })
        region_metrics = df.groupby('region').agg({
            'profit': 'sum',
            'total_sales': 'sum'
        })
        
        # 计算利润率
        product_profit_margins = (product_metrics['profit'] / product_metrics['total_sales'] * 100)
        region_profit_margins = (region_metrics['profit'] / region_metrics['total_sales'] * 100)
        
        return {
            'total_profit': total_profit,
            'profit_margin': (total_profit / total_sales * 100),
            'product_profit_margins': product_profit_margins.to_dict(),
            'region_profit_margins': region_profit_margins.to_dict()
        }
    
    async def _create_visualizations(self, df: pd.DataFrame) -> Dict[str, str]:
        """创建数据可视化并上传到OBS
        
        Args:
            df: 销售数据DataFrame
            
        Returns:
            Dict[str, str]: 包含所有图表URL的字典
        """
        chart_urls = {}
        
        # 1. 月度销售趋势图
        plt.figure(figsize=(15, 6))
        monthly_sales = df.groupby('month')['total_sales'].sum()
        plt.plot(monthly_sales.index, monthly_sales.values, marker='o')
        plt.title('月度销售趋势')
        plt.xlabel('月份')
        plt.ylabel('销售额')
        plt.xticks(rotation=45)
        plt.tight_layout()
        chart_urls['monthly_sales_trend'] = await self.obs_helper.upload_figure(plt.gcf(), 'monthly_sales_trend')
        plt.close()
        
        # 2. 区域销售分布图
        plt.figure(figsize=(10, 6))
        region_sales = df.groupby('region')['total_sales'].sum()
        sns.barplot(x=region_sales.index, y=region_sales.values)
        plt.title('各地区销售额分布')
        plt.xlabel('地区')
        plt.ylabel('销售额')
        plt.tight_layout()
        chart_urls['region_sales'] = await self.obs_helper.upload_figure(plt.gcf(), 'region_sales')
        plt.close()
        
        # 3. 渠道销售占比饼图
        plt.figure(figsize=(10, 8))
        channel_sales = df.groupby('channel')['total_sales'].sum()
        plt.pie(channel_sales.values, labels=channel_sales.index, autopct='%1.1f%%')
        plt.title('各渠道销售额占比')
        plt.axis('equal')
        plt.tight_layout()
        chart_urls['channel_sales'] = await self.obs_helper.upload_figure(plt.gcf(), 'channel_sales')
        plt.close()
        
        # 4. 产品利润矩阵图
        plt.figure(figsize=(12, 8))
        for product in df['product'].unique():
            product_data = df[df['product'] == product]
            plt.scatter(product_data['total_cost'].mean(), 
                       product_data['profit'].mean(),
                       s=100,
                       label=product)
        plt.xlabel('平均成本')
        plt.ylabel('平均利润')
        plt.title('产品利润矩阵')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        chart_urls['product_profit'] = await self.obs_helper.upload_figure(plt.gcf(), 'product_profit')
        plt.close()
        
        # 5. 区域-渠道热力图
        plt.figure(figsize=(12, 8))
        pivot_table = pd.pivot_table(df, 
                                   values='profit',
                                   index='region',
                                   columns='channel',
                                   aggfunc='sum')
        sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlOrRd')
        plt.title('区域渠道利润热力图')
        plt.tight_layout()
        chart_urls['region_channel_heatmap'] = await self.obs_helper.upload_figure(plt.gcf(), 'region_channel_heatmap')
        plt.close()
        
        return {
            'visualization_urls': chart_urls,
            'message': '可视化图表已生成并上传到OBS存储'
        }
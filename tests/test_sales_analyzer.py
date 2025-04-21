import pytest
import pandas as pd
from datetime import datetime
from app.abilities.analyzer.sales_analyzer import SalesAnalyzer

@pytest.fixture
def sample_sales_data():
    """创建测试用的销售数据"""
    data = {
        'date': [datetime(2025, 4, 1), datetime(2025, 4, 1)],
        'product': ['笔记本电脑', '手机'],
        'category': ['电子产品', '电子产品'],
        'region': ['华北', '华南'],
        'city': ['北京', '广州'],
        'channel': ['线下门店', '电商平台'],
        'quantity': [2, 3],
        'unit_price': [8000, 3000],
        'unit_cost': [6000, 2000],
        'total_sales': [16000, 9000],
        'total_cost': [12000, 6000],
        'profit': [4000, 3000]
    }
    return pd.DataFrame(data)

@pytest.mark.asyncio
async def test_sales_analyzer_validate():
    analyzer = SalesAnalyzer()
    
    # 测试有效参数
    valid_context = {
        "file_url": "https://example.com/sales_data.xlsx",
        "analysis_type": "basic_stats"
    }
    assert await analyzer.validate(valid_context)
    
    # 测试无效参数
    invalid_contexts = [
        {},  # 空字典
        {"file_url": "https://example.com/sales_data.xlsx"},  # 缺少 analysis_type
        {"analysis_type": "basic_stats"},  # 缺少 file_url
        {  # 无效的分析类型
            "file_url": "https://example.com/sales_data.xlsx",
            "analysis_type": "invalid_type"
        }
    ]
    
    for context in invalid_contexts:
        with pytest.raises(ValueError):
            await analyzer.validate(context)

@pytest.mark.asyncio
async def test_basic_stats_analysis(sample_sales_data):
    analyzer = SalesAnalyzer()
    result = analyzer._basic_stats_analysis(sample_sales_data)
    
    assert isinstance(result, dict)
    assert 'total_sales' in result
    assert 'total_profit' in result
    assert 'average_daily_sales' in result
    assert 'total_orders' in result
    assert 'summary_stats' in result
    
    assert result['total_sales'] == 25000  # 16000 + 9000
    assert result['total_profit'] == 7000  # 4000 + 3000
    assert result['total_orders'] == 2

@pytest.mark.asyncio
async def test_region_analysis(sample_sales_data):
    analyzer = SalesAnalyzer()
    result = analyzer._region_analysis(sample_sales_data)
    
    assert isinstance(result, dict)
    assert 'region_sales' in result
    assert 'top_10_cities' in result
    
    region_sales = result['region_sales']
    assert '华北' in region_sales
    assert '华南' in region_sales
    
    assert region_sales['华北']['total_sales'] == 16000
    assert region_sales['华南']['total_sales'] == 9000

@pytest.mark.asyncio
async def test_product_analysis(sample_sales_data):
    analyzer = SalesAnalyzer()
    result = analyzer._product_analysis(sample_sales_data)
    
    assert isinstance(result, dict)
    assert 'product_analysis' in result
    assert 'category_analysis' in result
    
    product_analysis = result['product_analysis']
    assert '笔记本电脑' in product_analysis
    assert '手机' in product_analysis
    
    assert product_analysis['笔记本电脑']['total_sales'] == 16000
    assert product_analysis['手机']['total_sales'] == 9000

@pytest.mark.asyncio
async def test_channel_analysis(sample_sales_data):
    analyzer = SalesAnalyzer()
    result = analyzer._channel_analysis(sample_sales_data)
    
    assert isinstance(result, dict)
    assert 'channel_analysis' in result
    assert 'channel_profit_margin' in result
    
    channel_analysis = result['channel_analysis']
    assert '线下门店' in channel_analysis
    assert '电商平台' in channel_analysis
    
    assert channel_analysis['线下门店']['total_sales'] == 16000
    assert channel_analysis['电商平台']['total_sales'] == 9000

@pytest.mark.asyncio
async def test_profit_analysis(sample_sales_data):
    analyzer = SalesAnalyzer()
    result = analyzer._profit_analysis(sample_sales_data)
    
    assert isinstance(result, dict)
    assert 'total_profit' in result
    assert 'profit_margin' in result
    assert 'product_profit_margins' in result
    assert 'region_profit_margins' in result
    
    assert result['total_profit'] == 7000
    assert abs(result['profit_margin'] - 28.0) < 0.1  # 7000/25000 * 100 ≈ 28%
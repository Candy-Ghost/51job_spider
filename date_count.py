import json
import pandas as pd
import numpy as np
import re
from pandas import json_normalize
from collections import OrderedDict
from datetime import datetime


# 1. 精确去重函数（基于指定四列）
def load_and_deduplicate(filepath):
    """根据岗位名称、公司名称、工作区域、薪资四列进行精确去重"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 转换为DataFrame
    df = json_normalize(data["jobs"])

    # 定义去重依据的列
    duplicate_cols = ['岗位名称', '公司名称', '工作区域', '薪资']

    # 检查缺失列
    missing_cols = [col for col in duplicate_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺失必要列: {missing_cols}")

    print(f"原始记录数: {len(df)}")
    print("去重依据列示例:")
    print(df[duplicate_cols].head(3))

    # 标记重复行（保留第一条）
    duplicate_mask = df.duplicated(subset=duplicate_cols, keep='first')
    print(f"发现重复行数: {duplicate_mask.sum()}")

    # 执行去重
    df_dedup = df[~duplicate_mask].copy()
    print(f"去重后记录数: {len(df_dedup)}")

    return df_dedup


# 2. 薪资解析函数（保持不变）
def parse_salary(salary_str):
    """解析薪资字符串，返回平均月薪(元)"""
    if not isinstance(salary_str, str) or "面议" in salary_str:
        return np.nan

    salary_str = salary_str.replace('k', '千').replace('K', '千')
    range_part = re.split(r'[·,]', salary_str)[0]
    matches = re.findall(r'([\d.]+)([万千]?)', range_part)
    if len(matches) < 2:
        return np.nan

    def to_yuan(num, unit):
        num = float(num)
        if '万' in unit: return num * 10000
        if '千' in unit: return num * 1000
        return num

    try:
        lower = to_yuan(matches[0][0], matches[0][1])
        upper = to_yuan(matches[1][0], matches[1][1])
        return (lower + upper) / 2
    except:
        return np.nan


# 3. 数据分析主函数
def analyze_data(df):
    """执行完整的数据分析"""
    results = OrderedDict()

    # 解析薪资
    df['平均月薪'] = df['薪资'].apply(parse_salary)
    valid_salary_count = df['平均月薪'].notna().sum()

    # 基础信息
    results["元数据"] = {
        "数据来源": "51job_python_job.json",
        "总记录数": int(len(df)),
        "有效薪资记录数": int(valid_salary_count),
        "去重依据": "岗位名称+公司名称+工作区域+薪资",
        "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 基础统计
    if valid_salary_count > 0:
        results["薪资统计"] = {
            "平均值": round(float(df['平均月薪'].mean()), 2),
            "中位数": round(float(df['平均月薪'].median()), 2),
            "最高值": round(float(df['平均月薪'].max()), 2),
            "最低值": round(float(df['平均月薪'].min()), 2),
            "分位数": {
                "25%": round(float(df['平均月薪'].quantile(0.25)), 2),
                "75%": round(float(df['平均月薪'].quantile(0.75)), 2)
            }
        }

    # 按地区分析
    results["地区分布"] = {
        region: {
            "岗位数": int(len(group)),
            "平均薪资": round(float(group['平均月薪'].mean()), 2)
        }
        for region, group in df.groupby('工作区域')
    }

    # 按经验要求分析
    if '经验要求' in df.columns:
        results["经验要求分布"] = {
            exp: {
                "岗位数": int(len(group)),
                "平均薪资": round(float(group['平均月薪'].mean()), 2)
            }
            for exp, group in df.groupby('经验要求')
        }

    # 公司类型分布
    if '公司类型' in df.columns:
        results["公司类型分布"] = df['公司类型'].value_counts().to_dict()

    # 热门标签统计（展开所有标签）
    if '标签' in df.columns:
        all_tags = [tag for sublist in df['标签'] for tag in sublist]
        results["热门标签TOP10"] = {
            tag: int(count)
            for tag, count in pd.Series(all_tags).value_counts().head(10).items()
        }

    return results


# 4. 主程序
if __name__ == "__main__":
    try:
        # 步骤1: 加载并去重
        print("正在执行精确去重...")
        df = load_and_deduplicate("51job_python_job.json")

        # 步骤2: 分析数据
        print("\n正在分析数据...")
        results = analyze_data(df)

        # 步骤3: 保存结果
        output_file = "job_analysis_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        print(f"\n分析完成！结果已保存到 {output_file}")
        print("\n关键统计:")
        print(f"- 去重后岗位数: {results['元数据']['总记录数']}")
        if '薪资统计' in results:
            print(f"- 平均薪资: {results['薪资统计']['平均值']:.2f}元")
            print(f"- 最高薪资: {results['薪资统计']['最高值']:.2f}元")

    except Exception as e:
        print(f"\n错误: {str(e)}")
        print("可能的原因:")
        print("1. JSON文件路径错误")
        print("2. 缺少必要的列（岗位名称/公司名称/工作区域/薪资）")
        print("3. 文件编码问题（确保是UTF-8编码）")
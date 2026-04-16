#!/usr/bin/env python3
"""
知识权重分析引擎 - Knowledge Weight Analyzer Engine

独立 Python 引擎，专门用于知识权重处理分析。
输入文本，输出权重评分和精挑细选的关键知识。
不负责存储，仅提供分析结果供 AI 决策使用。

设计原则：
1. 纯分析，零存储
2. 基于规则 + 启发式算法（可扩展为 NLP）
3. 输出结构化 JSON，便于集成
4. 可独立运行，也可作为模块导入
"""

import re
import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import Counter
import math

@dataclass
class KeyPoint:
    """关键知识点"""
    text: str
    type: str  # concept/definition/method/fact/technique/example/syntax
    confidence: float  # 0.0~1.0
    start_pos: int = 0
    end_pos: int = 0

@dataclass
class WeightScore:
    """权重分数详情"""
    overall: float  # 总权重分 0.0~1.0
    information_density: float  # 信息密度
    knowledge_type: float  # 知识类型权重
    structure: float  # 结构完整性
    uniqueness: float  # 独特性
    practicality: float  # 实用性
    authority: float  # 权威性（如有来源）

@dataclass
class AnalysisResult:
    """分析结果"""
    weight_score: WeightScore
    grade: str  # A(≥0.8) B(0.6~0.8) C(<0.6)
    key_points: List[KeyPoint]
    analysis: Dict[str, Any]
    recommendation: Dict[str, Any]
    timestamp: str
    version: str = "1.0.0"

class KnowledgeWeightAnalyzer:
    """知识权重分析引擎"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.version = "1.0.0"
        
        # 知识类型权重映射
        self.knowledge_type_weights = {
            "definition": 1.0,      # 定义
            "method": 0.9,         # 方法
            "concept": 0.8,        # 概念
            "technique": 0.85,     # 技巧
            "syntax": 0.8,         # 语法规则
            "fact": 0.7,          # 事实
            "example": 0.6,       # 示例
            "explanation": 0.75,  # 解释说明
            "comparison": 0.8,    # 对比
            "warning": 0.7,       # 注意事项
            "chat": 0.2,          # 闲聊
        }
        
        # 关键知识识别模式
        self.patterns = {
            "definition": [
                r"定义是", r"指的是", r"意思是", r"含义是",
                r"所谓[\u4e00-\u9fa5]{1,10}就是", r"即"
            ],
            "method": [
                r"步骤[一二三四五六七八九十\d]", r"第[一二三四五六七八九十\d]步",
                r"方法如下", r"操作流程", r"步骤如下", r"流程是",
                r"首先[\u4e00-\u9fa5]{0,10}然后", r"先[\u4e00-\u9fa5]{0,10}再"
            ],
            "technique": [
                r"技巧", r"窍门", r"妙招", r"建议", r"注意事项",
                r"关键点", r"重点", r"要点"
            ],
            "syntax": [
                r"语法是", r"格式为", r"表达式", r"正则表达式",
                r"代码示例", r"示例代码", r"[\w]+\(.*?\)"
            ],
            "comparison": [
                r"对比", r"比较", r"区别在于", r"不同点",
                r"相同点", r"相似处"
            ],
            "warning": [
                r"注意", r"警告", r"小心", r"避免",
                r"不要", r"严禁", r"禁止"
            ]
        }
        
        # 低价值内容模式（闲聊、客套话）
        self.low_value_patterns = [
            r"你好", r"谢谢", r"不客气", r"请问", r"帮忙",
            r"辛苦了", r"太好了", r"真棒", r"不错", r"很好",
            r"明白了", r"知道了", r"了解", r"嗯", r"哦",
            r"哈哈", r"呵呵", r"嘿嘿"
        ]
    
    def analyze(self, text: str, context: Dict = None) -> AnalysisResult:
        """
        分析文本，返回完整的权重评估结果
        
        Args:
            text: 待分析的文本
            context: 上下文信息（可选）
            
        Returns:
            AnalysisResult: 分析结果
        """
        # 文本预处理
        cleaned_text = self._preprocess_text(text)
        
        # 提取关键知识
        key_points = self.extract_key_knowledge(cleaned_text)
        
        # 计算权重分数
        weight_score = self.calculate_weight(cleaned_text, key_points, context)
        
        # 生成分析详情
        analysis = self._generate_analysis_details(cleaned_text, key_points, weight_score)
        
        # 生成推荐
        recommendation = self._generate_recommendation(weight_score, key_points, context)
        
        # 确定等级
        grade = self._calculate_grade(weight_score.overall)
        
        # 构建结果
        result = AnalysisResult(
            weight_score=weight_score,
            grade=grade,
            key_points=key_points,
            analysis=analysis,
            recommendation=recommendation,
            timestamp=datetime.now().isoformat(),
            version=self.version
        )
        
        return result
    
    def extract_key_knowledge(self, text: str) -> List[KeyPoint]:
        """
        提取精挑细选的关键知识
        
        Args:
            text: 输入文本
            
        Returns:
            List[KeyPoint]: 关键知识点列表
        """
        key_points = []
        lines = text.split('\n')
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 10:
                continue
                
            # 检查是否包含关键知识模式
            for ktype, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = list(re.finditer(pattern, line, re.IGNORECASE))
                    for match in matches:
                        # 提取上下文（匹配位置前后）
                        start = max(0, match.start() - 50)
                        end = min(len(line), match.end() + 100)
                        context_text = line[start:end]
                        
                        # 计算置信度（基于匹配质量和上下文）
                        confidence = self._calculate_pattern_confidence(pattern, context_text)
                        
                        if confidence > 0.3:  # 置信度阈值
                            key_point = KeyPoint(
                                text=context_text,
                                type=ktype,
                                confidence=confidence,
                                start_pos=start,
                                end_pos=end
                            )
                            key_points.append(key_point)
                            break  # 每行只提取一个该类型的知识点
            
            # 额外规则：识别定义性语句（包含"是"且结构简单）
            if '是' in line and len(line) < 100:
                # 简单定义检测
                if self._looks_like_definition(line):
                    key_point = KeyPoint(
                        text=line,
                        type="definition",
                        confidence=0.7,
                        start_pos=0,
                        end_pos=len(line)
                    )
                    key_points.append(key_point)
        
        # 去重（基于文本相似度）
        key_points = self._deduplicate_key_points(key_points)
        
        # 按置信度排序，取前5个
        key_points.sort(key=lambda x: x.confidence, reverse=True)
        return key_points[:5]
    
    def calculate_weight(self, text: str, key_points: List[KeyPoint], 
                        context: Dict = None) -> WeightScore:
        """
        计算权重分数
        
        Args:
            text: 文本内容
            key_points: 提取的关键知识点
            context: 上下文信息
            
        Returns:
            WeightScore: 权重分数详情
        """
        # 1. 信息密度（关键知识点密度）
        info_density = self._calculate_information_density(text, key_points)
        
        # 2. 知识类型权重（基于关键知识点类型）
        knowledge_type_score = self._calculate_knowledge_type_score(key_points)
        
        # 3. 结构完整性
        structure_score = self._calculate_structure_score(text)
        
        # 4. 独特性（基于关键词重复度）
        uniqueness_score = self._calculate_uniqueness_score(text, context)
        
        # 5. 实用性
        practicality_score = self._calculate_practicality_score(text, key_points)
        
        # 6. 权威性（默认0.5，如有来源可调整）
        authority_score = 0.5
        if context and 'source' in context:
            authority_score = self._calculate_authority_score(context['source'])
        
        # 加权计算总权重
        weights = {
            'information_density': 0.25,
            'knowledge_type': 0.20,
            'structure': 0.15,
            'uniqueness': 0.15,
            'practicality': 0.15,
            'authority': 0.10
        }
        
        overall = (
            info_density * weights['information_density'] +
            knowledge_type_score * weights['knowledge_type'] +
            structure_score * weights['structure'] +
            uniqueness_score * weights['uniqueness'] +
            practicality_score * weights['practicality'] +
            authority_score * weights['authority']
        )
        
        # 确保在0~1范围内
        overall = max(0.0, min(1.0, overall))
        
        return WeightScore(
            overall=overall,
            information_density=info_density,
            knowledge_type=knowledge_type_score,
            structure=structure_score,
            uniqueness=uniqueness_score,
            practicality=practicality_score,
            authority=authority_score
        )
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除常见低价值内容
        for pattern in self.low_value_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def _calculate_pattern_confidence(self, pattern: str, text: str) -> float:
        """计算模式匹配置信度"""
        # 简单实现：基于匹配位置和上下文长度
        confidence = 0.5
        
        # 上下文长度适中加分
        if 50 <= len(text) <= 300:
            confidence += 0.2
        
        # 包含特定关键词加分
        important_words = ['定义', '方法', '步骤', '技巧', '关键', '重要']
        for word in important_words:
            if word in text:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _looks_like_definition(self, text: str) -> bool:
        """判断是否像定义性语句"""
        # 简单规则：包含"是"且结构为"A是B"
        if '是' in text:
            parts = text.split('是')
            if len(parts) == 2:
                subject = parts[0].strip()
                definition = parts[1].strip()
                # 主语和定义都不为空，且长度适中
                if (subject and definition and 
                    len(subject) < 30 and len(definition) < 100):
                    return True
        return False
    
    def _deduplicate_key_points(self, key_points: List[KeyPoint]) -> List[KeyPoint]:
        """关键知识点去重"""
        unique_points = []
        seen_texts = set()
        
        for point in key_points:
            # 简化文本用于比较
            simple_text = re.sub(r'\s+', '', point.text)[:50]
            if simple_text not in seen_texts:
                seen_texts.add(simple_text)
                unique_points.append(point)
        
        return unique_points
    
    def _calculate_information_density(self, text: str, key_points: List[KeyPoint]) -> float:
        """计算信息密度"""
        if not text:
            return 0.0
        
        # 基于关键知识点数量和文本长度
        if len(key_points) == 0:
            return 0.2  # 无关键知识，低密度
        
        # 每100字符有关键知识点数
        chars_per_point = len(text) / max(1, len(key_points))
        
        if chars_per_point < 50:
            return 0.9  # 高密度
        elif chars_per_point < 150:
            return 0.7  # 中密度
        elif chars_per_point < 300:
            return 0.4  # 低密度
        else:
            return 0.2  # 极低密度
    
    def _calculate_knowledge_type_score(self, key_points: List[KeyPoint]) -> float:
        """计算知识类型权重分"""
        if not key_points:
            return 0.3  # 默认闲聊权重
        
        # 取最高权重的知识点类型
        best_score = 0.0
        for point in key_points:
            weight = self.knowledge_type_weights.get(point.type, 0.5)
            adjusted_weight = weight * point.confidence
            if adjusted_weight > best_score:
                best_score = adjusted_weight
        
        return best_score
    
    def _calculate_structure_score(self, text: str) -> float:
        """计算结构完整性"""
        lines = text.split('\n')
        
        # 检查是否有列表结构
        has_list = False
        list_indicators = ['•', '-', '*', '1.', '2.', '3.', '一、', '二、', '三、']
        for line in lines:
            line = line.strip()
            if any(line.startswith(indicator) for indicator in list_indicators):
                has_list = True
                break
        
        # 检查是否有分段
        has_paragraphs = len([l for l in lines if len(l.strip()) > 0]) > 1
        
        # 检查是否有标题
        has_title = False
        for line in lines[:3]:  # 只看前3行
            if len(line.strip()) < 50 and line.strip().endswith(('：', ':')):
                has_title = True
                break
        
        score = 0.3  # 基础分
        
        if has_list:
            score += 0.3
        if has_paragraphs:
            score += 0.2
        if has_title:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_uniqueness_score(self, text: str, context: Dict = None) -> float:
        """计算独特性"""
        # 简单实现：基于关键词重复度
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', text.lower())
        if not words:
            return 0.5
        
        # 计算词频，高频词过多则独特性低
        word_counts = Counter(words)
        most_common_count = word_counts.most_common(1)[0][1] if word_counts else 0
        
        if most_common_count > len(words) * 0.3:  # 某个词出现超过30%
            return 0.3
        elif most_common_count > len(words) * 0.2:  # 超过20%
            return 0.5
        elif most_common_count > len(words) * 0.1:  # 超过10%
            return 0.7
        else:
            return 0.9
    
    def _calculate_practicality_score(self, text: str, key_points: List[KeyPoint]) -> float:
        """计算实用性"""
        # 基于关键知识点类型和内容
        if not key_points:
            return 0.3
        
        practical_types = ['method', 'technique', 'syntax', 'warning']
        practical_count = sum(1 for p in key_points if p.type in practical_types)
        
        # 计算实用性比例
        practicality_ratio = practical_count / len(key_points)
        
        # 检查是否包含操作动词
        action_verbs = ['打开', '创建', '设置', '配置', '运行', '执行', '安装',
                       '使用', '操作', '点击', '输入', '选择', '保存']
        has_action = any(verb in text for verb in action_verbs)
        
        score = practicality_ratio * 0.7
        if has_action:
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_authority_score(self, source: str) -> float:
        """计算权威性（基于来源）"""
        # 简单实现：基于域名判断
        source_lower = source.lower()
        
        if any(domain in source_lower for domain in ['.gov.cn', '.edu.cn', '.ac.cn']):
            return 0.9
        elif any(domain in source_lower for domain in ['arxiv.org', 'ieee.org', 'springer.com']):
            return 0.8
        elif any(domain in source_lower for domain in ['wikipedia.org', 'baike.baidu.com']):
            return 0.7
        elif any(domain in source_lower for domain in ['zhihu.com', 'juejin.cn', 'csdn.net']):
            return 0.6
        elif any(domain in source_lower for domain in ['weibo.com', 'tieba.baidu.com']):
            return 0.4
        else:
            return 0.5
    
    def _generate_analysis_details(self, text: str, key_points: List[KeyPoint], 
                                  weight_score: WeightScore) -> Dict[str, Any]:
        """生成分析详情"""
        word_count = len(re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+', text))
        line_count = len([l for l in text.split('\n') if l.strip()])
        
        return {
            "word_count": word_count,
            "line_count": line_count,
            "key_point_count": len(key_points),
            "key_point_types": [kp.type for kp in key_points],
            "information_density_rating": self._get_rating_label(weight_score.information_density),
            "structure_rating": self._get_rating_label(weight_score.structure),
            "uniqueness_rating": self._get_rating_label(weight_score.uniqueness)
        }
    
    def _generate_recommendation(self, weight_score: WeightScore, 
                                key_points: List[KeyPoint], context: Dict = None) -> Dict[str, Any]:
        """生成推荐"""
        should_store = weight_score.overall >= 0.6
        
        # 确定存储优先级
        if weight_score.overall >= 0.8:
            priority = "high"
        elif weight_score.overall >= 0.6:
            priority = "medium"
        else:
            priority = "low"
        
        # 建议标签
        suggested_tags = []
        for point in key_points[:3]:
            tag = point.type
            if tag not in suggested_tags:
                suggested_tags.append(tag)
        
        # 添加内容类型标签
        if weight_score.practicality >= 0.7:
            suggested_tags.append("practical")
        if weight_score.knowledge_type >= 0.8:
            suggested_tags.append("core_knowledge")
        
        return {
            "should_store": should_store,
            "storage_priority": priority,
            "suggested_tags": suggested_tags,
            "confidence": weight_score.overall,
            "reasoning": self._generate_reasoning(weight_score, key_points)
        }
    
    def _generate_reasoning(self, weight_score: WeightScore, key_points: List[KeyPoint]) -> str:
        """生成推荐理由"""
        reasons = []
        
        if weight_score.information_density >= 0.7:
            reasons.append("信息密度高")
        elif weight_score.information_density <= 0.3:
            reasons.append("信息密度低")
        
        if weight_score.knowledge_type >= 0.8:
            reasons.append("知识类型权重高")
        
        if weight_score.structure >= 0.7:
            reasons.append("结构完整清晰")
        
        if weight_score.uniqueness >= 0.8:
            reasons.append("内容独特新颖")
        
        if weight_score.practicality >= 0.7:
            reasons.append("实用性强")
        
        if key_points:
            reasons.append(f"提取到{len(key_points)}个关键知识点")
        
        if reasons:
            return "；".join(reasons)
        else:
            return "内容质量一般"
    
    def _calculate_grade(self, score: float) -> str:
        """计算等级"""
        if score >= 0.8:
            return "A"
        elif score >= 0.6:
            return "B"
        else:
            return "C"
    
    def _get_rating_label(self, score: float) -> str:
        """获取评分标签"""
        if score >= 0.8:
            return "优秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "一般"
        else:
            return "较差"

# 命令行接口
def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='知识权重分析引擎')
    parser.add_argument('text', nargs='?', help='要分析的文本')
    parser.add_argument('--file', '-f', help='从文件读取文本')
    parser.add_argument('--context', '-c', help='JSON格式的上下文')
    parser.add_argument('--pretty', '-p', action='store_true', help='美化输出')
    
    args = parser.parse_args()
    
    # 获取文本
    text = ""
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        text = args.text
    elif not sys.stdin.isatty():
        # 从标准输入读取
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)
    
    # 解析上下文
    context = {}
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError as e:
            print(f"解析上下文失败: {e}", file=sys.stderr)
            sys.exit(1)
    
    # 执行分析
    analyzer = KnowledgeWeightAnalyzer()
    try:
        result = analyzer.analyze(text, context)
        
        # 转换为字典
        result_dict = {
            "weight_score": asdict(result.weight_score),
            "grade": result.grade,
            "key_points": [asdict(kp) for kp in result.key_points],
            "analysis": result.analysis,
            "recommendation": result.recommendation,
            "timestamp": result.timestamp,
            "version": result.version
        }
        
        # 输出
        if args.pretty:
            print(json.dumps(result_dict, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result_dict, ensure_ascii=False))
            
    except Exception as e:
        print(f"分析失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
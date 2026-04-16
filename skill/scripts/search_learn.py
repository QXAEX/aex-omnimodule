#!/usr/bin/env python3
"""
AEX全知模块 - 搜索与学习
负责自动搜索、深度验证、知识存储决策
"""

import json
import hashlib
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import asdict

# 动态检测根目录
SKILL_DIR = Path(__file__).resolve().parent.parent
_CANDIDATE = SKILL_DIR.parent / "db"
_FALLBACK = Path("D:/QClawAEXModule/db")
ROOT_DIR = _CANDIDATE if (_CANDIDATE.exists() or not _FALLBACK.exists()) else _FALLBACK

# 来源可信度评分
SOURCE_CREDIBILITY = {
    "official": 0.95,
    "academic": 0.90,
    "wiki": 0.75,
    "tech_blog": 0.70,
    "forum": 0.50,
    "social": 0.30,
    "unknown": 0.40
}


class SearchLearnManager:
    """搜索与学习管理器"""
    
    # 主题关键词映射
    TOPIC_KEYWORDS = {
        "Python": ["python", "py", "django", "flask", "pandas", "numpy", "decorator", "generator"],
        "CPlusPlus": ["c++", "cpp", "cplusplus", "stl", "qt", "opencv", "yolo", "darknet"],
        "Flutter": ["flutter", "dart", "widget", "material", "cupertino"],
        "AI": ["ai", "machine learning", "deep learning", "neural", "llm", "gpt", "transformer"],
        "Web": ["javascript", "html", "css", "react", "vue", "node", "typescript"],
        "Database": ["sql", "mysql", "postgresql", "mongodb", "redis", "database"],
        "Java": ["java", "spring", "hibernate", "jvm"],
        "Go": ["golang", "go", "goroutine"],
        "Rust": ["rust", "cargo", "ownership"],
        "Linux": ["linux", "ubuntu", "centos", "bash", "shell"],
    }

    def __init__(self, db_manager=None, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else ROOT_DIR
        
        if db_manager is None:
            try:
                # 尝试从同一目录导入 DatabaseManager
                from db_manager import DatabaseManager
                self.db_manager = DatabaseManager(root_dir=self.root_dir)
            except ImportError as e:
                print(f"[SearchLearnManager] 警告: 无法导入 db_manager: {e}")
                self.db_manager = None
        else:
            self.db_manager = db_manager
    
    def detect_topic(self, text: str) -> str:
        """检测文本主题"""
        if not text:
            return "general"
        
        text_lower = text.lower()
        
        # 统计关键词出现次数
        topic_scores = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            if score > 0:
                topic_scores[topic] = score
        
        # 找到最高分的主题
        if topic_scores:
            best_topic = max(topic_scores.items(), key=lambda x: x[1])[0]
            return best_topic
        
        return "general"  # 默认主题
    
    def ensure_topic_db(self, topic: str):
        """确保主题数据库存在"""
        if topic == "general":
            return  # 通用数据库已由 db_manager 管理
        
        # 检查数据库文件是否存在
        db_path = self.root_dir / f"{topic}.db"
        if not db_path.exists():
            print(f"[SearchLearnManager] 创建新主题数据库: {topic}.db")
            # 创建数据库文件
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    source TEXT,
                    credibility REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    weight REAL DEFAULT 0.5,
                    tags TEXT,
                    metadata TEXT
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at ON entries(created_at)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_weight ON entries(weight)
            ''')
            conn.close()
    
    def evaluate_source(self, url: str) -> float:
        """评估来源可信度，返回 0.0 ~ 1.0"""
        url_lower = url.lower()

        official_domains = [
            "gov.cn", "gov", "microsoft.com", "apple.com", "google.com",
            "github.com", "python.org", "mozilla.org", "w3.org"
        ]
        for domain in official_domains:
            if domain in url_lower:
                return SOURCE_CREDIBILITY["official"]

        academic_domains = ["scholar.google", "arxiv.org", "cnki.net", "doi.org", "ieee.org"]
        for domain in academic_domains:
            if domain in url_lower:
                return SOURCE_CREDIBILITY["academic"]

        if "wikipedia.org" in url_lower or "baike.baidu.com" in url_lower:
            return SOURCE_CREDIBILITY["wiki"]

        tech_domains = [
            "medium.com", "dev.to", "stackoverflow.com", "segmentfault.com",
            "juejin.cn", "zhihu.com", "csdn.net", "cnblogs.com"
        ]
        for domain in tech_domains:
            if domain in url_lower:
                return SOURCE_CREDIBILITY["tech_blog"]

        forum_domains = ["reddit.com", "tieba.baidu.com", "v2ex.com", "douyin.com"]
        for domain in forum_domains:
            if domain in url_lower:
                return SOURCE_CREDIBILITY["forum"]

        social_domains = ["weibo.com", "twitter.com", "tiktok.com", "x.com"]
        for domain in social_domains:
            if domain in url_lower:
                return SOURCE_CREDIBILITY["social"]

        return SOURCE_CREDIBILITY["unknown"]

    def cross_validate(self, results: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """交叉验证搜索结果"""
        trusted = []
        uncertain = []

        for result in results:
            content = result.get("content", "").strip()
            source = result.get("source", "unknown")

            if not content:
                continue

            credibility = self.evaluate_source(source)
            result["credibility"] = credibility

            if credibility >= 0.7:
                trusted.append(result)
            else:
                uncertain.append(result)

        trusted.sort(key=lambda x: x["credibility"], reverse=True)
        uncertain.sort(key=lambda x: x["credibility"], reverse=True)

        return trusted, uncertain

    def generate_content_hash(self, content: str) -> str:
        """生成内容指纹（用于重复检测）"""
        normalized = " ".join(content.split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def deep_process(self, query: str, results: List[Dict]) -> Dict:
        """深度处理搜索结果"""
        trusted, uncertain = self.cross_validate(results)
        all_results = trusted + uncertain

        consensus_points = []
        unique_points = []
        seen_hashes = set()

        for result in all_results:
            content_hash = self.generate_content_hash(result["content"])
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                if result["credibility"] >= 0.7:
                    consensus_points.append(result)
                else:
                    unique_points.append(result)

        processed = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "consensus": consensus_points,
            "unique": unique_points,
            "total_sources": len(all_results),
            "trusted_sources": len(trusted),
            "uncertain_sources": len(uncertain),
            "summary": self._generate_summary(consensus_points, unique_points)
        }

        return processed

    def _generate_summary(self, consensus: List[Dict], unique: List[Dict]) -> str:
        """生成知识摘要"""
        parts = []

        if consensus:
            parts.append(f"[高可信] {len(consensus)}个来源确认")
            for item in consensus[:3]:
                parts.append(f"  - {item['content'][:200]}")

        if unique:
            parts.append(f"[待验证] {len(unique)}个来源，需进一步确认")
            for item in unique[:3]:
                parts.append(f"  - {item['content'][:200]}")

        return "\n".join(parts)

    def store_knowledge(self, db_type: str, content: str, source: str = None,
                        metadata: Dict = None) -> int:
        """存储知识到数据库"""
        if self.db_manager is None:
            raise RuntimeError("DatabaseManager not initialized")

        credibility = self.evaluate_source(source) if source else 0.5

        entry_metadata = {
            "learned_at": datetime.now().isoformat(),
            "content_hash": self.generate_content_hash(content)
        }
        if metadata:
            entry_metadata.update(metadata)

        entry_id = self.db_manager.add_entry(
            db_type=db_type,
            content=content,
            source=source,
            credibility=credibility,
            metadata=entry_metadata
        )

        return entry_id

    def recall_knowledge(self, db_type: str, keyword: str = None, limit: int = 10) -> List[Dict]:
        """回忆知识"""
        if self.db_manager is None:
            raise RuntimeError("DatabaseManager not initialized")

        return self.db_manager.query_entries(db_type, keyword, limit)

    def is_knowledge_sufficient(self, db_type: str, keyword: str) -> bool:
        """检查是否已有足够知识"""
        results = self.recall_knowledge(db_type, keyword, limit=3)
        return len(results) > 0 and any(
            r["credibility_score"] >= 0.7 for r in results
        )
    
    def search(self, query: str, db_type: str = "core_knowledge", limit: int = 10) -> List[Dict]:
        """搜索知识（供插件调用）"""
        # 检测查询主题
        topic = self.detect_topic(query)
        
        # 如果检测到特定主题，优先搜索主题数据库
        if topic != "general":
            # 确保主题数据库存在
            self.ensure_topic_db(topic)
            
            # 搜索主题数据库
            topic_results = self.recall_knowledge(topic, query, limit)
            if topic_results:
                # 转换为插件期望的格式
                formatted = []
                for i, r in enumerate(topic_results):
                    formatted.append({
                        "id": r.get("id", i + 1),
                        "content": r.get("content", ""),
                        "source": r.get("source", "memory"),
                        "relevance": r.get("credibility_score", 0.5),
                        "topic": topic
                    })
                return formatted
        
        # 搜索通用数据库
        results = self.recall_knowledge(db_type, query, limit)
        # 转换为插件期望的格式
        formatted = []
        for i, r in enumerate(results):
            formatted.append({
                "id": r.get("id", i + 1),
                "content": r.get("content", ""),
                "source": r.get("source", "memory"),
                "relevance": r.get("credibility_score", 0.5),
                "topic": "general"
            })
        return formatted
    
    def evaluate_and_store(self, content: str, source: str = "conversation", 
                          db_type: str = "core_knowledge") -> int:
        """评估并存储对话内容（深度思考优化后存储）"""
        # 检测内容主题
        topic = self.detect_topic(content)
        
        # 如果检测到特定主题，使用主题数据库
        if topic != "general":
            db_type = topic
            # 确保主题数据库存在
            self.ensure_topic_db(topic)
        
        # 深度思考：生成摘要和关键点
        summary = self._generate_conversation_summary(content)
        
        # 评估内容价值
        value_score = self._evaluate_content_value(content)
        
        metadata = {
            "type": "conversation_learning",
            "summary": summary,
            "value_score": value_score,
            "processed_at": datetime.now().isoformat(),
            "topic": topic if topic != "general" else "general"
        }
        
        # 存储到知识库
        return self.store_knowledge(
            db_type=db_type,
            content=content,
            source=source,
            metadata=metadata
        )
    
    def process_conversation(self, question: str, answer: str, source: str = "conversation", 
                            threshold: float = 0.45) -> Dict[str, Any]:
        """
        处理完整对话，分析权重，结构化存储知识
        
        Args:
            question: 用户问题
            answer: AI回答
            source: 来源
            threshold: 存储阈值 (默认0.7)
            
        Returns:
            Dict: 处理结果，包含存储状态和分析信息
        """
        from knowledge_weight_analyzer import KnowledgeWeightAnalyzer
        
        # 1. 拼接对话
        conversation = f"Q: {question}\nA: {answer}"
        
        # 2. 分析权重
        analyzer = KnowledgeWeightAnalyzer()
        context = {"source": source} if source else {}
        analysis_result = analyzer.analyze(conversation, context)
        
        weight_score = analysis_result.weight_score.overall
        grade = analysis_result.grade
        
        result = {
            "processed_at": datetime.now().isoformat(),
            "weight_score": weight_score,
            "grade": grade,
            "threshold": threshold,
            "key_points_count": len(analysis_result.key_points),
            "recommendation": analysis_result.recommendation,
            "storage_status": "not_stored"
        }
        
        # 3. 阈值判断
        if weight_score >= threshold:
            # 4. 结构化存储
            storage_result = self._store_structured_knowledge(
                question=question,
                answer=answer,
                analysis_result=analysis_result,
                source=source
            )
            result["storage_status"] = "stored"
            result["storage_details"] = storage_result
        
        return result
    
    def _store_structured_knowledge(self, question: str, answer: str, 
                                   analysis_result, source: str) -> Dict[str, Any]:
        """结构化存储知识（摘要 + 关键知识点 + 完整对话可选）"""
        from knowledge_weight_analyzer import KeyPoint
        
        # 提取关键知识点文本
        key_points_text = []
        for kp in analysis_result.key_points:
            if isinstance(kp, KeyPoint):
                kp_text = kp.text
            elif isinstance(kp, dict):
                kp_text = kp.get("text", "")
            else:
                continue
            key_points_text.append(f"- {kp_text}")
        
        # 生成知识摘要
        summary = f"问题: {question[:200]}\n关键知识点:\n" + "\n".join(key_points_text[:5])
        
        # 决定是否存储完整对话（权重≥0.9时存储）
        store_full_conversation = analysis_result.weight_score.overall >= 0.9
        
        # 元数据
        metadata = {
            "type": "structured_knowledge",
            "question": question[:500],
            "answer_summary": answer[:1000],
            "key_points": [asdict(kp) if hasattr(kp, '__dataclass_fields__') else kp 
                          for kp in analysis_result.key_points],
            "weight_score": analysis_result.weight_score.overall,
            "grade": analysis_result.grade,
            "store_full_conversation": store_full_conversation,
            "processed_at": datetime.now().isoformat()
        }
        
        # 存储摘要到核心知识库
        entry_id = None
        if self.db_manager:
            try:
                entry_id = self.db_manager.add_entry(
                    db_type="core_knowledge",
                    content=summary,
                    source=source,
                    credibility=analysis_result.weight_score.overall,
                    metadata=metadata
                )
                
                # 如果需要，存储完整对话到对话库
                if store_full_conversation:
                    conv_metadata = {
                        "type": "full_conversation",
                        "knowledge_id": entry_id,
                        "weight_score": analysis_result.weight_score.overall,
                        "processed_at": datetime.now().isoformat()
                    }
                    self.db_manager.add_entry(
                        db_type="conversations",
                        content=f"Q: {question}\nA: {answer}",
                        source=source,
                        credibility=analysis_result.weight_score.overall,
                        metadata=conv_metadata
                    )
            except Exception as e:
                print(f"[_store_structured_knowledge] 存储失败: {e}")
                entry_id = None
        
        return {
            "entry_id": entry_id,
            "summary_length": len(summary),
            "key_points_count": len(analysis_result.key_points),
            "store_full_conversation": store_full_conversation,
            "database_available": self.db_manager is not None
        }
    
    def _generate_conversation_summary(self, content: str) -> str:
        """生成对话摘要（简化版，后续可优化）"""
        # 简单实现：取前500字符作为摘要
        # 实际应使用NLP技术提取关键信息
        if len(content) > 500:
            return content[:497] + "..."
        return content
    
    def _evaluate_content_value(self, content: str) -> float:
        """评估内容价值 0.0~1.0"""
        # 简单启发式评估
        value = 0.3  # 基础值
        
        # 长度因子
        length = len(content)
        if length > 1000:
            value += 0.2
        elif length > 500:
            value += 0.1
        
        # 包含特定关键词（示例）
        important_keywords = ["如何", "为什么", "方法", "步骤", "总结", "重要", "关键"]
        for keyword in important_keywords:
            if keyword in content:
                value += 0.05
        
        return min(value, 1.0)


if __name__ == "__main__":
    import sys
    
    slm = SearchLearnManager()
    
    if len(sys.argv) > 1:
        # 命令行参数：查询字符串
        mode = sys.argv[1]
        
        if mode == "--conversation" and len(sys.argv) >= 4:
            # 处理对话：--conversation <question> <answer> [source] [threshold]
            question = sys.argv[2]
            answer = sys.argv[3]
            source = sys.argv[4] if len(sys.argv) > 4 else "conversation"
            threshold = float(sys.argv[5]) if len(sys.argv) > 5 else 0.45
            
            result = slm.process_conversation(question, answer, source, threshold)
            print(json.dumps(result, ensure_ascii=False))
            
        elif mode == "--store" and len(sys.argv) > 3:
            # 存储内容
            content = sys.argv[2]
            source = sys.argv[3] if len(sys.argv) > 3 else "conversation"
            entry_id = slm.evaluate_and_store(content, source)
            print(json.dumps({"status": "stored", "id": entry_id}, ensure_ascii=False))
            
        else:
            # 普通搜索（第一个参数不是特殊标志时）
            query = mode
            results = slm.search(query)
            print(json.dumps(results, ensure_ascii=False))
    else:
        # 演示模式
        print("SearchLearnManager initialized - 支持以下模式:")
        print("  1. 搜索: python search_learn.py '查询词'")
        print("  2. 存储: python search_learn.py --store '内容' '来源'")
        print("  3. 对话处理: python search_learn.py --conversation '问题' '回答' [来源] [阈值]")
        print()
        print("示例测试:")
        urls = [
            "https://www.python.org/doc/",
            "https://arxiv.org/abs/1234",
            "https://www.weibo.com/test",
            "https://example.com/unknown"
        ]
        for url in urls:
            score = slm.evaluate_source(url)
            print(f"  {url}: {score}")

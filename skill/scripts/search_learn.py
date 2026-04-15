#!/usr/bin/env python3
"""
AEX全知模块 - 搜索与学习
负责自动搜索、深度验证、知识存储决策
"""

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

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

    def __init__(self, db_manager=None, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else ROOT_DIR
        self.db_manager = db_manager

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


if __name__ == "__main__":
    slm = SearchLearnManager()
    print("SearchLearnManager initialized")

    urls = [
        "https://www.python.org/doc/",
        "https://arxiv.org/abs/1234",
        "https://www.weibo.com/test",
        "https://example.com/unknown"
    ]
    for url in urls:
        score = slm.evaluate_source(url)
        print(f"  {url}: {score}")

#!/usr/bin/env python3
"""
AEX全知模块 - 情绪分析
通过文字自动分析用户情绪，提供语气调整建议
"""

import re
from typing import Dict, Tuple, List
from enum import Enum


class EmotionType(Enum):
    """情绪类型"""
    HAPPY = "happy"
    EXCITED = "excited"
    CALM = "calm"
    NEUTRAL = "neutral"
    THINKING = "thinking"
    CONFUSED = "confused"
    WORRIED = "worried"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    SAD = "sad"
    SARCASTIC = "sarcastic"
    URGENT = "urgent"


# 情绪关键词映射
EMOTION_KEYWORDS = {
    EmotionType.HAPPY: [
        "哈哈", "太好了", "开心", "棒", "厉害", "不错", "好的", "谢谢",
        "赞", "nice", "happy", "great", "awesome", "love", "喜欢", "满意",
        "可以", "行", "ok", "yes"
    ],
    EmotionType.EXCITED: [
        "！！！", "！！！ ", "卧槽", "我去", "牛逼", "绝了", "太强了",
        "666", "nb", "牛", "无敌", "太棒了", "!", "wtf", "omg",
        "简直", "真的是", "太不可思议"
    ],
    EmotionType.CALM: [
        "嗯", "好的", "收到", "了解", "明白", "嗯嗯", "行吧", "可以",
        "随便", "都行", "无所谓的", "你看着办", "嗯，", "知道了"
    ],
    EmotionType.THINKING: [
        "我想想", "考虑一下", "等等", "让我想想", "不确定", "也许",
        "可能", "大概", "应该", "或者", "还是", "你觉得呢", "怎么看",
        "分析一下", "对比", "比较"
    ],
    EmotionType.CONFUSED: [
        "什么意思", "不懂", "不明白", "啥", "？", "为什么", "怎么",
        "搞不懂", "看不懂", "啥意思", "什么鬼", "啊？", "这是啥"
    ],
    EmotionType.WORRIED: [
        "担心", "怕", "万一", "风险", "不安全", "有问题吗", "靠谱吗",
        "会不会", "后果", "严重吗", "有危险吗", "能不能"
    ],
    EmotionType.FRUSTRATED: [
        "烦", "受不了", "够了", "又", "怎么又", "老是", "总是",
        "无语", "算了", "不想", "懒得", "搞什么", "什么破"
    ],
    EmotionType.ANGRY: [
        "滚", "闭嘴", "废物", "垃圾", "蠢", "sb", "傻逼", "他妈",
        "妈的", "草", "fuck", "你懂什么", "别废话", "少废话",
        "你脑子有病", "白痴", "弱智", "神经病"
    ],
    EmotionType.SAD: [
        "难过", "伤心", "失望", "难受", "心痛", "可惜", "遗憾",
        "哭", "眼泪", "孤独", "寂寞", "累", "撑不住", "太累了"
    ],
    EmotionType.SARCASTIC: [
        "呵呵", "笑死", "厉害了", "就这", "行吧", "那你厉害",
        "随便你", "好吧", "是是是", "对对对", "您说的都对",
        "不愧是", "真是", "太真实了"
    ],
    EmotionType.URGENT: [
        "赶紧", "快点", "马上", "立刻", "现在", "急", "等不了",
        "不能等", "火烧眉毛", "紧急", "重要", "赶紧的", "马上要"
    ]
}

# 情绪对应的语气建议
TONE_SUGGESTIONS = {
    EmotionType.HAPPY: {
        "tone": "轻松愉快",
        "style": "可以适当幽默，分享喜悦，语气活泼",
        "approach": "正面回应，保持积极氛围"
    },
    EmotionType.EXCITED: {
        "tone": "热情激昂",
        "style": "匹配用户的兴奋度，但也适当降温保持理性",
        "approach": "一起兴奋，然后引导到具体行动"
    },
    EmotionType.CALM: {
        "tone": "平和稳重",
        "style": "简洁直接，不废话，高效沟通",
        "approach": "直接给结果，少铺垫"
    },
    EmotionType.NEUTRAL: {
        "tone": "专业中性",
        "style": "标准回复，清晰有条理",
        "approach": "直接回答问题"
    },
    EmotionType.THINKING: {
        "tone": "理性分析",
        "style": "帮助梳理思路，提供多角度视角",
        "approach": "提供结构化分析，帮助做决策"
    },
    EmotionType.CONFUSED: {
        "tone": "耐心解释",
        "style": "用简单的语言解释，一步步引导",
        "approach": "先确认哪里不懂，再针对性解答"
    },
    EmotionType.WORRIED: {
        "tone": "安心稳重",
        "style": "承认风险但给出解决方案，不要轻视担忧",
        "approach": "分析风险 + 提供应对方案"
    },
    EmotionType.FRUSTRATED: {
        "tone": "理解共情",
        "style": "先共情，再解决问题，不要急着给建议",
        "approach": "承认痛点，然后提出解决方案"
    },
    EmotionType.ANGRY: {
        "tone": "冷静应对",
        "style": "不要反驳或讨好，理性回应，可以适当互怼",
        "approach": "如果是我的错就认，不是就据理力争"
    },
    EmotionType.SAD: {
        "tone": "温暖陪伴",
        "style": "不要急着讲道理，先倾听和理解",
        "approach": "表达理解，陪伴，不打扰"
    },
    EmotionType.SARCASTIC: {
        "tone": "机智应对",
        "style": "接住梗，可以反讽回去，保持幽默",
        "approach": "以幽默化解或对线"
    },
    EmotionType.URGENT: {
        "tone": "高效直接",
        "style": "跳过寒暄，直接给核心信息",
        "approach": "快速响应，先解决紧急问题"
    }
}


class EmotionAnalyzer:
    """情绪分析器"""

    def analyze(self, text: str) -> Dict:
        """
        分析文本情绪
        返回: {
            "emotion": EmotionType,
            "confidence": float,
            "detected_keywords": list,
            "intensity": float,
            "tone_suggestion": dict
        }
        """
        text_lower = text.lower()

        scores = {}
        detected = {}

        for emotion, keywords in EMOTION_KEYWORDS.items():
            matched = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched.append(keyword)

            if matched:
                scores[emotion] = len(matched)
                detected[emotion] = matched

        if not scores:
            return {
                "emotion": EmotionType.NEUTRAL,
                "confidence": 0.5,
                "detected_keywords": [],
                "intensity": 0.1,
                "tone_suggestion": TONE_SUGGESTIONS[EmotionType.NEUTRAL]
            }

        # 找到得分最高的情绪
        primary_emotion = max(scores, key=scores.get)
        total_matches = sum(scores.values())
        confidence = scores[primary_emotion] / total_matches

        # 强度分析：基于标点和重复字符
        intensity = self._calc_intensity(text)

        return {
            "emotion": primary_emotion,
            "confidence": min(confidence * 1.5, 1.0),
            "detected_keywords": detected.get(primary_emotion, []),
            "intensity": min(intensity, 1.0),
            "tone_suggestion": TONE_SUGGESTIONS[primary_emotion]
        }

    def _calc_intensity(self, text: str) -> float:
        """计算情绪强度"""
        intensity = 0.3  # 基础强度

        # 感叹号增加强度
        excl = text.count("!")
        intensity += min(excl * 0.1, 0.3)

        # 问号增加强度（焦虑）
        ques = text.count("?") + text.count("？")
        intensity += min(ques * 0.05, 0.15)

        # 重复字符（啊啊啊, 哈哈哈）
        for pattern in [r"(.)\1{2,}"]:
            repeats = re.findall(pattern, text)
            intensity += min(len(repeats) * 0.1, 0.2)

        # 大写字母（英文场景）
        upper_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if upper_ratio > 0.3:
            intensity += 0.2

        return intensity

    def get_response_strategy(self, emotion_result: Dict) -> str:
        """获取回复策略建议"""
        emotion = emotion_result["emotion"]
        intensity = emotion_result["intensity"]
        suggestion = emotion_result["tone_suggestion"]

        parts = [f"情绪: {emotion.value} (强度: {intensity:.0%})"]
        parts.append(f"建议语气: {suggestion['tone']}")
        parts.append(f"风格: {suggestion['style']}")
        parts.append(f"策略: {suggestion['approach']}")

        return "\n".join(parts)


if __name__ == "__main__":
    # 测试
    ea = EmotionAnalyzer()

    test_texts = [
        "哈哈太好了谢谢",
        "卧槽牛逼！！！",
        "我不太确定，你觉得呢",
        "烦死了又出bug",
        "你懂个屁啊废物",
        "我不开心，有点累",
        "赶紧的，马上要交",
        "呵呵你开心就好"
    ]

    for text in test_texts:
        result = ea.analyze(text)
        strategy = ea.get_response_strategy(result)
        print(f"\n输入: {text}")
        print(strategy)

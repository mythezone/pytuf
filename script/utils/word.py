"""
Utilities for Chinese text normalization.

Function: convert_traditional_to_simplified(text)
- If the input is Traditional Chinese, return its Simplified variant.
- Otherwise, return the original text unchanged.

Lightweight first: prefer zhconv (small dependency). If zhconv is not
available, try OpenCC (t2s). If neither is installed, use a tiny
character mapping as a last resort and only return the converted string
when any character actually changed.
"""
from __future__ import annotations

from typing import Callable


_converter: Callable[[str], str] | None = None


def _init_converter() -> Callable[[str], str] | None:
    """Try to initialize a Traditional->Simplified converter.

    Order: zhconv (lightweight) -> opencc-python-reimplemented -> None
    """
    # 1) zhconv: pip install zhconv
    try:
        import zhconv  # type: ignore

        def _zhconv_t2s(text: str) -> str:
            # zhconv only has 'zhconv.convert(text, 'zh-cn')'
            return zhconv.convert(text, "zh-cn")

        return _zhconv_t2s
    except Exception:
        pass

    # 2) OpenCC (heavier but comprehensive): pip install opencc-python-reimplemented
    try:
        from opencc import OpenCC  # type: ignore

        cc = OpenCC("t2s")

        def _opencc_t2s(text: str) -> str:
            return cc.convert(text)

        return _opencc_t2s
    except Exception:
        pass

    # 3) Fallback: minimal static map (best-effort)
    _fallback_map = {
        "萬": "万",
        "與": "与",
        "為": "为",
        "內": "内",
        "兩": "两",
        "體": "体",
        "個": "个",
        "億": "亿",
        "優": "优",
        "會": "会",
        "價": "价",
        "傳": "传",
        "倫": "伦",
        "兒": "儿",
        "寫": "写",
        "冷": "冷",  # same in both (placeholder to illustrate no-change)
        "區": "区",
        "醫": "医",
        "歷": "历",
        "壞": "坏",
        "壓": "压",
        "壘": "垒",
        "國": "国",
        "圖": "图",
        "報": "报",
        "場": "场",
        "壽": "寿",
        "專": "专",
        "對": "对",
        "將": "将",
        "層": "层",
        "歲": "岁",
        "廣": "广",
        "廠": "厂",
        "應": "应",
        "愛": "爱",
        "戶": "户",
        "戰": "战",
        "戶": "户",
        "據": "据",
        "時": "时",
        "曆": "历",
        "會": "会",
        "標": "标",
        "橋": "桥",
        "歡": "欢",
        "氣": "气",
        "況": "况",
        "測": "测",
        "灣": "湾",
        "燈": "灯",
        "牆": "墙",
        "畫": "画",
        "發": "发",
        "變": "变",
        "點": "点",
        "為": "为",
        "國": "国",
        "臺": "台",
        "臺灣": "台湾",
        "協": "协",
        "經": "经",
        "網": "网",
        "臺": "台",
        "藝": "艺",
        "蘋": "苹",
        "蘇": "苏",
        "藥": "药",
        "觀": "观",
        "語": "语",
        "貝": "贝",
        "財": "财",
        "責": "责",
        "負": "负",
        "貓": "猫",
        "貴": "贵",
        "買": "买",
        "車": "车",
        "軟": "软",
        "達": "达",
        "週": "周",
        "遊": "游",
        "過": "过",
        "還": "还",
        "這": "这",
        "進": "进",
        "遠": "远",
        "電": "电",
        "體": "体",
        "麼": "么",
    }

    def _mini_map(text: str) -> str:
        return "".join(_fallback_map.get(ch, ch) for ch in text)

    return _mini_map


def convert_traditional_to_simplified(text: str) -> str:
    """
    Convert Traditional Chinese to Simplified Chinese when the input appears
    to be Traditional; otherwise, return the original string.

    Heuristic: perform a t2s conversion and only return it if at least one
    character changed. This avoids altering already-simplified or non-Chinese
    text.
    """
    global _converter
    if not isinstance(text, str) or not text:
        return text

    if _converter is None:
        _converter = _init_converter()
    if _converter is None:
        # No converter available; return original
        return text

    converted = _converter(text)
    # Only return when conversion changed at least one character
    if converted != text:
        return converted
    return text


__all__ = ["convert_traditional_to_simplified"]

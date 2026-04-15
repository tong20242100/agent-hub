#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X Article Fetcher - 获取 X/Twitter Article 完整内容

功能:
- 获取文章标题、正文、摘要
- 获取所有图片 URL（封面 + 文章内）
- 复用 xreach 的认证信息

用法:
    python3 x_article.py <article_url_or_id>
    python3 x_article.py https://x.com/i/article/2033941492633362432
    python3 x_article.py 2033941492633362432

输出 JSON 格式:
{
    "id": "2033941492633362432",
    "title": "文章标题",
    "plain_text": "纯文本正文",
    "summary_text": "AI 生成的摘要",
    "cover_image": {"url": "...", "width": 3280, "height": 1312},
    "images": [{"url": "...", "width": 1376, "height": 768}, ...],
    "author": {"screen_name": "...", "name": "..."},
    "published_at": "2026-03-17T17:08:16Z",
    "stats": {"views": 1000000, "likes": 2941, "retweets": 666}
}
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import quote

import requests

# X GraphQL API 配置
TWEET_RESULT_API = "https://x.com/i/api/graphql/zy39CwTyYhU-_0LP7dljjg/TweetResultByRestId"
ARTICLE_REDIRECT_API = "https://x.com/i/api/graphql/zrSRXJmE1vj37AUmkh2oGg/ArticleRedirectScreenQuery"
PUBLIC_BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

# 请求参数
VARIABLES = {
    "includePromotedContent": True,
    "withBirdwatchNotes": True,
    "withVoice": True,
    "withCommunity": True
}

FEATURES = {
    "articles_preview_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True
}

FIELD_TOGGLES = {
    "withArticleRichContentState": True,
    "withArticlePlainText": True,
    "withArticleSummaryText": True,
    "withArticleVoiceOver": True
}


def get_xreach_session() -> Dict[str, str]:
    """从 xreach 读取认证信息"""
    session_path = Path.home() / ".xreach" / "session.json"
    
    if not session_path.exists():
        raise RuntimeError(
            "未找到 xreach 认证信息。请先运行: xreach auth extract --browser chrome"
        )
    
    with open(session_path) as f:
        return json.load(f)


def extract_article_id(url_or_id: str) -> str:
    """从 URL 或 ID 提取文章 ID"""
    # 尝试匹配 /i/article/ID 格式
    match = re.search(r'/i/article/(\d+)', url_or_id)
    if match:
        return match.group(1)
    
    # 尝试匹配 /status/ID 格式 (推文 ID)
    match = re.search(r'/status/(\d+)', url_or_id)
    if match:
        return match.group(1)
    
    # 纯数字 ID
    if url_or_id.isdigit():
        return url_or_id
    
    raise ValueError(f"无法解析 ID: {url_or_id}")


def is_article_url(url_or_id: str) -> bool:
    """判断是否是 Article URL"""
    return '/i/article/' in url_or_id


def get_tweet_id_from_article(article_id: str, auth_token: str, ct0: str) -> str:
    """通过 Article ID 获取关联的推文 ID"""
    
    variables = {"articleEntityId": article_id}
    # 使用 separators 去掉空格，匹配 X API 期望的格式
    params_str = f"variables={quote(json.dumps(variables, separators=(',', ':')))}"
    url = f"{ARTICLE_REDIRECT_API}?{params_str}"
    
    headers = {
        "authorization": f"Bearer {PUBLIC_BEARER}",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
        "x-csrf-token": ct0,
        "cookie": f"auth_token={auth_token}; ct0={ct0}",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    
    data = resp.json()
    
    try:
        tweet_results = data["data"]["article_result_by_rest_id"]["result"]["metadata"]["tweet_results"]
        return tweet_results["rest_id"]
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"无法获取文章关联的推文 ID: {e}")


def fetch_article(article_id: str, auth_token: str, ct0: str) -> Dict[str, Any]:
    """调用 X GraphQL API 获取文章"""
    
    variables = {**VARIABLES, "tweetId": article_id}
    
    # 手动构建 URL 参数，使用 separators 去掉空格
    params_str = "&".join([
        f"variables={quote(json.dumps(variables, separators=(',', ':')))}",
        f"features={quote(json.dumps(FEATURES, separators=(',', ':')))}",
        f"fieldToggles={quote(json.dumps(FIELD_TOGGLES, separators=(',', ':')))}"
    ])
    
    url = f"{TWEET_RESULT_API}?{params_str}"
    
    headers = {
        "authorization": f"Bearer {PUBLIC_BEARER}",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
        "x-csrf-token": ct0,
        "cookie": f"auth_token={auth_token}; ct0={ct0}",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    
    return resp.json()


def parse_article_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """解析 API 响应，提取文章内容"""
    
    try:
        tweet_result = data["data"]["tweetResult"]["result"]
        article = tweet_result["article"]["article_results"]["result"]
    except (KeyError, TypeError) as e:
        # 检查是否是普通推文（非 Article）
        if "article" not in tweet_result:
            return {
                "error": "这不是一篇 Article，而是普通推文。请使用 xreach tweet 命令。",
                "is_article": False
            }
        raise RuntimeError(f"解析响应失败: {e}")
    
    # 提取封面图片
    cover_media = article.get("cover_media", {}).get("media_info", {})
    cover_image = None
    if cover_media:
        cover_image = {
            "url": cover_media.get("original_img_url"),
            "width": cover_media.get("original_img_width"),
            "height": cover_media.get("original_img_height")
        }
    
    # 提取文章内图片
    images = []
    for media in article.get("media_entities", []):
        info = media.get("media_info", {})
        if info.get("original_img_url"):
            images.append({
                "url": info["original_img_url"],
                "width": info.get("original_img_width"),
                "height": info.get("original_img_height")
            })
    
    # 提取作者信息
    author = {}
    try:
        user_results = tweet_result.get("core", {}).get("user_results", {}).get("result", {})
        author = {
            "screen_name": user_results.get("core", {}).get("screen_name", ""),
            "name": user_results.get("core", {}).get("name", "")
        }
    except (KeyError, TypeError):
        pass
    
    # 提取发布时间
    published_at = None
    meta = article.get("metadata", {})
    if meta.get("first_published_at_secs"):
        published_at = datetime.utcfromtimestamp(
            meta["first_published_at_secs"]
        ).isoformat() + "Z"
    
    # 提取统计数据
    stats = {}
    legacy = tweet_result.get("legacy", {})
    if legacy:
        stats = {
            "views": legacy.get("views", {}).get("count", 0),
            "likes": legacy.get("favorite_count", 0),
            "retweets": legacy.get("retweet_count", 0),
            "replies": legacy.get("reply_count", 0)
        }
    
    # 提取结构化内容 (blocks)
    content_blocks = []
    for block in article.get("content_state", {}).get("blocks", []):
        if block.get("text", "").strip():
            content_blocks.append({
                "type": block.get("type"),
                "text": block.get("text")
            })
    
    return {
        "id": article.get("rest_id"),
        "title": article.get("title"),
        "plain_text": article.get("plain_text"),
        "summary_text": article.get("summary_text"),
        "preview_text": article.get("preview_text"),
        "cover_image": cover_image,
        "images": images,
        "author": author,
        "published_at": published_at,
        "stats": stats,
        "content_blocks": content_blocks,
        "is_article": True
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    url_or_id = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "json"
    
    try:
        # 获取认证
        session = get_xreach_session()
        auth_token = session["authToken"]
        ct0 = session["ct0"]
        
        # 提取 ID
        entity_id = extract_article_id(url_or_id)
        
        # 判断是 Article URL 还是 Tweet URL
        if is_article_url(url_or_id):
            # Article URL: 需要先获取关联的推文 ID
            tweet_id = get_tweet_id_from_article(entity_id, auth_token, ct0)
        else:
            # Tweet URL 或 ID: 直接使用
            tweet_id = entity_id
        
        # 获取文章内容
        raw_data = fetch_article(tweet_id, auth_token, ct0)
        
        # 解析结果
        result = parse_article_response(raw_data)
        
        # 输出
        if output_format == "text":
            print(f"标题: {result.get('title', 'N/A')}")
            print(f"作者: @{result.get('author', {}).get('screen_name', 'N/A')}")
            print(f"发布时间: {result.get('published_at', 'N/A')}")
            print(f"\n{'='*50}")
            print(result.get('plain_text', '无内容'))
            if result.get('images'):
                print(f"\n{'='*50}")
                print(f"图片 ({len(result['images'])} 张):")
                for i, img in enumerate(result['images'], 1):
                    print(f"  {i}. {img['url']}")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
    except Exception as e:
        error_result = {"error": str(e), "success": False}
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
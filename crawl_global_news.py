#!/usr/bin/env python3
"""全球热点新闻和GitHub项目爬取器"""
import urllib.request
import json
import datetime
import time
import re
import base64
import os

def fetch_url(url, timeout=15):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; GlobalNewsBot/1.0)'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f'  Error fetching {url}: {e}')
        return None

def crawl_hacker_news():
    """Hacker News 热门"""
    print('[1/4] Hacker News...')
    html = fetch_url('https://news.ycombinator.com/')
    if not html:
        return []
    results = []
    # 简单正则提取
    title_pattern = re.compile(r'class="titleline"><a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>')
    matches = title_pattern.findall(html)
    for link, title in matches[:15]:
        if not link.startswith('http'):
            link = 'https://news.ycombinator.com/' + link
        results.append({
            'title': title.strip(),
            'link': link,
            'source': 'Hacker News',
            'category': 'Tech'
        })
    print(f'  Got {len(results)} items')
    return results

def crawl_reddit_technology():
    """Reddit r/technology"""
    print('[2/4] Reddit r/technology...')
    results = []
    try:
        req = urllib.request.Request(
            'https://www.reddit.com/r/technology/top.json?limit=15&t=day',
            headers={'User-Agent': 'GlobalNewsBot/1.0'}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        posts = data.get('data', {}).get('children', [])
        for post in posts:
            pd = post.get('data', {})
            results.append({
                'title': pd.get('title', ''),
                'link': f'https://reddit.com{pd.get("permalink", "")}',
                'source': 'Reddit r/technology',
                'category': 'Tech',
                'score': pd.get('score', 0)
            })
    except Exception as e:
        print(f'  Error: {e}')
    print(f'  Got {len(results)} items')
    return results

def crawl_github_trending():
    """GitHub Trending"""
    print('[3/4] GitHub Trending...')
    results = []
    html = fetch_url('https://github.com/trending')
    if not html:
        return []
    # 提取项目信息
    repo_pattern = re.compile(r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"')
    desc_pattern = re.compile(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', re.DOTALL)
    star_pattern = re.compile(r'<a[^>]*class="Link--muted[^"]*"[^>]*>\s*<svg[^>]*>.*?</svg>\s*([\d,]+)', re.DOTALL)
    lang_pattern = re.compile(r'<span itemprop="programmingLanguage">([^<]+)</span>')
    
    repos = repo_pattern.findall(html)
    descs = desc_pattern.findall(html)
    stars = star_pattern.findall(html)
    langs = lang_pattern.findall(html)
    
    for i, repo in enumerate(repos[:15]):
        desc = descs[i].strip() if i < len(descs) else 'N/A'
        star = stars[i].strip() if i < len(stars) else '0'
        lang = langs[i].strip() if i < len(langs) else 'N/A'
        results.append({
            'name': repo,
            'description': desc,
            'language': lang,
            'stars': star,
            'link': f'https://github.com/{repo}',
            'source': 'GitHub Trending'
        })
    print(f'  Got {len(results)} projects')
    return results

def crawl_producthunt():
    """Product Hunt"""
    print('[4/4] Product Hunt...')
    results = []
    html = fetch_url('https://www.producthunt.com/')
    if not html:
        return []
    # 简单提取
    title_pattern = re.compile(r'data-test="post-name"[^>]*>([^<]+)<')
    link_pattern = re.compile(r'data-test="post-link"[^>]*href="([^"]+)"')
    titles = title_pattern.findall(html)
    links = link_pattern.findall(html)
    for i, title in enumerate(titles[:10]):
        link = links[i] if i < len(links) else ''
        if link and not link.startswith('http'):
            link = 'https://www.producthunt.com' + link
        results.append({
            'title': title.strip(),
            'link': link,
            'source': 'Product Hunt',
            'category': 'Product'
        })
    print(f'  Got {len(results)} items')
    return results

def generate_report(news, github_projects):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    report = f'# {today} 全球热点日报

' 
    report += '> 自动爬取，每天早8点发送到 635503886@qq.com

'
    
    # News section
    report += '## 📰 全球科技热点

'
    
    sources = {}
    for n in news:
        s = n['source']
        if s not in sources:
            sources[s] = []
        sources[s].append(n)
    
    for source, items in sources.items():
        report += f'### {source}

'
        for i, item in enumerate(items[:10], 1):
            score_info = f' (👍 {item["score"]})' if 'score' in item else ''
            report += f'{i}. **{item["title"]}**{score_info}
'
            if item.get('link'):
                report += f'   [链接]({item["link"]})
'
        report += '
'
    
    # GitHub section
    report += '## 🔥 GitHub 热门项目

'
    if github_projects:
        report += '| # | 项目 | 语言 | ⭐ Stars | 简介 |
'
        report += '|---|------|------|----------|------|
'
        for i, p in enumerate(github_projects[:15], 1):
            name = p['name']
            lang = p.get('language', 'N/A')
            stars = p.get('stars', '0')
            desc = p.get('description', '')[:60]
            report += f'| {i} | [{name}]({p["link"]}) | {lang} | {stars} | {desc} |
'
    else:
        report += '暂无数据
'
    
    report += f'
---
*共采集 {len(news)} 条新闻，{len(github_projects)} 个GitHub项目*
'
    return report

def main():
    print('=== 全球热点爬取开始 ===')
    start = time.time()
    
    news = []
    news.extend(crawl_hacker_news())
    time.sleep(1)
    news.extend(crawl_reddit_technology())
    time.sleep(1)
    news.extend(crawl_producthunt())
    
    github = crawl_github_trending()
    
    report = generate_report(news, github)
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    md_file = f'daily_{today}.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'
Report saved to {md_file}')
    
    # Also save JSON for archival
    json_data = {
        'date': today,
        'news': news,
        'github_projects': github
    }
    json_file = f'daily_{today}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f'JSON saved to {json_file}')
    
    # Save report content to env file for the workflow to use
    with open('report_content.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    elapsed = time.time() - start
    print(f'
=== Done! {elapsed:.1f}s ===')
    print(f'News: {len(news)}, GitHub: {len(github)}')

if __name__ == '__main__':
    main()

import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import os
import pandas as pd
from requests_oauthlib import OAuth1

st.set_page_config(page_title="Auto Syndicator", page_icon="🚀", layout="centered")

# ==========================================
# 🧠 SMART KEYWORD GENERATION
# ==========================================
NICHE_KEYWORD_MAP = {
    "selenium": "Selenium Test Automation",
    "cypress": "Cypress E2E Testing",
    "api": "API Testing and Validation",
    "rest": "REST API Test Automation",
    "mobile": "Mobile App QA Testing",
    "appium": "Appium Mobile Automation",
    "performance": "Software Performance Testing",
    "load": "Load Testing Strategies",
    "security": "Application Security Testing",
    "agile": "Agile QA Methodologies",
    "manual": "Manual Software Testing",
    "playwright": "Playwright Automation Framework",
    "bdd": "Behavior-Driven Development (BDD)",
    "tdd": "Test-Driven Development (TDD)",
    "ci/cd": "CI/CD Pipeline Testing",
    "jenkins": "Automated Testing in Jenkins"
}

def analyze_and_extract_keyword(title, url):
    combined_text = f"{title} {url}".lower()
    for key, seo_keyword in NICHE_KEYWORD_MAP.items():
        if key in combined_text:
            return seo_keyword
    return "Software Testing Best Practices"

# ==========================================
# 🤖 AUTOMATIC SCRAPING & CONTENT GEN
# ==========================================
def fetch_article_data(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else "Software Testing Guide"
        title = title.split('|')[0].strip()
        
        paragraphs = soup.find_all('p')
        summary_text = ""
        count = 0
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 60:  
                summary_text += text + "\n\n"
                count += 1
            if count >= 3:
                break
                
        if not summary_text:
            summary_text = "Software testing is a crucial part of the development lifecycle."
        return title, summary_text
    except Exception as e:
        return None, str(e)

def generate_markdown_payload(summary, url, anchor_text):
    return f"{summary}\n\n---\n\n🚀 **Want to dive deeper into this topic?** \n\nRead the full, comprehensive guide on **[{anchor_text}]({url})** over at the main blog."

def generate_html_payload(summary, url, anchor_text):
    html = f"<p>{summary.replace(chr(10), '<br>')}</p><hr>"
    html += "<p>🚀 <strong>Want to dive deeper into this topic?</strong></p>"
    html += f'<p>Read the full, comprehensive guide on <a href="{url}"><strong>{anchor_text}</strong></a> over at the main blog.</p>'
    return html

# ==========================================
# 🚀 PUBLISHING FUNCTIONS 
# ==========================================
def publish_to_devto(api_key, title, body_markdown, original_url):
    if not api_key: return {"Platform": "Dev.to (DA 84)", "Status": "⚠️ Skipped", "Details": "No API Key"}
    url = "https://dev.to/api/articles"
    headers = {"Content-Type": "application/json", "api-key": api_key}
    data = {"article": {"title": title, "published": True, "body_markdown": body_markdown, "canonical_url": original_url, "tags": ["softwaretesting", "qa", "automation"]}}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201: return {"Platform": "Dev.to (DA 84)", "Status": "✅ Success", "Details": response.json()['url']}
        return {"Platform": "Dev.to (DA 84)", "Status": "❌ Failed", "Details": f"HTTP {response.status_code}"}
    except Exception as e: return {"Platform": "Dev.to (DA 84)", "Status": "❌ Failed", "Details": str(e)}

def publish_to_medium(token, title, body_markdown, original_url):
    if not token: return {"Platform": "Medium (DA 95)", "Status": "⚠️ Skipped", "Details": "No API Token"}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    try:
        user_resp = requests.get("https://api.medium.com/v1/me", headers=headers)
        if user_resp.status_code != 200: return {"Platform": "Medium (DA 95)", "Status": "❌ Failed", "Details": "Invalid Token"}
        user_id = user_resp.json()['data']['id']
        post_url = f"https://api.medium.com/v1/users/{user_id}/posts"
        data = {"title": title, "contentFormat": "markdown", "content": f"# {title}\n\n{body_markdown}", "canonicalUrl": original_url, "publishStatus": "public", "tags": ["Software Testing"]}
        publish_resp = requests.post(post_url, headers=headers, json=data)
        if publish_resp.status_code == 201: return {"Platform": "Medium (DA 95)", "Status": "✅ Success", "Details": publish_resp.json()['data']['url']}
        return {"Platform": "Medium (DA 95)", "Status": "❌ Failed", "Details": f"HTTP {publish_resp.status_code}"}
    except Exception as e: return {"Platform": "Medium (DA 95)", "Status": "❌ Failed", "Details": str(e)}

def publish_to_hashnode(pat, pub_id, title, body_markdown, original_url):
    if not pat or not pub_id: return {"Platform": "Hashnode (DA 74)", "Status": "⚠️ Skipped", "Details": "Missing Credentials"}
    url = "https://gql.hashnode.com/"
    query = """mutation PublishPost($input: PublishPostInput!) { publishPost(input: $input) { post { url } } }"""
    variables = {"input": {"title": title, "contentMarkdown": body_markdown, "publicationId": pub_id, "originalArticleURL": original_url}}
    headers = {"Authorization": pat, "Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        if response.status_code == 200 and 'errors' not in response.json():
            return {"Platform": "Hashnode (DA 74)", "Status": "✅ Success", "Details": response.json()['data']['publishPost']['post']['url']}
        return {"Platform": "Hashnode (DA 74)", "Status": "❌ Failed", "Details": "GraphQL Error"}
    except Exception as e: return {"Platform": "Hashnode (DA 74)", "Status": "❌ Failed", "Details": str(e)}

def publish_to_wordpress(domain, token, title, body_html):
    if not domain or not token: return {"Platform": "WordPress (DA 92)", "Status": "⚠️ Skipped", "Details": "Missing Credentials"}
    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{domain}/posts/new"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"title": title, "content": body_html, "status": "publish", "tags": "Software Testing"}
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200: return {"Platform": "WordPress (DA 92)", "Status": "✅ Success", "Details": response.json()['URL']}
        return {"Platform": "WordPress (DA 92)", "Status": "❌ Failed", "Details": f"HTTP {response.status_code}"}
    except Exception as e: return {"Platform": "WordPress (DA 92)", "Status": "❌ Failed", "Details": str(e)}

def publish_to_tumblr(blog_name, c_key, c_secret, o_token, o_secret, title, body_html):
    if not all([blog_name, c_key, c_secret, o_token, o_secret]): 
        return {"Platform": "Tumblr (DA 86)", "Status": "⚠️ Skipped", "Details": "Missing Credentials"}
    url = f"https://api.tumblr.com/v2/blog/{blog_name}/post"
    auth = OAuth1(c_key, c_secret, o_token, o_secret)
    data = {"type": "text", "title": title, "body": body_html, "tags": "softwaretesting"}
    try:
        response = requests.post(url, auth=auth, data=data)
        if response.status_code == 201: return {"Platform": "Tumblr (DA 86)", "Status": "✅ Success", "Details": f"https://{blog_name}.tumblr.com/post/{response.json()['response']['id']}"}
        return {"Platform": "Tumblr (DA 86)", "Status": "❌ Failed", "Details": f"HTTP {response.status_code}"}
    except Exception as e: return {"Platform": "Tumblr (DA 86)", "Status": "❌ Failed", "Details": str(e)}

# ==========================================
# 🎨 WEB UI
# ==========================================
def main():
    st.title("🚀 Auto Syndicator")
    st.markdown("Automate High-DA Backlinks for your Software Testing Blog. Works perfectly on mobile!")

    # Sidebar for API Keys
    with st.sidebar:
        st.header("🔑 API Credentials")
        st.info("Set these permanently in Streamlit Cloud Secrets, or paste them here.")
        
        with st.expander("Medium", expanded=False):
            medium_token = st.text_input("Medium Integration Token", type="password", value=st.secrets.get("MEDIUM_TOKEN", ""), key="med_tok")
        
        with st.expander("Dev.to", expanded=False):
            devto_key = st.text_input("Dev.to API Key", type="password", value=st.secrets.get("DEVTO_KEY", ""), key="dev_key")
            
        with st.expander("Hashnode", expanded=False):
            hashnode_pat = st.text_input("Personal Access Token", type="password", value=st.secrets.get("HASHNODE_PAT", ""), key="hash_pat")
            hashnode_pub_id = st.text_input("Publication ID", value=st.secrets.get("HASHNODE_PUB_ID", ""), key="hash_pub")
            
        with st.expander("WordPress", expanded=False):
            wp_domain = st.text_input("Site Domain", value=st.secrets.get("WP_DOMAIN", ""), key="wp_dom")
            wp_token = st.text_input("WP OAuth Token", type="password", value=st.secrets.get("WP_TOKEN", ""), key="wp_tok")
            
        with st.expander("Tumblr", expanded=False):
            tumblr_blog = st.text_input("Blog Name", value=st.secrets.get("TUMBLR_BLOG", ""), key="tb_blog")
            tumblr_c_key = st.text_input("Consumer Key", type="password", value=st.secrets.get("TUMBLR_C_KEY", ""), key="tb_ckey")
            tumblr_c_secret = st.text_input("Consumer Secret", type="password", value=st.secrets.get("TUMBLR_C_SECRET", ""), key="tb_csec")
            tumblr_o_token = st.text_input("Tumblr OAuth Token", type="password", value=st.secrets.get("TUMBLR_O_TOKEN", ""), key="tb_otok")
            tumblr_o_secret = st.text_input("Tumblr OAuth Secret", type="password", value=st.secrets.get("TUMBLR_O_SECRET", ""), key="tb_osec")

    # Main Area
    st.write("### Step 1: Paste Your Blog URL")
    target_url = st.text_input("🔗 Target URL", placeholder="https://yourblog.com/testing-tutorial", key="main_url")
    
    if st.button("Generate Backlinks", type="primary"):
        if not target_url.startswith("http"):
            st.error("Please enter a valid URL starting with http:// or https://")
            return
            
        with st.spinner("Scraping your article..."):
            title, summary = fetch_article_data(target_url)
            
        if not title:
            st.error(f"Failed to fetch article: {summary}")
            return
            
        st.success(f"**Extracted Title:** {title}")
        best_keyword = analyze_and_extract_keyword(title, target_url)
        st.info(f"**Smart Keyword Selected:** {best_keyword}")
        
        body_markdown = generate_markdown_payload(summary, target_url, best_keyword)
        body_html = generate_html_payload(summary, target_url, best_keyword)
        
        st.write("### Step 2: Publishing & Syndicating")
        progress_bar = st.progress(0)
        
        results = []
        
        results.append(publish_to_devto(devto_key, title, body_markdown, target_url))
        progress_bar.progress(20)
        
        results.append(publish_to_medium(medium_token, title, body_markdown, target_url))
        progress_bar.progress(40)
        
        results.append(publish_to_hashnode(hashnode_pat, hashnode_pub_id, title, body_markdown, target_url))
        progress_bar.progress(60)
        
        results.append(publish_to_wordpress(wp_domain, wp_token, title, body_html))
        progress_bar.progress(80)
        
        results.append(publish_to_tumblr(tumblr_blog, tumblr_c_key, tumblr_c_secret, tumblr_o_token, tumblr_o_secret, title, body_html))
        progress_bar.progress(100)
        
        st.write("### 📊 Status Dashboard")
        df = pd.DataFrame(results)
        
        def make_clickable(val):
            if str(val).startswith('http'):
                return f'<a target="_blank" href="{val}">View Post</a>'
            return val
            
        html_table = df.to_html(escape=False, formatters={'Details': make_clickable}, index=False)
        st.markdown(html_table, unsafe_allow_html=True)
        
        st.balloons()

if __name__ == "__main__":
    main()